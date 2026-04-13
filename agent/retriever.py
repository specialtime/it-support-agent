import os
from typing import List, Dict, Any
import warnings

def _search_local(query: str, source_type: str, top: int = 4) -> List[Dict[str, Any]]:
    """Búsqueda semántica usando ChromaDB local."""
    from etl.embedding import get_chroma_client, get_embedding_fn
    
    collection_mapping = {
        "sharepoint": "sharepoint",
        "jira_onprem": "jira_onprem",
        "jira_cloud": "jira_cloud"
    }
    
    col_name = collection_mapping.get(source_type)
    if not col_name:
        warnings.warn(f"Colección desconocida para source_type: {source_type}")
        return []
        
    client = get_chroma_client()
    try:
        ef = get_embedding_fn()
        collection = client.get_collection(name=col_name, embedding_function=ef)
    except Exception as e:
        warnings.warn(f"No se pudo acceder a la colección {col_name}: {e}")
        return []
        
    results = collection.query(
        query_texts=[query],
        n_results=top
    )
    
    mapped_results = []
    if not results or not results.get("ids") or not results["ids"][0]:
        return []
        
    for i in range(len(results["ids"][0])):
        metadatas = results["metadatas"][0][i]
        mapped_results.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "source": metadatas.get("source", ""),
            "source_type": metadatas.get("source_type", source_type),
            "title": metadatas.get("title", ""),
            "url": metadatas.get("url", "")
        })
        
    return mapped_results

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
