# Text splitter methods that might be reused by all ETL pipelines
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80
    )
except ImportError:
    splitter = None

def upload_to_index(documents: list) -> None:
    """
    Sube los documentos inyectados a Azure AI Search o los registra en el InMemoryLocalStore.
    """
    pass
