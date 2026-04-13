---
description: "Task list template for feature implementation"
---

# Tasks: Improve Main UI

**Input**: Design documents from `/specs/003-improve-main-ui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create `frontend` directory structure (`frontend/src/css`, `frontend/src/js/components`) per implementation plan
- [x] T002 Initialize `frontend/index.html` with basic skeleton, importing Google Fonts (Inter) y configurando el `<head>`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Implementar variables CSS base (colores oscuros premium, fuentes) en `frontend/src/css/index.css`
- [x] T004 [P] Crear el modelo de red en `frontend/src/js/api.js` para comunicarse con la API nativa de FastAPI (endpoint `/ask`)
- [x] T005 Crear la gestión del estado global (UI State) y utilidades genéricas en `frontend/src/js/main.js`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Modernized Chat Interface (Priority: P1) 🎯 MVP

**Goal**: Crear una interfaz de chat dinámica, fluida y con excelente diseño premium.

**Independent Test**: Poder cargar el index.html en el navegador, escribir en el input de texto, enviarlo, y recibir un mensaje con burbujas de estilo impecable y animaciones suaves sin depender de ajustes avanzados.

### Implementation for User Story 1

- [x] T006 [P] [US1] Añadir estructura HTML del contenedor de chat y la barra inferior de envío a `frontend/index.html`
- [x] T007 [P] [US1] Estilizar componentes de chat (burbujas `MessageObj`, scroll, input form) con transiciones suaves en `frontend/src/css/index.css`
- [x] T008 [US1] Implementar renderizador dinámico de mensajes en el DOM a través de `frontend/src/js/main.js`
- [x] T009 [US1] Ligar el evento del teclado y envío al frontend con `frontend/src/js/api.js` y reflejar los estados de carga (typing indicators)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Premium Settings Panel (Priority: P2)

**Goal**: Interfaz de control lateral/superior (panel de ajustes y roles) estéticamente rica, con respuesta visual instantánea.

**Independent Test**: Modificar los controles (ej. selector de Rol) y observar al instante animaciones en cada iteración y correcta inyección de parámetros.

### Implementation for User Story 2

- [x] T010 [P] [US2] Diseñar la plantilla HTML para el Panel Lateral de opciones y Selección de Rol en `frontend/index.html`
- [x] T011 [P] [US2] Proveer estilos ricos (hovers, glassmorphism, botones elegantes) en `frontend/src/css/index.css` para el panel
- [x] T012 [US2] Conectar los contoles del panel al payload HTTP en `frontend/src/js/api.js`
- [x] T013 [US2] Implementar micro-animaciones interactivos por JS y manipular el UI State en `frontend/src/js/main.js` 

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T014 Depurar sistema viejo y eliminar la antigua UI de Streamlit (`ui/app.py` y `ui/`)
- [x] T015 Ajustes en responsividad global (Media Queries finales) en `frontend/src/css/index.css`
- [x] T016 Validación manual final utilizando pasos de `specs/003-improve-main-ui/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1) proceeds before User Story 2 (P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Se acopla visualmente a US1 pero su lógica de panel es independiente.

### Parallel Opportunities

- Creación de estructuras CSS vs creación de estructuras JS API pueden correr en paralelo (ej. `T003` y `T004`).
- Modificación del HTML vs CSS (ej `T006` y `T007` o `T010` y `T011`).

---

## Parallel Example: User Story 1

```bash
# Developer A focuses on markup and styling:
Task: "T006 [P] [US1] Añadir estructura HTML del contenedor de chat..."
Task: "T007 [P] [US1] Estilizar componentes de chat (burbujas)..."

# Developer B focuses on API parsing and DOM interaction:
Task: "T008 [US1] Implementar renderizador dinámico de mensajes en el DOM..."
Task: "T009 [US1] Ligar el evento del teclado y envío al frontend con api.js..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently abriendo `frontend/index.html`.
5. Deploy/demo if ready

### Incremental Delivery

1. Se entrega Setup + Foundational.
2. Se completa la interfaz de Chat Central. Se verifica.
3. Se integran los paneles de configuración y control de roles. Se verifica integralmente.
4. Se pule, se elimina lo no utilzado.
