# Tasks: Local Vector Database para IT Support Agent

**Input**: Design documents from `specs/002-local-vector-db/`  
**Branch**: `002-local-vector-db`  
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Organization**: Tasks agrupadas por user story para implementación y testing independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede correr en paralelo (archivos distintos, sin dependencias en tareas incompletas)
- **[Story]**: A qué user story pertenece la tarea (US1, US2, US3)
- Cada tarea incluye la ruta exacta del archivo

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuración inicial de dependencias y entorno

- [x] T001 Agregar `chromadb>=0.5.0` y `openai>=1.0.0` en `requirements.txt`
- [x] T002 [P] Agregar `data/chroma_db/` en `.gitignore`
- [x] T003 [P] Agregar variables `LMS_BASE_URL` y `LMS_EMBED_MODEL` documentadas en `.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Módulo de embedding compartido que bloquea TODO el trabajo posterior

**⚠️ CRITICAL**: Ninguna user story puede comenzar hasta completar esta fase

- [x] T004 Crear el módulo `etl/embedding.py` con la función `get_embedding_fn() -> OpenAIEmbeddingFunction` que lee `LMS_BASE_URL` y `LMS_EMBED_MODEL` del entorno (defaults: `http://localhost:1234/v1` y `nomic-embed-text-v1.5`) usando `chromadb.utils.embedding_functions.OpenAIEmbeddingFunction`
- [x] T005 Crear la función `get_chroma_client() -> PersistentClient` en `etl/embedding.py` que inicializa ChromaDB en `data/chroma_db/` con la ruta resuelta desde `BASE_DIR`

**Checkpoint**: Módulo de embedding y cliente ChromaDB disponibles — las user stories pueden comenzar

---

## Phase 3: User Story 1 — Ingesta unificada de fuentes de conocimiento (Priority: P1) 🎯 MVP

**Goal**: Script único `etl/ingest.py` que indexa las 3 fuentes en ChromaDB usando LM Studio como servidor de embeddings

**Independent Test**: Ejecutar `python -m etl.ingest` y verificar que existen 3 colecciones no vacías en `data/chroma_db/`. Verificable con `python -c "from etl.ingest import get_stats; print(get_stats())"`

### Implementation for User Story 1

- [x] T006 [P] [US1] Crear función `ingest_sharepoint(client, ef)` en `etl/ingest.py` que llama a `load_sharepoint_documents()` de `etl/pipeline_sharepoint.py` y hace `collection.upsert()` a la colección `sharepoint`, agregando `source_type` y `has_analyst_comment=False` a cada metadata
- [x] T007 [P] [US1] Crear función `ingest_jira_onprem(client, ef)` en `etl/ingest.py` que llama a `load_onprem_tickets()` de `etl/pipeline_onprem.py` y hace `collection.upsert()` a la colección `jira_onprem`, calculando `has_analyst_comment` desde los comentarios internos del ticket
- [x] T008 [P] [US1] Crear función `ingest_jira_cloud(client, ef)` en `etl/ingest.py` que lee `data/jira_cloud_mock.json` y hace `collection.upsert()` a la colección `jira_cloud`, construyendo IDs con patrón `cloud_{ISSUE_KEY}` y agregando `source_type="jira_cloud"` y `has_analyst_comment=False`
- [x] T009 [US1] Crear el bloque `if __name__ == "__main__"` en `etl/ingest.py` que instancia `get_chroma_client()` y `get_embedding_fn()` de `etl/embedding.py`, llama a las 3 funciones de ingesta en orden e imprime resumen de documentos ingestados por colección (depende de T006, T007, T008)
- [x] T010 [US1] Crear función `get_stats() -> dict` en `etl/ingest.py` que devuelve el conteo de documentos por colección (`sharepoint`, `jira_onprem`, `jira_cloud`) para facilitar verificación sin arrancar el agente
- [x] T011 [US1] Agregar manejo de errores en `etl/ingest.py`: si LM Studio no está disponible o una fuente de datos no existe, loguear advertencia con `warnings.warn()` y continuar sin abortar el script completo

**Checkpoint**: `python -m etl.ingest` completa exitosamente y `get_stats()` muestra documentos en las 3 colecciones

---

## Phase 4: User Story 2 — Búsqueda semántica desde el agente (Priority: P2)

**Goal**: Reemplazar `_search_local` en `agent/retriever.py` con búsqueda semántica via ChromaDB

**Independent Test**: Ejecutar `from agent.retriever import search; r = search("contraseña expirada vpn", "jira_cloud", 3); assert len(r) > 0 and "content" in r[0]` — debe retornar resultados relevantes sin coincidir exactamente con las palabras de la query

### Implementation for User Story 2

- [x] T012 [US2] Reemplazar la función `_search_local(query, source_type, top)` en `agent/retriever.py` con nueva implementación que: (1) obtiene el cliente ChromaDB via `get_chroma_client()` importado de `etl/embedding.py`, (2) obtiene `get_embedding_fn()`, (3) llama a `collection.query(query_texts=[query], n_results=top)`, (4) mapea los resultados al formato dict con claves `id`, `content`, `source`, `source_type`, `title`, `url`
- [x] T013 [US2] Agregar en `agent/retriever.py` el mapeo de `source_type` a nombre de colección ChromaDB: `{"sharepoint": "sharepoint", "jira_onprem": "jira_onprem", "jira_cloud": "jira_cloud"}` y manejo del caso en que la colección no exista (retornar `[]` con log de advertencia)
- [x] T014 [US2] Eliminar las funciones obsoletas `_init_cache()`, `clear_cache()` y la variable global `_doc_cache` de `agent/retriever.py`, ya que el estado es gestionado por ChromaDB (depende de T012, T013)
- [x] T015 [US2] Verificar que la función pública `search(query, source_type, top)` en `agent/retriever.py` mantiene su firma y flujo de enrutamiento: `RETRIEVER_ENV == "azure"` → `_search_azure()`, caso contrario → nueva `_search_local()` con ChromaDB

**Checkpoint**: `search("vpn", "jira_cloud", 4)` retorna hasta 4 resultados con búsqueda semántica. Los tests existentes en `tests/` pasan sin cambios.

---

## Phase 5: User Story 3 — Compatibilidad con interfaz existente del retriever (Priority: P3)

**Goal**: Garantizar que los nodos del grafo LangGraph no necesiten cambios en su código de llamada al retriever

**Independent Test**: Ejecutar `pytest tests/` sin modificar ningún test existente — todos deben pasar. El grafo LangGraph puede consultar las 3 fuentes via fan-out sin errores.

### Implementation for User Story 3

- [x] T016 [US3] Auditar todos los archivos en `agent/` que importan o llaman a `retriever.search()` y verificar que la firma `search(query: str, source_type: str, top: int = 4) -> List[Dict[str, Any]]` no fue modificada (solo lectura / validación, no cambios de código)
- [x] T017 [US3] Verificar que el dict de retorno de `_search_local` en `agent/retriever.py` incluye exactamente las claves que los nodos del grafo esperan: `id`, `content`, `source`, `title`, `url` (más `source_type` como campo adicional no destructivo). Ajustar el mapeo de resultados en T012 si alguna clave falta.
- [x] T018 [US3] Ejecutar `pytest tests/` y confirmar que todos los tests existentes pasan. Si algún test mockea `_doc_cache` o `_init_cache`, actualizarlo para mockear `chromadb.PersistentClient` en su lugar.

**Checkpoint**: Todos los tests existentes pasan. El grafo LangGraph puede operar sin cambios visibles.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Calidad, documentación y validación end-to-end

- [x] T019 [P] Actualizar el `README.md` del proyecto para documentar el paso de ingesta (`python -m etl.ingest`) y el prerequisito de LM Studio como servidor de embeddings
- [x] T020 [P] Crear `tests/test_ingest.py` con un test básico que verifique que `etl/ingest.py` corre sin errores contra los datos mock (puede mockear el cliente ChromaDB con `unittest.mock`)
- [x] T021 Actualizar `agent/retriever.py`: limpiar imports no utilizados (`json`, `string`) que dejó la implementación anterior de keyword search
- [x] T022 Validar el quickstart en `specs/002-local-vector-db/quickstart.md` ejecutando los pasos manualmente y confirmando que el flujo completo funciona: LM Studio running → `python -m etl.ingest` → `search()` retorna resultados semánticos

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** — T001, T002, T003: Sin dependencias, pueden comenzar inmediatamente y en paralelo
- **Foundational (Phase 2)** — T004, T005: Depende de T001 (requirements). Bloquea todas las user stories
- **US1 (Phase 3)** — T006-T011: Depende de T004, T005. T006-T008 pueden correr en paralelo entre sí
- **US2 (Phase 4)** — T012-T015: Depende de T004, T005. Puede correr en paralelo a US1 una vez completado Foundational
- **US3 (Phase 5)** — T016-T018: Depende de T012-T015 (US2 completo)
- **Polish (Phase 6)** — T019-T022: Depende de US1 + US2 + US3 completos

### User Story Dependencies

- **US1 (P1)**: Inicia después de Foundational — independiente de US2 y US3
- **US2 (P2)**: Inicia después de Foundational — puede desarrollarse en paralelo a US1
- **US3 (P3)**: Depende de US2 completado (valida la retrocompatibilidad de los cambios de US2)

### Within Each User Story

- T006, T007, T008 [US1] — paralelos entre sí (archivos y colecciones distintas)
- T009 [US1] — depende de T006, T007, T008
- T012, T013 [US2] — paralelos entre sí
- T014 [US2] — depende de T012, T013

### Parallel Opportunities

```bash
# Fase 1 — todo en paralelo:
T001 + T002 + T003

# Fase 2 — secuencial:
T004 → T005

# Fase 3 (US1) — T006, T007, T008 en paralelo, luego T009, T010, T011:
T006 + T007 + T008 → T009 → T010 → T011

# Fases 3 y 4 pueden correr en paralelo si hay capacidad:
[US1: T006-T011] || [US2: T012-T015]
```

---

## Parallel Example: User Story 1 (Ingesta)

```bash
# Lanzar las 3 ingestas en paralelo (archivos de datos independientes):
Task: "ingest_sharepoint() en etl/ingest.py → colección 'sharepoint'"
Task: "ingest_jira_onprem() en etl/ingest.py → colección 'jira_onprem'"
Task: "ingest_jira_cloud() en etl/ingest.py → colección 'jira_cloud'"

# Luego unificar:
Task: "bloque __main__ + get_stats() en etl/ingest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Completar Phase 1: Setup (T001-T003)
2. Completar Phase 2: Foundational (T004-T005) ← **CRÍTICO, desbloquea todo**
3. Completar Phase 3: US1 — script de ingesta (T006-T011)
4. **STOP y VALIDAR**: `python -m etl.ingest` exitoso, `get_stats()` muestra documentos
5. Completar Phase 4: US2 — retriever semántico (T012-T015)
6. **STOP y VALIDAR**: `search()` retorna resultados semánticos
7. Completar Phase 5: US3 — retrocompatibilidad (T016-T018)
8. Polish (T019-T022)

### Incremental Delivery

1. Setup + Foundational → módulo de embedding listo
2. US1 (ingesta) → datos indexados, verificable independientemente
3. US2 (retriever) → agente con búsqueda semántica, verificable con cualquier query
4. US3 (retrocompatibilidad) → tests completos pasan, sin regresiones

---

## Notes

- [P] = archivos distintos, sin dependencias entre sí
- [Story] = trazabilidad a user story de spec.md
- No se generan tests nuevos salvo `tests/test_ingest.py` (T020) — los tests existentes deben pasar sin modificación (US3)
- El índice `data/chroma_db/` nunca se versiona; cada entorno ejecuta su propia ingesta
- LM Studio debe estar corriendo con `nomic-embed-text-v1.5` cargado antes de T006-T011
- Si LM Studio no está disponible, T006-T011 fallarán con `ConnectionRefusedError` — esperado
