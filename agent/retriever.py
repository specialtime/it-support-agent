import os
import json
from typing import List, Dict, Any

_doc_cache = {}

def clear_cache():
    """Limpia el caché de documentos para forzar recarga."""
    global _doc_cache
    _doc_cache = {}

def _init_cache():
    if not _doc_cache:
        # Avoid circular imports or issues by lazy loading
        from etl.pipeline_sharepoint import load_sharepoint_documents
        from etl.pipeline_onprem import load_onprem_tickets
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        sp_path = os.path.join(base_dir, "data", "mock_sharepoint")
        sp_docs = load_sharepoint_documents(sp_path) if os.path.exists(sp_path) else []
        
        db_path = os.path.join(base_dir, "data", "jira_mock.db")
        onprem_docs = load_onprem_tickets(db_path) if os.path.exists(db_path) else []
        
        cloud_docs = []
        cloud_path = os.path.join(base_dir, "data", "jira_cloud_mock.json")
        if os.path.exists(cloud_path):
            try:
                with open(cloud_path, "r", encoding="utf-8") as f:
                    cloud_data = json.load(f)
                    for issue in cloud_data.get("issues", []):
                        cloud_docs.append({
                            "id": issue.get("key"),
                            "source_id": issue.get("key"),
                            "source": "jira_cloud",
                            "title": issue.get("summary", ""),
                            "content": json.dumps(issue),
                            "url": f"cloud://{issue.get('key')}"
                        })
            except Exception:
                pass
                
        _doc_cache["sharepoint"] = sp_docs
        _doc_cache["jira_onprem"] = onprem_docs
        _doc_cache["jira_cloud"] = cloud_docs

def _search_local(query: str, source_type: str, top: int = 4) -> List[Dict[str, Any]]:
    _init_cache()
    docs = _doc_cache.get(source_type, []) 
    
    import string
    stop_words = {"para", "como", "cómo", "paso", "las", "los", "qué", "que", "una", "por", "con", "dar", "del", "resumime", "en"}
    
    # Strip punctuation and filter
    query_clean = query.translate(str.maketrans("", "", string.punctuation))
    keywords = [kw.lower() for kw in query_clean.split() if len(kw) > 3 and kw.lower() not in stop_words]
    
    scored = []
    for doc in docs:
        text = str(doc.get("content", "") + " " + doc.get("title", "")).lower()
        score = sum(text.count(kw) for kw in keywords)
        if score > 0:
            scored.append((score, doc))
            
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for s, d in scored][:top]

def _search_azure(query: str, source_type: str, top: int = 4) -> List[Dict[str, Any]]:
    # Placeholder for Azure AI search implementation in Phase 3
    return []

def search(query: str, source_type: str, top: int = 4) -> List[Dict[str, Any]]:
    """
    Abstract retriever routing the vector search depending on the `RETRIEVER_ENV` 
    """
    if os.getenv("RETRIEVER_ENV") == "azure":
        return _search_azure(query, source_type, top)
    else:
        return _search_local(query, source_type, top)
