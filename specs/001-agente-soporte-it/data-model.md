# Data Model and Agent State Schema

## AgentState (LangGraph)
El `AgentState` define la representación inmutable temporal de los iteraciones del Grafo.
```python
class AgentState(TypedDict):
    messages:           list[BaseMessage]
    session_id:         str
    user_role:          str              # Valores: 'user', 'helpdesk', 'admin'
    intent:             str              # Clasificado por LLM: 'query' | 'jira_search' | 'action'
    sharepoint_docs:    list[dict]
    onprem_docs:        list[dict]
    cloud_docs:         list[dict]
    context:            list[dict]       # Resultados del merge_and_rank
    action_taken:       Optional[str]    # Tool ejecutada si aplica (e.g. "reset_password(jsmith)")
    answer:             str              # Respuesta consolidada AI
    sources:            list[str]
    confidence:         float
    has_expert_context: bool
    permission_granted: bool             # Seteado por check_permissions antes de execute_tool
```

## Knowledge Chunk Schema (AI Search & Local Target)
Estructura unificada donde se volcarán tanto la información sacada de SQL, JSON y HTML.
```json
{
    "id": "md5(hash_unique)",
    "content": "text string...",
    "content_vector": [0.1, 0.44, ...], 
    "source_type": "sharepoint | jira_onprem | jira_cloud",
    "source_id": "IT-1042 or index.html",
    "title": "String title",
    "status": "String (Resolved, Closed) or NULL",
    "priority": "String or NULL",
    "system": "ERP | VPN | AD | Correo | Red",
    "category": "Topic classification",
    "has_analyst_comment": "Boolean",
    "created_date": "ISO8601 Date String",
    "chunk_index": "Integer"
}
```

## Mock Jira On-Prem (SQLite Table Spec)
```sql
CREATE TABLE issues (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    resolution TEXT,
    status TEXT,
    priority TEXT,
    reporter TEXT,
    assignee TEXT,
    system TEXT,
    category TEXT,
    created_date TEXT,
    resolved_date TEXT,
    tags TEXT
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id TEXT REFERENCES issues(id),
    author TEXT,
    body TEXT,
    created_date TEXT,
    is_analyst INTEGER DEFAULT 0
);
```
