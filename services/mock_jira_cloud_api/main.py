import json
import os
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any

app = FastAPI(title="Mock Jira Cloud API")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOCK_DATA_FILE = os.path.join(BASE_DIR, "data", "jira_cloud_mock.json")
_mock_issues = None

def get_issues() -> List[Dict[str, Any]]:
    global _mock_issues
    if _mock_issues is None:
        try:
            with open(MOCK_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _mock_issues = data.get("issues", [])
        except Exception as e:
            print(f"Error loading mock JSON: {e}")
            _mock_issues = []
    return _mock_issues

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/jira/issues/open")
@app.get("/rest/api/3/search")
def get_open_issues(jql: str = ""):
    """Listado Activos (Filtro estructurado sin RAG)"""
    issues = get_issues()
    if "key =" in jql:
         # simple mock for specific key search in JQL
         import re
         match = re.search(r'key\s*=\s*([^\s]+)', jql)
         if match:
             key = match.group(1).strip("'").strip('"')
             return {"issues": [iss for iss in issues if iss.get("key") == key]}

    open_issues = [iss for iss in issues if iss.get("status", "").lower() not in ("closed", "resolved", "done")]
    return {"issues": open_issues}

@app.get("/jira/issue/{issue_id}")
@app.get("/rest/api/3/issue/{issue_id}")
def get_issue(issue_id: str):
    """Obtener por ID"""
    issues = get_issues()
    for iss in issues:
        if iss.get("key") == issue_id or str(iss.get("id")) == issue_id:
            return iss
    raise HTTPException(status_code=404, detail="Issue not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
