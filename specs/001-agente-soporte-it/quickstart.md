# Setup & Quickstart (Local MVP)

## 1. Prerequisitos
- Python 3.10
- Archivos `.html` ubicados en `data/mock_sharepoint/`
- Servidor LM Studio levantado en el puerto `1234` usando un environment de modelo compatible de chat.

## 2. Instalación de entorno
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Variables de Entorno (.env)
```env
LLM_ENV=local
RETRIEVER_ENV=local
GROQ_API_KEY=opcional_para_testing_remoto
```

## 4. Construcción Batch de Índice In-Memory
Dado que todo arranca local primero:
```powershell
python etl/run_all.py
```
*Este comando generará el dump de SQLite (`jira_mock.db`), cargará los `.html` e indexará los chunks vectorizados por primera vez en la sesión.*

## 5. Lanzamiento del Backend
```powershell
uvicorn api.main:app --reload
```
Acceder a la terminal de Swagger generada auto por FastAPI: `http://localhost:8000/docs`.

*(Opcional Fase 4)*: `streamlit run ui/app.py`
