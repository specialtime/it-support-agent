# Implementation Plan: Local Vector Database para IT Support Agent

**Branch**: `002-local-vector-db` | **Date**: 2026-04-12 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/002-local-vector-db/spec.md`

## Summary

El motor de búsqueda actual en `agent/retriever.py` usa coincidencia de keywords sin comprensión semántica, lo que produce resultados pobres en consultas con sinónimos, paráfrasis o variaciones de terminología. Esta feature reemplaza `_search_local` por búsqueda semántica usando **ChromaDB** como base de datos vectorial persistida en disco y **nomic-embed-text-v1.5** servido desde **LM Studio** como motor de embeddings (API OpenAI-compatible, sin dependencias extras en el proceso Python). Se agrega un script de ingesta único (`etl/ingest.py`) que reutiliza los pipelines ETL existentes y construye tres colecciones separadas: `sharepoint`, `jira_onprem`, `jira_cloud`. La interfaz pública de `search()` permanece idéntica para no romper los nodos del grafo LangGraph.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: ChromaDB ≥ 0.5, openai ≥ 1.0 (cliente HTTP para LM Studio), langchain ≥ 0.3, langgraph ≥ 0.3, FastAPI 0.115+  
**Storage**: ChromaDB persistido en `data/chroma_db/` (disco local, carpeta excluida de git)  
**Testing**: pytest  
**Target Platform**: Windows local (desarrollo), aligned con MVP env per constitution  
**Project Type**: Componente interno de un agente LangGraph (no expone API externa nueva)  
**Performance Goals**: Ingesta < 60s sobre datos mock; query < 2s por colección  
**Constraints**: LM Studio corriendo en localhost:1234 es prerequisito de runtime; embedding dimension debe ser consistente en todas las colecciones (768d para nomic-embed-text)  
**Scale/Scope**: Cientos de tickets / documentos en fase local; escala a producción fuera del alcance de esta feature

## Constitution Check

*GATE: evaluado pre-diseño y post-diseño.*

| Principio | Estado | Observación |
|---|---|---|
| I. Retriever Abstraction | ✅ | Se mantiene el switch `RETRIEVER_ENV`. La nueva implementación está dentro de `_search_local`, sin que el grafo cambie. |
| II. Parallel Fan-Out | ✅ | Los nodos del grafo siguen llamando a `search()` en fan-out; ChromaDB responde por colección como antes. |
| III. Role-Based Permissions | ✅ | No se toca la capa de permisos. |
| IV. Observability & Tracing | ✅ | Los traces a LangSmith se emiten en los nodos del grafo, no en el retriever. No afectado. |
| V. SharePoint Data Integrity | ✅ | `pipeline_sharepoint.py` no se modifica; sigue leyendo `.html`. |
| Schema Rules | ⚠️ Menor | Los metadatos actuales usan `source` en lugar de `source_type`. Se agrega `source_type` como alias en los metadatos del documento indexado para cumplir el schema. |
| Governance (RETRIEVER_ENV) | ✅ | Cambio documentado aquí. Compatible con MVP env (LM Studio). |

**Violation menor**: el campo `source_type` requerido por el schema de la constitution no estaba presente en la estructura actual de documentos. Se agrega durante la ingesta sin romper nada existente.

## Project Structure

### Documentation (this feature)

```text
specs/002-local-vector-db/
├── plan.md              ← este archivo
├── research.md          ← Phase 0 (generado abajo)
├── data-model.md        ← Phase 1 (generado abajo)
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
etl/
├── ingest.py            [NUEVO] Script de ingesta unificado → ChromaDB
├── pipeline_sharepoint.py  [sin cambios]
├── pipeline_onprem.py      [sin cambios]
└── shared.py               [sin cambios]

agent/
├── retriever.py         [MODIFICAR] Reemplazar _search_local + agregar _get_embedding_fn()
└── ...                  [sin cambios]

data/
├── chroma_db/           [NUEVO, excluido de git] Índice vectorial persistido
├── jira_cloud_mock.json [sin cambios]
├── jira_mock.db         [sin cambios]
└── mock_sharepoint/     [sin cambios]

requirements.txt         [MODIFICAR] Agregar chromadb, openai
.gitignore               [MODIFICAR] Agregar data/chroma_db/
.env.example             [MODIFICAR] Documentar LMS_BASE_URL, LMS_EMBED_MODEL
```

**Structure Decision**: Proyecto único con ajustes mínimos. No se crean paquetes nuevos; se agrega un módulo ETL y se modifica un módulo de agente.

---

## Phase 0: Research

> Ver [`research.md`](./research.md) para detalle completo.

### Decisiones clave resueltas

| Decisión | Elección | Alternativas descartadas |
|---|---|---|
| DB Vectorial local | **ChromaDB** (PersistentClient) | FAISS (no tiene metadatos nativos, más burocrático); Qdrant (requiere servidor Docker) |
| Motor de embeddings | **LM Studio** con `nomic-embed-text-v1.5` | sentence-transformers en proceso (suma ~90MB+ al inicio del proceso Python, más lento en CPU); OpenAI API (externa, costo, latencia) |
| Modelo de embedding | **nomic-embed-text-v1.5 GGUF Q4** (~274 MB) | `bge-small-en-v1.5` (calidad menor, 512 tokens max); `all-MiniLM-L6-v2` (más viejo, menor MTEB) |
| Integración ChromaDB↔LM Studio | `OpenAIEmbeddingFunction` con `api_base` override | Clase custom (más código, igual resultado) |
| Fallback embedding | `bge-small-en-v1.5` cargado en LM Studio | N/A — ambos usan la misma ruta de código |

---

## Phase 1: Design & Contracts

### Data Model

> Ver [`data-model.md`](./data-model.md) para detalle completo.

#### Documento indexado en ChromaDB

Cada chunk que se ingesta en ChromaDB tiene:

```python
# ID único del documento
id: str            # e.g. "cloud_SUPP-104", "onprem_INT-22_0", "sp_reset-password_1"

# Texto embeddeable (enviado al modelo de embeddings)
document: str      # contenido del chunk (plain text)

# Metadatos almacenados junto al vector (no se embeddean)
metadata: {
    "source_id":   str,   # key del ticket o nombre del doc
    "source":      str,   # "jira_cloud" | "jira_onprem" | "sharepoint"
    "source_type": str,   # alias de source (requerido por constitution schema)
    "title":       str,   # resumen/nombre del documento
    "url":         str,   # referencia al origen
    "has_analyst_comment": bool  # constitution schema requirement
}
```

#### Colecciones ChromaDB

| Nombre | Fuente | Pipeline ETL | Embedding dim |
|---|---|---|---|
| `sharepoint` | `data/mock_sharepoint/*.html` | `pipeline_sharepoint.py` | 768 |
| `jira_onprem` | `data/jira_mock.db` (SQLite) | `pipeline_onprem.py` | 768 |
| `jira_cloud` | `data/jira_cloud_mock.json` | inline en `ingest.py` | 768 |

### Interface Contracts

#### Función pública del retriever (sin cambio de firma)

```python
def search(query: str, source_type: str, top: int = 4) -> List[Dict[str, Any]]:
    """
    Retorna hasta `top` documentos relevantes para `query` de la colección `source_type`.
    source_type: "sharepoint" | "jira_onprem" | "jira_cloud"
    
    Cada dict de retorno contiene: id, content, source, source_type, title, url
    Devuelve [] si la colección no existe o hay error.
    """
```

#### Función de embedding (nueva, interna)

```python
def _get_embedding_fn() -> OpenAIEmbeddingFunction:
    """
    Retorna la función de embedding apuntando a LM Studio.
    Lee LMS_BASE_URL (default: http://localhost:1234/v1) y 
    LMS_EMBED_MODEL (default: nomic-embed-text-v1.5) del entorno.
    """
```

#### Script de ingesta (CLI)

```bash
python -m etl.ingest
# opciones futuras: --source sharepoint|jira_onprem|jira_cloud
# Exit code 0 = éxito, 1 = error crítico
```

### Variables de entorno nuevas

| Variable | Default | Descripción |
|---|---|---|
| `LMS_BASE_URL` | `http://localhost:1234/v1` | URL base del servidor LM Studio |
| `LMS_EMBED_MODEL` | `nomic-embed-text-v1.5` | Nombre del modelo de embeddings cargado |
| `RETRIEVER_ENV` | *(vacío)* | Sin cambios: vacío→ChromaDB, `azure`→Azure AI Search |

### Quickstart (para ejecutar después de implementar)

1. Abrir LM Studio → pestaña **Local Server** → cargar `nomic-embed-text-v1.5` → Start Server
2. `pip install -r requirements.txt`
3. `python -m etl.ingest`  ← solo cuando cambian los datos
4. `python -m uvicorn api.main:app --reload`  ← el agente ya usa el índice

---

## Complexity Tracking

No hay violaciones de la constitution que requieran justificación. El cambio de `source` → `source_type` como campo de metadatos es una adición no destructiva.
