# IT Support Agent (AI-Powered)

Este es un agente de soporte IT inteligente construido con **LangGraph**, **FastAPI** y una interfaz moderna en **Vanilla JS**. Utiliza una arquitectura de RAG (Retrieval-Augmented Generation) multi-fuente en paralelo para responder consultas técnicas y ejecutar acciones administrativas.

## 🚀 Características Principales

- **Búsqueda Multi-Fuente en Paralelo**: Consulta simultáneamente SharePoint (knowledge base), Base de Datos SQL de Tickets y conexión a la API de Jira Cloud.
- **Clasificación Inteligente de Intenciones**: Identifica si el usuario necesita ayuda, buscar un ticket específico o realizar una acción.
- **Acciones Administrativas Seguras**: Soporta reset de contraseñas y procesamiento de archivos, protegidos por control de acceso basado en roles (RBAC).
- **Interfaz de Chat Moderna**: Construida con Vanilla HTML, CSS y JS con un diseño premium y glassmorphism.
- **Trazabilidad con LangSmith**: Monitoreo completo de cada paso de la lógica del agente.

## 🛠️ Stack Tecnológico

- **Orquestación**: LangGraph 0.3+
- **Framework de IA**: LangChain 0.2+
- **Backend API**: FastAPI
- **Frontend**: Vanilla HTML/JS (servido en puerto 8080)
- **Modelos**: Compatible con OpenAI, Groq y modelos locales (via LM Studio)
- **Base de Datos**: SQLite

## 📋 Requisitos Previos

1. **Python 3.10+**
2. **LM Studio** (requerido para embeddings locales):
   - Servidor levantado en `http://localhost:1234/v1` con el modelo `nomic-embed-text-v1.5` cargado.
3. **Claves de API** (Groq o OpenAI si no usas local).

## 💻 Instalación y Uso

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repo>
   cd it-support-agent
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar el entorno**:
   - Copia `.env.example` a `.env` y completa tus credenciales.

4. **Ingestar datos en la BD Vectorial**:
   Garantiza que el servidor de LM Studio está en ejecución y lanza:
   ```bash
   python -m etl.ingest
   ```

5. **Ejecutar la aplicación**:
   Puedes usar el script automatizado (Windows):
   ```powershell
   .\run_app.ps1
   ```
   O manualmente en dos terminales:
   - **Backend**: `uvicorn api.main:app --host 0.0.0.0 --port 8000`
   - **Frontend**: `python -m http.server 8080 --directory frontend`

## 🧪 Testing

Para ejecutar la suite de pruebas:
```bash
pytest
```

## 🔒 Privacidad y Datos

Este repositorio ha sido configurado para excluir archivos de datos sensibles (`data/`), prompts de sistema personalizados (`agent/prompts/`) y planes maestros internos. Utiliza datos de prueba (mocks) para demostraciones seguras.
