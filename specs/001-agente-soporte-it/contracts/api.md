# System Interfaces and API Contracts

## 1. Endpoint Principal de Consulta (RAG y Tools)
**Ruta:** `POST /ask`
**Descripción:** Orquestador principal hacia el workflow de LangGraph. 

### Request Validation Contract (Pydantic)
```json
{
  "question": "Estoy atascado con un error 403 en ERP",
  "role": "user"    // Requerido, define permisos del estado. Ejs: user, helpdesk, admin
}
```

### Typical Response (Application/JSON)
```json
{
  "answer": "Hemos revisado los repositorios activos y base de conocimientos. El error 403 suele deberse a... (fuente: [IT-1042] y [runbook_erp_passwords.html])",
  "confidence": 0.88,
  "sources_cited": [
    "IT-1042 (On-Prem, Resuelto)",
    "runbook_erp_passwords.html (SharePoint)"
  ],
  "action_executed": null,
  "status": "success"
}
```

## 2. API Mock Interna de Jira Cloud 
Restringida a tráfico interno o Testing local

**Obtener por ID:** `GET /jira/issue/{id}`
**Listado Activos (Filtro estructurado sin RAG):** `GET /jira/issues/open`

## 3. Tool: Reset Password Contract 
```json
// Executed natively by Langchain Tools bindings internally
{
   "function_name": "reset_password",
   "arguments": {
      "username": "jperez",
      "system": "ERP"
   }
}
```

## 4. Microsoft Teams Webhook Contract (Fase 4)
**Ruta:** `POST /api/messages`
**Descripción:** Endpoint de compatibilidad nativa Bot Framework. Se intercepta aquí la solicitud base XML/JSON de Azure Bot Service, extrae la pregunta, la manda al endpoint `/ask` y retorna la Activity adaptada con la respuesta text.
