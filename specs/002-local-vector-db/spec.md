# Feature Specification: Local Vector Database para IT Support Agent

**Feature Branch**: `002-local-vector-db`  
**Created**: 2026-04-12  
**Status**: Draft  
**Input**: User description: "Implementing Local Vector Database con lo que hablamos hasta ahora"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingesta unificada de fuentes de conocimiento (Priority: P1)

Como desarrollador/operador del sistema, quiero ejecutar un script de ingesta único que procese las tres fuentes de datos (Jira Cloud, base de datos on-premise y SharePoint) y las indexe en una base de datos vectorial local, para que el agente pueda realizar búsquedas semánticas sin depender de servicios externos.

**Why this priority**: Sin el índice vectorial poblado, el agente no puede responder consultas. Es el prerequisito fundamental de toda la feature.

**Independent Test**: Puede probarse ejecutando el script de ingesta contra datos mock existentes y verificando que se crean colecciones con documentos en la carpeta `data/chroma_db/`.

**Acceptance Scenarios**:

1. **Given** que existen los archivos de datos (`jira_cloud_mock.json`, `jira_mock.db`, archivos HTML en `mock_sharepoint/`), **When** se ejecuta el script de ingesta, **Then** se crean tres colecciones (`sharepoint`, `jira_onprem`, `jira_cloud`) en el índice vectorial local con al menos un documento cada una.
2. **Given** que el script de ingesta ya fue ejecutado previamente, **When** se vuelve a ejecutar, **Then** los documentos son actualizados (upsert) sin duplicados ni errores.
3. **Given** que una de las fuentes de datos no existe o está vacía, **When** se ejecuta la ingesta, **Then** el script continúa sin detenerse, registra un aviso y procesa las fuentes disponibles.

---

### User Story 2 - Búsqueda semántica desde el agente (Priority: P2)

Como agente de soporte IT, quiero consultar el índice vectorial local para encontrar tickets, documentos y procedimientos relevantes a la consulta del usuario, para que las respuestas sean contextualmente precisas incluso cuando la consulta no usa las palabras exactas del documento.

**Why this priority**: Reemplaza el motor de búsqueda actual por keyword que es frágil. Es el cambio de comportamiento central que aporta valor semántico.

**Independent Test**: Puede probarse enviando una consulta al retriever y verificando que devuelve documentos relevantes con semejanza semántica (no solo coincidencia de palabras clave).

**Acceptance Scenarios**:

1. **Given** que el índice vectorial está poblado, **When** el agente consulta por una frase semánticamente cercana a un ticket existente (sin usar las palabras exactas), **Then** el retriever devuelve ese ticket entre los resultados top.
2. **Given** que se consulta por `source_type="sharepoint"`, **When** se realiza la búsqueda, **Then** solo se devuelven documentos de la colección SharePoint.
3. **Given** que la colección solicitada no existe o el índice está vacío, **When** se realiza la búsqueda, **Then** el retriever devuelve una lista vacía sin lanzar excepciones no controladas.

---

### User Story 3 - Compatibilidad con la interfaz existente del retriever (Priority: P3)

Como desarrollador, quiero que el nuevo retriever vectorial mantenga la misma firma de función `search(query, source_type, top)` que la implementación actual, para que todos los nodos del grafo LangGraph funcionen sin cambios en su código de llamada.

**Why this priority**: Permite integrar la nueva capacidad sin refactorizar los nodos del agente. Reduce el riesgo de regresiones.

**Independent Test**: Puede verificarse ejecutando los tests existentes (`pytest tests/`) después del cambio y confirmando que todos pasan.

**Acceptance Scenarios**:

1. **Given** el nuevo retriever instalado, **When** se llama a `search(query="vpn reset", source_type="jira_cloud", top=4)`, **Then** se devuelve una lista de hasta 4 dicts con claves `id`, `content`, `source`, `title`, `url`.
2. **Given** la variable de entorno `RETRIEVER_ENV=azure`, **When** se llama a `search()`, **Then** se sigue enrutando a la implementación de Azure sin modificaciones.

---

### Edge Cases

- ¿Qué ocurre si el modelo de embeddings no está descargado localmente al primer arranque?
- ¿Qué pasa si el directorio `data/chroma_db/` fue eliminado pero el agente intenta consultar el índice?
- ¿Cómo se comporta la ingesta si un documento tiene contenido vacío o excesivamente largo?
- ¿El índice vectorial puede corromperse si el proceso de ingesta se interrumpe a mitad?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE contar con un script de ingesta (`etl/ingest.py`) que lea las tres fuentes de datos y las indexe en colecciones separadas dentro de la base de datos vectorial local.
- **FR-002**: El script de ingesta DEBE soportar ejecución idempotente: múltiples ejecuciones sobre los mismos datos no deben generar duplicados (upsert).
- **FR-003**: La base de datos vectorial DEBE persistir en disco dentro del directorio `data/chroma_db/` para sobrevivir reinicios del proceso.
- **FR-004**: El retriever DEBE usar búsqueda por similitud semántica (embeddings) en lugar de coincidencia de keywords.
- **FR-005**: Los embeddings DEBEN generarse a través del servidor local de LM Studio (API compatible con OpenAI en `http://localhost:1234/v1`), usando un modelo de embeddings liviano y de alta calidad cargado en LM Studio. No se requieren dependencias adicionales de inferencia de modelos en el proceso Python.
- **FR-006**: El retriever DEBE respetar el parámetro `source_type` filtrando la búsqueda a la colección correspondiente (`sharepoint`, `jira_onprem`, `jira_cloud`).
- **FR-007**: La función `search(query, source_type, top)` DEBE mantener la misma firma y estructura de datos de retorno que la implementación actual.
- **FR-008**: El sistema DEBE manejar errores de forma elegante: colección inexistente, índice vacío o corrupción deben devolver lista vacía con log de advertencia, no excepción no controlada.
- **FR-009**: Las nuevas dependencias DEBEN declararse en `requirements.txt`.
- **FR-010**: El directorio `data/chroma_db/` DEBE agregarse al `.gitignore` para evitar incluir el índice binario en el repositorio.

### Key Entities

- **VectorIndex**: Representación persistida en disco de los embeddings de todos los documentos, organizado por colecciones por fuente de datos.
- **Colección**: Subconjunto del índice vectorial correspondiente a una fuente específica (`sharepoint`, `jira_onprem`, `jira_cloud`). Cada colección tiene su propio espacio de búsqueda.
- **Documento indexado**: Unidad atómica del índice. Contiene el texto del chunk, su embedding calculado y metadatos (`source`, `title`, `url`, `source_id`).
- **EmbeddingModel**: Modelo de lenguaje ligero usado para transformar texto en vectores numéricos. Se descarga una vez y se reutiliza localmente sin conexión.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El script de ingesta procesa la totalidad de los datos mock existentes (Jira Cloud JSON, SQLite on-prem, HTMLs de SharePoint) en menos de 60 segundos en hardware de desarrollo estándar.
- **SC-002**: Una consulta semántica al índice vectorial devuelve resultados en menos de 2 segundos para colecciones de hasta 10.000 documentos.
- **SC-003**: El retriever vectorial retorna al menos un resultado relevante para el 90% de las consultas de prueba que antes fallaban con el motor de keywords (consultas con sinónimos o paráfrasis).
- **SC-004**: Todos los tests existentes del proyecto (`pytest tests/`) continúan pasando tras la integración del nuevo retriever, sin regresiones.
- **SC-005**: La ingesta ejecutada dos veces sobre los mismos datos produce exactamente la misma cantidad de documentos en el índice (idempotencia verificable).
- **SC-006**: El índice persiste correctamente entre reinicios de la aplicación, y el agente puede consultar documentos indexados previamente sin necesidad de re-ingestar.

## Assumptions

- Se asume que LM Studio está instalado y corriendo localmente en el puerto 1234 con un modelo de embeddings cargado antes de ejecutar la ingesta o iniciar el agente.
- El modelo de embeddings recomendado es `nomic-embed-text-v1.5` (~274 MB GGUF Q4): ofrece el mejor balance entre calidad (MTEB alto), tamaño reducido y soporte de contexto largo (8k tokens). Como alternativa más liviana: `bge-small-en-v1.5` (~33M params, 384d).
- El servidor de embeddings de LM Studio expone un endpoint OpenAI-compatible en `http://localhost:1234/v1/embeddings` que el código Python consume con el cliente `openai`.
- Los datos mock actuales en `data/` son representativos de la carga real esperada a corto plazo (cientos de tickets, no millones).
- La variable de entorno `RETRIEVER_ENV` se mantiene como mecanismo de enrutamiento: valor vacío/ausente → ChromaDB local; valor `"azure"` → Azure AI Search (sin cambios en esa rama).
- El directorio de datos (`data/chroma_db/`) no se versiona en Git; cada entorno (local, CI) ejecuta la ingesta de forma independiente.
- Los pipelines ETL existentes (`etl/pipeline_sharepoint.py`, `etl/pipeline_onprem.py`) se reutilizan sin modificaciones para la extracción y chunking de documentos.
- Escalar a producción (miles de fuentes, índices distribuidos) queda fuera del alcance de esta feature; el diseño local es suficiente para la fase actual del proyecto.
