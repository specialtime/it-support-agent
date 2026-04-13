# Research: Local Vector Database — Decisiones técnicas

**Feature**: Local Vector Database para IT Support Agent  
**Branch**: `002-local-vector-db`  
**Date**: 2026-04-12

---

## Decisión 1: Base de Datos Vectorial

**Decision**: ChromaDB con `PersistentClient`

**Rationale**:
- Persistencia en disco sin servidor externo (una carpeta `data/chroma_db/`)
- API Python nativa con soporte de metadatos por documento
- Integración directa con LangChain (`Chroma` vectorstore)
- Soporta `upsert` nativo → ingesta idempotente
- Licencia Apache 2.0, activamente mantenida

**Alternatives considered**:
- **FAISS**: sin soporte de metadatos nativos; requiere serialización manual; no tiene `upsert`
- **Qdrant**: servidor Docker independiente necesario; overhead innecesario para escala local
- **LanceDB**: menos ecosistema Python; menor integración con LangChain
- **Weaviate**: requiere Docker, stack completo; excesivo para fase local

---

## Decisión 2: Motor de Embeddings

**Decision**: LM Studio como servidor de embeddings (API OpenAI-compatible en `http://localhost:1234/v1`)

**Rationale**:
- El usuario ya usa LM Studio para el LLM; consistencia de stack
- Expone `/v1/embeddings` compatible con `openai` Python SDK sin cambios de código
- No agrega dependencias de ML al proceso Python (sin PyTorch, sin sentence-transformers)
- Elimina el tiempo de descarga/carga del modelo en cada arranque del agente (ya está en LM Studio)
- Configuración mediante variables de entorno → mismo mecanismo que `LLM_ENV` y `RETRIEVER_ENV`

**Alternatives considered**:
- **sentence-transformers en proceso**: suma PyTorch (~2GB de dependencias), carga lenta en CPU, más complejo de gestionar versiones
- **OpenAI API Embeddings**: externa, requiere API key, costo por token, latencia de red
- **Ollama embeddings**: válido pero el usuario ya tiene LM Studio; mantener un solo servidor local

---

## Decisión 3: Modelo de Embeddings

**Decision**: `nomic-embed-text-v1.5` (GGUF Q4_K_M, ~274 MB)

**Rationale**:

| Modelo | Params | Dim | Contexto | MTEB Score | Tamaño GGUF |
|---|---|---|---|---|---|
| **nomic-embed-text-v1.5** | 137M | 768 | **8k tokens** | ~62 (alto) | ~274 MB Q4 |
| bge-small-en-v1.5 | 33M | 384 | 512 tokens | ~51 | ~45 MB |
| all-MiniLM-L6-v2 | 22M | 384 | 512 tokens | ~47 | ~45 MB |

- Contexto de 8k tokens: los tickets de Jira pueden ser largos (con comentarios); evita perder información por truncado
- Embeddings de 768 dimensiones: mejor capacidad de distinción semántica
- Matryoshka Representation Learning: permite reducir dimensiones en el futuro sin re-indexar
- Disponible en LM Studio como modelo descargable directo
- Alternativa aceptable: `bge-small-en-v1.5` si se prioriza velocidad y memoria

**Alternatives considered**:
- `all-MiniLM-L6-v2`: más antiguo, MTEB inferior, no disponible como GGUF en LM Studio
- `bge-large-en-v1.5`: mejor calidad pero ~1.3GB; excesivo para esta escala
- `e5-small-v2`: menor MTEB que bge-small

---

## Decisión 4: Integración ChromaDB ↔ LM Studio

**Decision**: `OpenAIEmbeddingFunction` de ChromaDB con `api_base` apuntando a LM Studio

**Rationale**:
- LM Studio expone exactamente el mismo contrato que OpenAI `/v1/embeddings`
- `chromadb.utils.embedding_functions.OpenAIEmbeddingFunction` acepta `api_base` override
- Código mínimo, sin clase custom
- Fallback: implementar clase custom `LMStudioEmbeddingFunction(EmbeddingFunction)` si se necesita control de errores granular

```python
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

ef = OpenAIEmbeddingFunction(
    api_key="lm-studio",          # LM Studio ignora el api_key
    api_base="http://localhost:1234/v1",
    model_name="nomic-embed-text-v1.5"
)
```

**Alternatives considered**:
- Clase custom `EmbeddingFunction`: mismo resultado, más código innecesario
- `langchain_openai.OpenAIEmbeddings` con `base_url`: válido para LangChain pero no integra con ChromaDB directamente

---

## Decisión 5: Idempotencia de ingesta

**Decision**: ChromaDB `collection.upsert()` con IDs deterministas

**Rationale**:
- `upsert` actualiza si el ID existe, inserta si no
- IDs construidos con patrón `{source}_{key}_{chunk_index}` son deterministas
- Re-ejecutar la ingesta es seguro; produce el mismo estado final

---

## Decisión 6: Compatibilidad de Schema

**Decision**: agregar `source_type` como campo de metadatos (alias de `source`)

**Rationale**:
- La constitution exige: `id`, `source_type`, `content`, `has_analyst_comment` en cada chunk
- La implementación actual usa `source` (no `source_type`)
- Solución: agregar ambos campos en los metadatos — no rompe el código existente
- `has_analyst_comment` = False por defecto para Jira Cloud/SharePoint; True si hay comentario interno en on-prem
