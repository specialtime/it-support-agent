---
description: "Task list template for feature implementation"
---

# Tasks: Agente de Soporte IT

**Input**: Design documents from `/specs/001-agente-soporte-it/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/api.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `agent/`, `api/`, `data/`, `etl/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Initialize Python environment and create `requirements.txt` in `/requirements.txt`
- [x] T002 [P] Create `.env.example` in `/.env.example`
- [x] T003 Create directory structure (`agent/`, `api/`, `services/`, `ui/`, `data/`, `etl/`, `tests/`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create AgentState and Agent roles schemas in `api/models.py`
- [x] T005 [P] Create abstract retriever interface in `agent/retriever.py`
- [x] T006 [P] Create LLM factory supporting "local" configs in `agent/llm.py`
- [x] T007 [P] Scaffold FastAPI app structure in `api/main.py`
- [x] T008 Setup common ETL utilities in `etl/shared.py` (text splitters, vector embeddings dummy placeholders)
- [x] T009 Create SQLite mock generator helper in `data/create_db.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Consulta Semántica Multi-Fuente (Priority: P1) 🎯 MVP

**Goal**: Búsqueda semántica usando LangGraph con RAG paralelo a 3 orígenes (Mock HTML, OnPrem SQLite, Jira Cloud JSON)
**Independent Test**: Lanzar una consulta directa al endpoint y validar que cite 2 origenes extraidos sin colisiones.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US1] Unit test for HTML parsing in `tests/test_etl.py`
- [x] T011 [P] [US1] Integration test for `/ask` endpoint routing to query RAG in `tests/test_api.py`

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement SharePoint HTML extractor logic in `etl/pipeline_sharepoint.py`
- [x] T013 [P] [US1] Implement On-Prem SQLite loader in `etl/pipeline_onprem.py`
- [x] T014 [US1] Implement RAG node functions (`rag_sharepoint`, `rag_onprem`, `search_cloud`) in `agent/nodes.py` (depends on Retriever)
- [x] T015 [US1] Implement `merge_and_rank` node logic with scores in `agent/nodes.py`
- [x] T016 [US1] Implement `graph.py` orchestrating the LangGraph parallel fan-out structure
- [x] T017 [US1] Implement `POST /ask` endpoint logic in `api/main.py` executing the graph compiled state

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Búsqueda Estructurada en Jira Cloud (Priority: P2)

**Goal**: Permitir llamadas precisas al backend de Jira Cloud saltando el proceso RAG.
**Independent Test**: Suministrar "dame el detalle de IT-C-089" y recibir el ticket formateado.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [x] T018 [P] [US2] Contract test for Jira internal APIs in `tests/test_api.py`
- [x] T019 [P] [US2] Tool schema validation test in `tests/test_tools.py`

### Implementation for User Story 2

- [x] T020 [P] [US2] Create Mock Jira Cloud API in `services/mock_jira_cloud_api/main.py`
- [x] T021 [P] [US2] Setup base mock data file `data/jira_cloud_mock.json`
- [x] T022 [US2] Implement `search_jira_cloud` and `get_jira_ticket` tools in `agent/tools.py`
- [x] T023 [US2] Update graph structure to include intent routing for "jira_search" in `agent/graph.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Operación: Reset de Contraseña (Priority: P3)

**Goal**: Disparar acciones restrictivas segurizadas por controles de rol sobre la sesión inyectada.
**Independent Test**: Validar que "role: user" falle (Unauthorized) y "role: helpdesk" sea procesado como ticket exitoso.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [x] T024 [P] [US3] Unit test for permission gating logic in `tests/test_graph.py`

### Implementation for User Story 3

- [x] T025 [P] [US3] Implement `reset_password` tool code binding in `agent/tools.py`
- [x] T026 [US3] Implement strict `check_permissions` node handler in `agent/nodes.py`
- [x] T027 [US3] Configure conditional edge in `agent/graph.py` linking `check_permissions` before `execute_tool`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Operación: Procesamiento de Archivo Excel (Priority: P4)

**Goal**: Capacidad de manipulación local de procesadores externos simulados (Excel/API).
**Independent Test**: Activar endpoint validando file transfer.

### Implementation for User Story 4

- [x] T028 [P] [US4] Implement `process_excel` tool stub in `agent/tools.py`
- [x] T029 [US4] Map processing intent inside the tool executor router in `agent/graph.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T028b [US1-3] Reemplazar router determinista (regex/keywords) en `classify_intent` por llamada al LLM local con `with_structured_output(IntentClassification)` — schema Pydantic `Literal["query","jira_search","action"]`. Fallback determinista conservado para CI/entornos sin LLM. Ver decisión arquitectónica 4 en `research.md`.
- [x] T030 Add robust tracing with `LangSmith` callbacks injecting runtime data into the application context across `api/main.py`.
- [x] T031 [P] Initial scaffold of Streamlit conversational interface in `ui/app.py`.
- [x] T032 Scaffold Azure Teams Hook (`/api/messages`) placeholder endpoint in `api/bot_handler.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May complement US1 routing logic.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on graph execution patterns defined in Phase 2/3.
- **User Story 4 (P4)**: Depends directly on US3 components (re-uses check_permissions nodes).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all test configurations targeting parsers and endpoints simultaneously:
Task: "Unit test for HTML parsing in tests/test_etl.py"
Task: "Integration test for /ask endpoint routing to query RAG in tests/test_api.py"

# Build source components independently while testing completes:
Task: "Implement SharePoint HTML extractor logic in etl/pipeline_sharepoint.py"
Task: "Implement On-Prem SQLite loader in etl/pipeline_onprem.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently via Swagger API UI testing RAG nodes.
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Expand routing scope
4. Add User Story 3 → Test independently → Validate Admin capabilities
5. Each story adds value without breaking previous stories (Continuous integration)
