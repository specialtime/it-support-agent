from typing import List, Dict, Any, Literal, Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel, Field
from api.models import AgentState
from .retriever import search
from .llm import get_llm

import re
import os

def _load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ---------------------------------------------------------------------------
# Structured output schema for LLM-based intent classification
# ---------------------------------------------------------------------------

class IntentClassification(BaseModel):
    intent: Literal["query", "jira_search", "action", "greeting"]
    reasoning: str  # trazable en LangSmith; no se expone al usuario

    target_user: Optional[str] = Field(
        default=None,
        description="Username del afectado cuando intent=action y se menciona un usuario. Ej: 'jsmith', 'juan.garcia'. None si no aplica."
    )

_CLASSIFY_SYSTEM = _load_prompt("classify.md")



def classify_intent(state: AgentState) -> dict:
    llm = get_llm()
    structured_llm = llm.with_structured_output(IntentClassification)

    # Pasamos el historial completo para que el LLM resuelva referencias implícitas
    # ("ese ticket", "el mismo caso") usando el contexto de turnos anteriores.
    messages = [
        SystemMessage(content=_CLASSIFY_SYSTEM),
        *state["messages"],
    ]

    try:
        result: IntentClassification = structured_llm.invoke(messages)
        return {"intent": result.intent, "action_target_user": result.target_user}
    except Exception:
        # Fallback al router determinista si el LLM no está disponible
        return _classify_intent_fallback(state)

_REWRITE_QUERY_SYSTEM = _load_prompt("rewrite.md")



def rewrite_query(state: AgentState) -> dict:
    """Expande referencias implícitas del último mensaje usando el historial reciente.
    Produce search_query: la consulta contextualizada que usarán los nodos RAG."""
    llm = get_llm()

    REWRITE_WINDOW = 4
    recent = state["messages"][-REWRITE_WINDOW:]

    messages = [
        SystemMessage(content=_REWRITE_QUERY_SYSTEM),
        *recent,
    ]

    try:
        response = llm.invoke(messages)
        search_query = response.content.strip()
    except Exception:
        search_query = state["messages"][-1].content

    return {"search_query": search_query}


def _classify_intent_fallback(state: AgentState) -> dict:
    """Router determinista usado como fallback cuando el LLM no está disponible."""
    query = state["messages"][-1].content.lower()
    
    greeting_words = ["hola", "buenos dias", "buenos días", "buenas tardes", "buenas", "gracias", "saludos"]
    if any(query.strip().startswith(w) or query.strip() == w for w in greeting_words) and len(query.split()) < 4:
        return {"intent": "greeting"}

    action_triggers = ["resetea", "resetear", "reset", "restablecer", "cambiar contraseña", "cambiar password", "procesar", "excel", "archivo"]
    if any(t in query for t in action_triggers):
        return {"intent": "action"}
    if "ticket" in query or "jira" in query or re.search(r'[a-zA-Z]+-\d+', query):
        return {"intent": "jira_search"}
    trigger_words = ["comentario", "analista", "estado", "resolución", "prioridad", "ese", "este", "hora", "fecha", "quién", "quien", "falla", "error"]
    if any(w in query for w in trigger_words) and len(state["messages"]) >= 3:
        last_ai_msg = state["messages"][-2].content.upper()
        if re.search(r'[A-Z]+-\d+', last_ai_msg):
            return {"intent": "jira_search"}
    return {"intent": "query"}


def execute_jira_tools(state: AgentState) -> dict:
    query = state["messages"][-1].content
    from .tools import get_jira_ticket, search_jira_cloud
    
    match = re.search(r'([a-zA-Z]+-\d+)', query)
    ticket_id = None
    
    if match:
        ticket_id = match.group(1).upper()
    else:
        # Search backwards in history for a ticket ID
        for msg in reversed(state["messages"][:-1]):
            m = re.search(r'([a-zA-Z]+-\d+)', msg.content)
            if m:
                ticket_id = m.group(1).upper()
                break
                
    if ticket_id:
        tool_res = get_jira_ticket.invoke({"ticket_key": ticket_id})
    else:
        tool_res = search_jira_cloud.invoke({"jql": ""})
        
    doc = {
        "content": f"RESULTADO DE JIRA (Vía API Tool):\n{tool_res}",
        "source_id": "Jira_API",
        "origin": "cloud",
        "score": 100.0,
        "has_analyst_comment": True
    }
    
    return {"cloud_docs": [doc]}

def rag_sharepoint(state: AgentState) -> dict:
    query = state.get("search_query") or state["messages"][-1].content
    docs = search(query, "sharepoint", top=3)
    return {"sharepoint_docs": [d | {"origin": "sharepoint"} for d in docs]}

def rag_onprem(state: AgentState) -> dict:
    query = state.get("search_query") or state["messages"][-1].content
    docs = search(query, "jira_onprem", top=4)
    return {"onprem_docs": [d | {"origin": "onprem"} for d in docs]}

def search_cloud(state: AgentState) -> dict:
    query = state.get("search_query") or state["messages"][-1].content
    docs = search(query, "jira_cloud", top=3)
    return {"cloud_docs": [d | {"origin": "cloud"} for d in docs]}

def merge_and_rank(state: AgentState) -> dict:
    all_docs = (
        state.get("onprem_docs", []) +
        state.get("sharepoint_docs", []) +
        state.get("cloud_docs", [])
    )
    
    seen = set()
    deduped = []
    
    for doc in all_docs:
        source_id = doc.get("source_id") or doc.get("id")
        if source_id not in seen:
            seen.add(source_id)
            if "score" not in doc:
                doc["score"] = 1.0  # mock score fallback
            deduped.append(doc)

    def weighted_score(doc):
        s = doc.get("score", 1.0)
        origin = doc.get("origin")
        if origin == "onprem" and doc.get("has_analyst_comment"):
            return s * 1.4
        if origin == "sharepoint":
            return s * 1.2
        if origin == "cloud":
            return s * 1.1
        return s

    ranked = sorted(deduped, key=weighted_score, reverse=True)[:7]
    has_expert = any(d.get("has_analyst_comment") for d in ranked)
    sources = [f"{d.get('source_id')} [{d.get('origin')}]" for d in ranked]
    return {
        "context": ranked,
        "has_expert_context": has_expert,
        "sources": sources
    }

AUTHORIZED_ROLES = {"helpdesk", "admin"}


def check_permissions(state: AgentState) -> dict:
    """Validates whether the current user_role is allowed to execute privileged tools."""
    role = state.get("user_role", "user")
    granted = role in AUTHORIZED_ROLES
    return {"permission_granted": granted}


def execute_tool(state: AgentState) -> dict:
    """Executes the requested privileged action tool (e.g. reset_password, process_excel)."""
    from .tools import reset_password, process_excel

    query = state["messages"][-1].content
    query_lower = query.lower()

    if "excel" in query_lower or "archivo" in query_lower or "procesar" in query_lower:
        match = re.search(r'(?:archivo|excel)\s+([^\s]+)', query, re.IGNORECASE)
        file_path = match.group(1) if match else "datos.xlsx"
        tool_result = process_excel.invoke({"file_path": file_path})
        action_taken = f"process_excel({file_path})"
    else:
        # Username extraído por classify_intent vía LLM; fallback a regex si no vino
        username = state.get("action_target_user")
        if not username:
            match = re.search(r'usuario\s+(\w+)', query, re.IGNORECASE)
            username = match.group(1) if match else "unknown"

        tool_result = reset_password.invoke({"username": username})
        action_taken = f"reset_password({username})"

    from langchain_core.messages import AIMessage
    response = AIMessage(content=tool_result)

    return {
        "messages": [response],
        "answer": tool_result,
        "action_taken": action_taken,
        "confidence": 1.0,
        "sources": [],
    }


def generate_permission_denied(state: AgentState) -> dict:
    """Returns a polite refusal when the user role lacks permission for the requested action."""
    role = state.get("user_role", "user")
    msg = (
        f"Acceso denegado. Tu rol actual ('{role}') no tiene permisos para ejecutar "
        "esta operación. Solo los roles 'helpdesk' y 'admin' pueden realizar acciones "
        "sobre cuentas de usuario. Por favor, contacta a tu administrador de sistemas."
    )

    from langchain_core.messages import AIMessage
    response = AIMessage(content=msg)

    return {
        "messages": [response],
        "answer": msg,
        "confidence": 1.0,
        "sources": [],
    }


def generate_answer(state: AgentState) -> dict:
    llm = get_llm()
    
    context_parts = []
    for d in state.get("context", []):
        sid = d.get("source_id", "N/A")
        origin = d.get("origin", "N/A")
        content = d.get("content", "")
        context_parts.append(f"Fuente: {sid} - Origen: {origin}\n{content}")
        
    context_str = "\n\n".join(context_parts)
    if not context_str:
        context_str = "No hay contexto disponible."
        
    sys_prompt = _load_prompt("answer.md").format(context=context_str)


    # generate_answer NO necesita historial conversacional: el RAG context ya está en el
    # system prompt y las deíxis ("eso", "ese módulo") ya fueron resueltas por rewrite_query.
    # Pasar turnos anteriores contamina la respuesta con contexto irrelevante de otras preguntas.
    current_question = state.get("search_query") or state["messages"][-1].content
    messages = [
        SystemMessage(content=sys_prompt),
        HumanMessage(content=current_question),
    ]
    
    # Check if we should catch HTTP errors to LM studio if it is not running
    try:
        response = llm.invoke(messages)
        ans = response.content
    except Exception as e:
        ans = f"Error conectando al LLM: {str(e)}"
        response = AIMessage(content=ans)

    return {
        "messages": [response],
        "answer": ans,
        "confidence": 0.85
    }
