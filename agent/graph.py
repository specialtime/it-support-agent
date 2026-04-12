from langgraph.graph import StateGraph, END, START
from api.models import AgentState
from .nodes import (
    classify_intent,
    rewrite_query,
    rag_sharepoint,
    rag_onprem,
    search_cloud,
    execute_jira_tools,
    merge_and_rank,
    generate_answer,
    check_permissions,
    execute_tool,
    generate_permission_denied,
)

builder = StateGraph(AgentState)

def fan_out_node(state: AgentState):
    return {}

builder.add_node("classify_intent", classify_intent)
builder.add_node("rewrite_query", rewrite_query)
builder.add_node("fan_out_query", fan_out_node)
builder.add_node("rag_sharepoint", rag_sharepoint)
builder.add_node("rag_onprem", rag_onprem)
builder.add_node("search_cloud", search_cloud)
builder.add_node("execute_jira_tools", execute_jira_tools)
builder.add_node("merge_and_rank", merge_and_rank)
builder.add_node("generate_answer", generate_answer)
builder.add_node("check_permissions", check_permissions)
builder.add_node("execute_tool", execute_tool)
builder.add_node("generate_permission_denied", generate_permission_denied)

builder.add_edge(START, "classify_intent")

def route_intent(state: AgentState):
    intent = state.get("intent")
    if intent == "jira_search":
        return "jira_search"
    if intent == "action":
        return "action"
    if intent == "greeting":
        return "greeting"
    return "query"

builder.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "query": "rewrite_query",
        "jira_search": "execute_jira_tools",
        "action": "check_permissions",
        "greeting": "generate_answer"
    }
)


builder.add_edge("rewrite_query", "fan_out_query")

builder.add_edge("fan_out_query", "rag_sharepoint")
builder.add_edge("fan_out_query", "rag_onprem")
builder.add_edge("fan_out_query", "search_cloud")

# Fan-in
builder.add_edge(["rag_sharepoint", "rag_onprem", "search_cloud"], "merge_and_rank")
builder.add_edge("execute_jira_tools", "merge_and_rank")

builder.add_edge("merge_and_rank", "generate_answer")
builder.add_edge("generate_answer", END)

# Permission gate: check_permissions → execute_tool (allowed) or denied (blocked)
def route_permission(state: AgentState):
    if state.get("permission_granted"):
        return "allowed"
    return "denied"

builder.add_conditional_edges(
    "check_permissions",
    route_permission,
    {
        "allowed": "execute_tool",
        "denied": "generate_permission_denied",
    }
)

builder.add_edge("execute_tool", END)
builder.add_edge("generate_permission_denied", END)

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
