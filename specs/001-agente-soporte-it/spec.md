# Feature Specification: Agente de Soporte IT

**Feature Branch**: `001-agente-soporte-it`  
**Created**: 2026-04-11  
**Status**: Draft  
**Input**: User description: "revisa las historias, casos de uso y requerimientos en [plan-agente-soporte-it-v4.md]"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consulta Semántica Multi-Fuente (Priority: P1)

El usuario (empleado buscando ayuda IT o soporte) describe un problema (e.g., error 403 en ERP). El agente busca en tres fuentes simultáneas, consolida la información y provee una respuesta detallada citando el origen exacto.

**Why this priority**: Es la funcionalidad central (Core) de conocimiento RAG (Retrieval-Augmented Generation), y brinda el mayor valor inmediato a los usuarios que necesitan resolver problemas cotidianos, incidentes comunes o buscar bugs conocidos.

**Independent Test**: Se puede probar localmente y en la nube inyectando consultas y verificando en la bitácora si el agente ejecuta búsquedas en paralelo, devolviendo referencias al documento SharePoint y/o el ticket Jira correspondiente en el top de contexto.

**Acceptance Scenarios**:

1. **Given** un problema descrito en lenguaje natural, **When** el agente procesa la consulta de un actor con rol `user`, **Then** el mismo busca en las 3 fuentes (SharePoint, On-Prem, Cloud) en paralelo, fusiona resultados priorizando con scoring y responde citando el título/ID de cada origen preciso.
2. **Given** que no existe información pertinente en la base de datos de conocimiento, **When** un usuario consulta, **Then** el agente debe declarar abiertamente que no tiene info, evitar alucinaciones, y sugerir abrir un nuevo caso.

---

### User Story 2 - Búsqueda Estructurada en Jira Cloud (Priority: P2)

El actor (analista HelpDesk o User) necesita averiguar el detalle de un ID de ticket específico o ver todos los tickets críticos activos para ERP desde la herramienta conversacional, en lugar del buscador semántico difuso.

**Why this priority**: Acelera el workflow del Support Team para consultas diarias sin tener que acceder a la interfaz web completa de un tracker de tickets, obteniendo listados o detalles directos.

**Independent Test**: Verificable introduciendo un ID explícitamente existente (e.g., IT-C-089) o filtros estructurados; las trazas deben mostrar que el agente clasificó el *intent* de forma correcta y llamó a la Mock Cloud API saltándose el fan-out.

**Acceptance Scenarios**:

1. **Given** una consulta como "dame el detalle del caso IT-C-089", **When** se le consulta al agente, **Then** invoca la "API tool" pertinente enviando el tag y retorna el resumen del ticket.
2. **Given** una solicitud de "listar tickets críticos ERP", **When** el rol sea válido, **Then** extrae la lista de tickets de la herramienta de filtrado estructurado.

---

### User Story 3 - Operación: Reset de Contraseña (Priority: P3)

El analista reacciona ante un caso y decide ejecutar una directiva para resetear un password en el ERP remoto en nombre del usuario, gatillando el proceso directamente en el chat.

**Why this priority**: Descarga el trabajo técnico al proveer self-service asistido que automatiza tareas manuales rutinarias. 

**Independent Test**: Ejecutar la herramienta `reset_password` comprobando los bloqueos por jerarquías (e.g., rol `user` vs rol `admin`/`helpdesk`).

**Acceptance Scenarios**:

1. **Given** la orden de resetear contraseña de ERP, **When** el requester tiene asignado el rol `user` (default), **Then** el agente rechaza cortésmente la acción por falta de permisos.
2. **Given** la misma instrucción, **When** el requester tiene asignado rol `helpdesk` o `admin`, **Then** se ejecuta la simulación de la tool exitosamente y se confirma en formato texto.

---

### User Story 4 - Operación: Procesamiento de Archivo Excel (Priority: P4)

El usuario autorizado (helpdesk/admin) pide al sistema procesar un archivo excel a través de una API externa pasando una ruta local y un trigger explícito.

**Why this priority**: Funcionalidad complementaria de automatización para flujos de trabajo muy específicos de la mesa de ayuda IT.

**Independent Test**: Suministrar una ruta válida y un flag de procesamiento; verificar si llega la respuesta simulada con la URL de salida y que no sea ejecutada por perfiles bajos.

**Acceptance Scenarios**:

1. **Given** la instrucción de subir el excel `/tmp/data.xlsx` con proceso `X`, **When** un `admin` lo solicita, **Then** la orden activa el endpoint de procesado y devuelve ok.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST process unstructured natural language questions and route them internally to "query" paths.
- **FR-002**: System MUST classify explicit ticket-reference interactions or searches as a tool-based intent ("jira_search").
- **FR-003**: System MUST execute standard RAG queries through a simultaneous fan-out search over all 3 data stores (SharePoint, Jira OnPrem, Jira Cloud).
- **FR-004**: System MUST strictly restrict execution capabilities for mutating tools (`reset_password`, `process_excel`) to pre-authorized roles (`helpdesk`, `admin`).
- **FR-005**: System MUST cite source type (e.g. [On-Prem], [SharePoint HTML mock]) and document-ID within its generated LLM answers to provide auditable references.
- **FR-006**: System MUST isolate vector-store infrastructure logic so switching from `local` to `azure` is solely dictated by the `RETRIEVER_ENV` variable.
- **FR-007**: System MUST emit traces to LangSmith for observability into every graph step (routing, retrieving, merging, responding).

### Key Entities

- **Knowledge Chunk (Retrieved Document)**: Represents a fragment from the indexing stores, carrying essential schema fields uniformly across sources (`id`, `source_type`, `content`, `has_analyst_comment`).
- **Agent State**: An encapsulated context instance keeping track of the `messages`, assigned `user_role`, current `intent`, retrieved docs split by origin, final merged `context`, and system status vectors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90%+ routing accuracy separating unstructured knowledge questions from explicit structured Jira searches.
- **SC-002**: Full fan-out RAG processing must complete and respond to the endpoint in under 8 seconds.
- **SC-003**: 100% of malicious execution attempts for password reset/tools by standard users are actively intercepted and blocked.
- **SC-004**: The system's retrieved chunks accurately include HTML parser derivations from SharePoint rather than generic text artifacts.

## Assumptions

- SharePoint data represents static `.html` knowledge articles.
- Jira Cloud information is available as mocked JSON records and accessed synchronously.
- Users converse in Spanish as default (matching organizational layout in mock resources).
- System execution occurs locally first before full migration to an Azure architecture.
