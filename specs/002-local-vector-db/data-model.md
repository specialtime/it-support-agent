# Data Model: Local Vector Database

**Feature**: Local Vector Database para IT Support Agent  
**Branch**: `002-local-vector-db`  
**Date**: 2026-04-12

---

## Entidades principales

### 1. DocumentoIndexado (chunk en ChromaDB)

Unidad atómica del índice. Representa un fragmento de texto con su embedding y metadatos.

| Campo | Tipo | Descripción | Requerido por constitution |
|---|---|---|---|
| `id` | `str` | ID único del chunk. Patrón: `{source}_{key}_{idx}` | — |
| `document` | `str` | Texto del chunk (contenido embeddeable) | — |
| `source_id` | `str` | Identificador del documento original (ej: `SUPP-104`) | — |
| `source` | `str` | Nombre de la fuente: `jira_cloud`, `jira_onprem`, `sharepoint` | — |
| `source_type` | `str` | Alias de `source` requerido por el schema de la constitution | ✅ |
| `title` | `str` | Resumen/nombre del documento original | — |
| `url` | `str` | Referencia al origen (`cloud://SUPP-104`, `sqlite://INT-22`, `https://...`) | — |
| `has_analyst_comment` | `bool` | True si el ticket tiene comentario interno/de analista | ✅ |

### 2. Colección ChromaDB

Agrupación de DocumentosIndexados por fuente de datos.

| Colección | Fuente de datos | Pipeline de extracción | Notas |
|---|---|---|---|
| `sharepoint` | Archivos `.html` en `data/mock_sharepoint/` | `etl/pipeline_sharepoint.py` | Chunking por párrafo |
| `jira_onprem` | `data/jira_mock.db` (SQLite: tablas `issues` + `comments`) | `etl/pipeline_onprem.py` | `has_analyst_comment=True` si hay comentario interno |
| `jira_cloud` | `data/jira_cloud_mock.json` (array `issues`) | `etl/ingest.py` (inline) | Primero: JSON completo como contenido |

### 3. EmbeddingFunction

Adaptador entre el texto y LM Studio.

| Atributo | Valor |
|---|---|
| API endpoint | `${LMS_BASE_URL}/embeddings` (default: `http://localhost:1234/v1`) |
| Modelo | `${LMS_EMBED_MODEL}` (default: `nomic-embed-text-v1.5`) |
| Dimensión de output | 768 |
| Contexto máximo | 8.192 tokens |
| Protocolo | OpenAI `/v1/embeddings` compatible |

---

## Patrones de ID por fuente

```
Jira Cloud:   cloud_{ISSUE_KEY}
              e.g. cloud_SUPP-104

Jira On-Prem: onprem_{ISSUE_KEY}_{CHUNK_IDX}
              e.g. onprem_INT-22_0, onprem_INT-22_1

SharePoint:   sp_{DOC_TITLE}_{CHUNK_IDX}
              e.g. sp_reset-password_0
```

---

## Estado hasAnalystComment por fuente

| Fuente | Lógica |
|---|---|
| `jira_cloud` | `False` (el mock JSON no distingue comentarios internos) |
| `jira_onprem` | `True` si algún `comment.is_internal = 1` en el ticket |
| `sharepoint` | `False` (documentos de KB, no tickets) |

---

## Transformación de retorno del retriever

El dict devuelto por `search()` mapea los campos de ChromaDB a la estructura esperada por el grafo:

```python
{
    "id":       result["ids"][0][i],
    "content":  result["documents"][0][i],
    "source":   result["metadatas"][0][i]["source"],
    "source_type": result["metadatas"][0][i]["source_type"],
    "title":    result["metadatas"][0][i]["title"],
    "url":      result["metadatas"][0][i]["url"],
}
```
