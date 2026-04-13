import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

load_dotenv()

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_embedding_fn() -> OpenAIEmbeddingFunction:
    """
    Devuelve la función de embeddings apuntando a LM Studio 
    usando la API compatible con OpenAI.
    """
    lms_base_url = os.environ.get("LMS_BASE_URL", "http://localhost:1234/v1")
    lms_embed_model = os.environ.get("LMS_EMBED_MODEL", "nomic-embed-text-v1.5")
    
    return OpenAIEmbeddingFunction(
        api_key="lm-studio",  # LM Studio no valida este token, pero es requerido por el SDK
        api_base=lms_base_url,
        model_name=lms_embed_model
    )

import threading

_client_instance = None
_client_lock = threading.Lock()

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Devuelve el cliente persistente de ChromaDB apuntando a la carpeta local data/chroma_db/.
    Implementa un patrón singleton thread-safe para evitar bloqueos concurrentes "tenant" en FastAPI/LangGraph.
    """
    global _client_instance
    if _client_instance is None:
        with _client_lock:
            if _client_instance is None:
                chroma_db_path = os.path.join(BASE_DIR, "data", "chroma_db")
                _client_instance = chromadb.PersistentClient(path=chroma_db_path)
    return _client_instance
