from langchain_core.tools import tool
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DATA_FILE = os.path.join(BASE_DIR, "data", "jira_cloud_mock.json")

def _get_mock_issues():
    try:
        with open(MOCK_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("issues", [])
    except Exception:
        return []

@tool
def search_jira_cloud(jql: str) -> str:
    """Busca tickets en Jira Cloud usando un JQL (Jira Query Language). Útil para listar tickets abiertos o asignados."""
    issues = _get_mock_issues()
    # Simple mock: return all open issues if 'status' not in JQL for demo
    results = [iss for iss in issues if iss.get("status", "").lower() not in ("closed", "done")]
    
    if not results:
        return "No se encontraron tickets."
        
    formatted = []
    for issue in results:
        formatted.append(f"Ticket: {issue.get('key')} - {issue.get('summary')} (Estado: {issue.get('status')})")
    
    return "\n".join(formatted)

@tool
def get_jira_ticket(ticket_key: str) -> str:
    """Obtiene todo el detalle de un ticket específico de Jira Cloud a partir de su ID (ej. SUPP-123)."""
    issues = _get_mock_issues()
    for iss in issues:
        if iss.get("key") == ticket_key:
            return json.dumps(iss, indent=2, ensure_ascii=False)

    return f"Ticket {ticket_key} no encontrado en Jira."


@tool
def reset_password(username: str) -> str:
    """Resetea la contraseña del usuario especificado en el sistema ERP. Solo disponible para roles helpdesk y admin."""
    # Simulated password reset — in production this would call the ERP API
    new_temp_password = f"Temp@{username[:3].upper()}2026!"
    return (
        f"Contraseña reseteada exitosamente para el usuario '{username}'. "
        f"Contraseña temporal asignada: {new_temp_password}. "
        "El usuario deberá cambiarla en el próximo inicio de sesión."
    )

@tool
def process_excel(file_path: str) -> str:
    """Procesa un archivo Excel especificado desde el almacenamiento local o remoto."""
    # Simulated excel processing
    return f"Procesamiento del archivo '{file_path}' iniciado y completado exitosamente con 100 filas importadas."
