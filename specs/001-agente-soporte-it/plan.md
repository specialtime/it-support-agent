# Implementation Plan: Agente de Soporte IT

**Branch**: `001-agente-soporte-it` | **Date**: 2026-04-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-agente-soporte-it/spec.md`

## Summary

Desarrollar un Agente de Soporte IT inteligente manejado por LangGraph que soporta búsqueda multi-fuente en paralelo (fan-out) integrando manuales de SharePoint (HTML), tickets On-Prem (SQLite) y tickets Cloud (JSON), aplicando roles de acceso para ejecutar acciones restrictivas como reseteos de password. Implementado en un backend FastAPI, transicionando desde un MVP local hasta producción en Azure Services.

## Technical Context

**Language/Version**: Python 3.10
**Primary Dependencies**: LangGraph 0.3+, LangChain 0.3+, FastAPI 0.115+, Pydantic v2, pytest
**Storage**: Búsqueda Vectorial abstracta (LangChain InMemoryVectorStore localmente y Azure AI Search productivamente); SQLite y JSON para datos mock.
**Testing**: `pytest` + `FastAPI TestClient`
**Target Platform**: Local setup transicionando a un Serverless Environment en Azure Functions (Consumption Plan) con Azure App Registration para el Bot Teams.
**Project Type**: Servicio web AI / Agent API + Frontend opcional (Teams / Streamlit / Gradio)
**Performance Goals**: Latencia menor a 8 segundos para búsquedas semánticas multi-fuente consolidadas.
**Constraints**: Todos los datos que expone SharePoint deben ser ingeridos mediante parser HTML, nunca mediante MDs para la versión productiva. Control estricto de accesibilidad a las Actions según el Rol. Todo el RAG Vector Storage debe mantenerse polimórfico ante la variable `RETRIEVER_ENV` (cero acoplamiento de infraestructura). Limitación a plan gratuito y 50MB Index size en Azure.
**Scale/Scope**: Limitado al procesamiento en lotes de ~150 chunks para índices locales (~15-20 documentos mockeados). 

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Metodología Incremental**: Las fases están separadas explícitamente en el plan y probables en orden aislado. (PASSED)
- [x] **II. Arquitectura de Fuentes y III. Fan-Out Paralelo**: Uso de retriever agnóstico para conectar paralelo. (PASSED)
- [x] **IV. Trazabilidad**: LangSmith estará atado a la raíz de LangGraph logeando toda decisión. (PASSED)
- [x] **V. Control de Permisos Estricto**: Definido por Pydantic validation en API y State checks. (PASSED)

## Project Structure

### Documentation (this feature)

```text
specs/001-agente-soporte-it/
├── plan.md              # This file
├── research.md          # Technical analysis, why choices were made
├── data-model.md        # State structure, Vector chunk definition
├── quickstart.md        # How to execute locally
├── contracts/           
│   └── api.md           # API specification mappings
└── tasks.md             # (Created later)
```

### Source Code (repository root)

```text
agente-soporte-it/
├── agent/
│   ├── graph.py                    # LangGraph orchestration
│   ├── nodes.py                    # Multi-source parallel and functional nodes
│   ├── tools.py                    # Executable tools mapping
│   ├── retriever.py                # Abstract retrieval strategy
│   └── llm.py                      # LLM Environment factory
├── api/
│   ├── main.py                     # FastAPI routes
│   ├── models.py                   # Pydantic payloads
│   └── bot_handler.py              # Teams adapter
├── services/
│   └── mock_jira_cloud_api/        # Secondary local backend
├── ui/
│   └── app.py                      # UI Streamlit fallback
├── data/
│   ├── mock_sharepoint/*.html      # Updated Mock files (HTML requirement)
│   ├── jira_mock.db                # SQLite
│   └── jira_cloud_mock.json        # Static dump
├── etl/
│   └── pipeline_*.py               # Ingestion engines varying per source type
└── tests/
    └── test_*.py                   # Pytest suites
```

**Structure Decision**: El proyecto es puramente monolítico en el sentido de un Agente con múltiples puntos de entrada (API y Chat), separado por responsabilidades entre the core `agent/`, la capa HTTP `api/` y el `etl/` batch system. La UI cae bajo `ui/` en un fallback module, pero está mayormente diseñada para integrarse externamente.
