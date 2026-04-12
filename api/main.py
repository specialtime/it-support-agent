from fastapi import FastAPI
from .models import AskRequest, AskResponse
from langchain_core.messages import HumanMessage
from agent.graph import graph
from .bot_handler import router as bot_router

app = FastAPI(title="Agente de Soporte IT API", version="1.0.0")

app.include_router(bot_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    # Pasar solo el mensaje nuevo y campos per-request al grafo.
    # Pasar el estado completo causaba duplicación de mensajes con el checkpointer.
    # Los campos efímeros (acción ejecutada, intent, permisos) se limpian
    # explícitamente cada turno para evitar que el checkpoint los arrastre.
    input_state = {
        "messages": [HumanMessage(content=request.question)],
        "user_role": request.role,
        "session_id": request.session_id,
        # Efímeros por turno — deben resetearse aunque el nodo no los toque
        "action_taken": None,
        "intent": "",
        "permission_granted": False,
        "action_target_user": None,
        "search_query": "",
    }

    config = {
        "configurable": {"thread_id": request.session_id},
        "metadata": {
            "session_id": request.session_id,
            "user_role": request.role,
            "application": "IT-Support-Agent"
        },
        "tags": ["api_request", f"role_{request.role}"]
    }
    
    # LangSmith tracing se activa automáticamente con variables de entorno,
    # pero inyectar metadatos y tags permite cruzar logs por sesión y rol.
    result = await graph.ainvoke(input_state, config=config)

    return AskResponse(
        answer=result.get("answer", ""),
        confidence=result.get("confidence", 0.0),
        sources_cited=result.get("sources", []),
        action_executed=result.get("action_taken"),
        status="success"
    )
