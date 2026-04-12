from bs4 import BeautifulSoup
from typing import List, Dict, Any
import os
import glob
from etl.shared import splitter

def extract_html_text(html_content: str) -> str:
    """Extrae el texto de un documento HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=' ', strip=True)

def load_sharepoint_documents(mock_dir: str) -> List[Dict[str, Any]]:
    """Carga los documentos HTML de un directorio simulando SharePoint y los divide."""
    documents = []
    html_files = glob.glob(os.path.join(mock_dir, "*.html"))
    for file_path in html_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            text = extract_html_text(content)
            title = os.path.basename(file_path).replace(".html", "")
            
            if splitter:
                chunks = splitter.split_text(text)
                for i, chunk in enumerate(chunks):
                    documents.append({
                        "id": f"sp_{title}_{i}",
                        "source_id": title,
                        "source": "sharepoint",
                        "title": title,
                        "content": chunk,
                        "url": f"https://mock-sharepoint.local/{os.path.basename(file_path)}"
                    })
            else:
                documents.append({
                    "id": f"sp_{title}_0",
                    "source_id": title,
                    "source": "sharepoint",
                    "title": title,
                    "content": text,
                    "url": f"https://mock-sharepoint.local/{os.path.basename(file_path)}"
                })
    return documents
