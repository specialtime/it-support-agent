import json
import os
import warnings
from etl.pipeline_sharepoint import load_sharepoint_documents
from etl.pipeline_onprem import load_onprem_tickets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ingest_sharepoint(client, ef):
    """
    Ingesta documentos mockeados de SharePoint en ChromaDB.
    """
    mock_dir = os.path.join(BASE_DIR, "data", "mock_sharepoint")
    if not os.path.exists(mock_dir):
        warnings.warn(f"Directorio SharePoint no encontrado en: {mock_dir}")
        return
        
    collection = client.get_or_create_collection(
        name="sharepoint",
        embedding_function=ef
    )
    
    docs = load_sharepoint_documents(mock_dir)
    if not docs:
        return
        
    ids = [doc["id"] for doc in docs]
    documents = [doc["content"] for doc in docs]
    metadatas = [
        {
            "source": doc["source"],
            "source_type": doc["source"], # sharepoint
            "title": doc["title"],
            "url": doc["url"],
            "has_analyst_comment": False
        }
        for doc in docs
    ]
    
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

def ingest_jira_onprem(client, ef):
    """
    Ingesta tickets mockeados de Jira On-Prem (SQLite) en ChromaDB.
    """
    db_path = os.path.join(BASE_DIR, "data", "jira_mock.db")
    if not os.path.exists(db_path):
        warnings.warn(f"Base de datos Jira On-Prem no encontrada en: {db_path}")
        return
        
    collection = client.get_or_create_collection(
        name="jira_onprem",
        embedding_function=ef
    )
    
    docs = load_onprem_tickets(db_path)
    if not docs:
        return
        
    ids = [doc["id"] for doc in docs]
    documents = [doc["content"] for doc in docs]
    metadatas = [
        {
            "source": "jira_onprem",
            "source_type": "jira_onprem",
            "title": doc["title"],
            "url": doc["url"],
            # Inferimos si es interno revisando si load_onprem_tickets agregó '[Internal]' al texto
            "has_analyst_comment": "[Internal]" in doc["content"]
        }
        for doc in docs
    ]
    
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

def ingest_jira_cloud(client, ef):
    """
    Ingesta tickets mockeados de Jira Cloud (JSON) en ChromaDB.
    """
    mock_path = os.path.join(BASE_DIR, "data", "jira_cloud_mock.json")
    if not os.path.exists(mock_path):
        warnings.warn(f"Archivo JSON Jira Cloud no encontrado en: {mock_path}")
        return
        
    collection = client.get_or_create_collection(
        name="jira_cloud",
        embedding_function=ef
    )
    
    with open(mock_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    issues = data.get("issues", [])
    if not issues:
        return
        
    ids = []
    documents = []
    metadatas = []
    
    for issue in issues:
        issue_key = issue["key"]
        ids.append(f"cloud_{issue_key}")
        
        # Generar contenido que sea util para la db
        doc_content = f"Title: {issue.get('summary', '')}\n"
        doc_content += f"Status: {issue.get('status', '')}\n"
        doc_content += f"System: {issue.get('system', '')}\n"
        
        comments = issue.get("comments", [])
        if comments:
            doc_content += "Comments:\n"
            for comment in comments:
                doc_content += f"- {comment.get('author', 'Unknown')}: {comment.get('body', '')}\n"
                
        documents.append(doc_content)
        
        metadatas.append({
            "source": "jira_cloud",
            "source_type": "jira_cloud",
            "title": f"[{issue_key}] {issue.get('summary', '')}",
            "url": f"https://soporte-it.atlassian.net/browse/{issue_key}",
            "has_analyst_comment": False
        })
        
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

def get_stats() -> dict:
    """Devuelve el conteo de documentos por colección."""
    from etl.embedding import get_chroma_client
    client = get_chroma_client()
    stats = {}
    for coll_name in ["sharepoint", "jira_onprem", "jira_cloud"]:
        try:
            col = client.get_collection(coll_name)
            stats[coll_name] = col.count()
        except Exception:
            stats[coll_name] = 0
    return stats

if __name__ == "__main__":
    from etl.embedding import get_chroma_client, get_embedding_fn
    
    print("Inicializando entorno de ChromaDB...")
    client = get_chroma_client()
    try:
        ef = get_embedding_fn()
    except Exception as e:
        warnings.warn(f"Error al inicializar embedding function: {e}")
        ef = None

    if ef:
        print("Iniciando ingesta de datos en ChromaDB...")
        try:
            ingest_sharepoint(client, ef)
            print("[sharepoint] ingesta completada")
        except Exception as e:
            warnings.warn(f"Error en sharepoint: {e}")

        try:
            ingest_jira_onprem(client, ef)
            print("[jira_onprem] ingesta completada")
        except Exception as e:
            warnings.warn(f"Error en jira_onprem: {e}")

        try:
            ingest_jira_cloud(client, ef)
            print("[jira_cloud] ingesta completada")
        except Exception as e:
            warnings.warn(f"Error en jira_cloud: {e}")

    stats = get_stats()
    for source, count in stats.items():
        print(f"[{source}]  {count} documentos ingestados")
    print(f"Ingesta completada. Índice en: {os.path.join(BASE_DIR, 'data', 'chroma_db')}")
