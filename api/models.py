from pydantic import BaseModel
from typing import TypedDict, Optional, List, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AskRequest(BaseModel):
    question: str
    role: str = "user"  # Options: "user", "helpdesk", "admin"
    session_id: str = "default"

class AskResponse(BaseModel):
    answer: str
    confidence: float
    sources_cited: List[str]
    action_executed: Optional[str] = None
    status: str = "success"

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    user_role: str
    intent: str
    sharepoint_docs: List[dict]
    onprem_docs: List[dict]
    cloud_docs: List[dict]
    context: List[dict]  # Merged and ranked chunks
    action_taken: Optional[str]
    answer: str
    sources: List[str]
    confidence: float
    has_expert_context: bool
    permission_granted: bool
    action_target_user: Optional[str]  # username extraído por classify_intent cuando intent=action
    search_query: str                  # query reescrita con contexto para los nodos RAG
