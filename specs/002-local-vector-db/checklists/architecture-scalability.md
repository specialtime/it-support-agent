# Architecture Scalability Checklist: Local Vector Database

**Purpose**: Validate that scalability and extensibility requirements are well-specified — ensuring the local ChromaDB implementation can migrate to Azure AI Search or other index providers without surprises
**Created**: 2026-04-12
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md) | [research.md](../research.md)
**Focus**: Architecture extensibility, retriever abstraction, cloud migration path

---

## Requirement Completeness — Retriever Abstraction

- [ ] CHK001 - ¿La spec define explícitamente que la interfaz pública `search()` es el único punto de contacto entre el grafo LangGraph y la infraestructura de búsqueda? [Completeness, Gap — spec menciona firma pero no el contrato de aislamiento]
- [ ] CHK002 - ¿Están documentados en la spec todos los valores válidos de `RETRIEVER_ENV` y el comportamiento esperado para cada uno (`""` → ChromaDB, `"azure"` → Azure AI Search)? [Completeness, Spec §Assumptions]
- [ ] CHK003 - ¿La spec define qué ocurre cuando `RETRIEVER_ENV` tiene un valor desconocido (ej: `"pinecone"`)? [Coverage, Gap — no hay requisito para valor inválido]
- [ ] CHK004 - ¿Existe un requisito que especifique que agregar un nuevo proveedor de índice NO debe requerir cambios en los nodos del grafo LangGraph? [Completeness, Gap]
- [ ] CHK005 - ¿El plan documenta el contrato que deben cumplir todas las implementaciones de retriever (firma, tipos de retorno, campos garantizados)? [Completeness, Plan §Interface Contracts]

---

## Requirement Clarity — Abstracción de Embeddings

- [ ] CHK006 - ¿La spec especifica qué proveedor de embeddings se usaría al migrar a Azure AI Search? (Azure AI también tiene su propio modelo de embeddings; ¿se mantendría LM Studio? ¿se usaría Azure OpenAI Embeddings?) [Clarity, Gap — FR-005 solo aplica a escenario local]
- [ ] CHK007 - ¿Está claramente definido si la función `get_embedding_fn()` debe ser intercambiable por proveedor (es decir, si en Azure se usa un embedding distinto) o si el vector producido por LM Studio debe ser compatible bit-a-bit con el índice de Azure? [Clarity, Ambiguity]
- [ ] CHK008 - ¿La spec documenta que la dimensión de embedding (768d para nomic-embed-text) debe mantenerse consistente entre el índice local y cualquier índice cloud para evitar re-indexación? [Clarity, Gap]

---

## Requirement Consistency — Ingesta vs. Retrieval

- [ ] CHK009 - ¿Los requisitos de ingesta (`etl/ingest.py`) son consistentes con los requisitos del retriever en cuanto al schema de metadatos? ¿Ambos lados documentan los mismos campos requeridos (`source_type`, `has_analyst_comment`)? [Consistency, Spec §FR-001 y §data-model]
- [ ] CHK010 - ¿El schema de metadatos definido en `data-model.md` es suficientemente agnóstico como para ser usado tanto en ChromaDB como en Azure AI Search (que tiene su propio esquema de campos)? [Consistency, Gap]
- [ ] CHK011 - ¿Los IDs deterministas (`cloud_SUPP-104`, `onprem_INT-22_0`) definidos en el data model son compatibles con las restricciones de formato de IDs de Azure AI Search (sin `/`, sin caracteres especiales, max 1024 chars)? [Consistency, Gap]

---

## Coverage — Escenarios de Migración Cloud

- [ ] CHK012 - ¿La spec o el plan definen un escenario de migración desde ChromaDB a Azure AI Search sin downtime del agente? [Coverage, Gap]
- [ ] CHK013 - ¿Están especificados los requisitos para una ejecución de ingesta cloud (¿el mismo `etl/ingest.py` o un script distinto para Azure AI Search Indexer?) [Coverage, Gap]
- [ ] CHK014 - ¿El plan documenta si el índice ChromaDB y el índice Azure pueden coexistir simultáneamente durante una migración gradual? [Coverage, Gap]
- [ ] CHK015 - ¿La spec cubre el escenario donde el mismo documento existe en el índice local y en Azure con IDs distintos (riesgo de inconsistencia)? [Coverage, Edge Case]

---

## Acceptance Criteria Quality — Escalabilidad

- [ ] CHK016 - ¿Los Success Criteria incluyen métricas de escala para el escenario cloud? (Los SC-001 y SC-002 aplican solo a escala local "hasta 10.000 documentos" — ¿hay criterios para escala mayor?) [Measurability, Spec §SC-001, SC-002]
- [ ] CHK017 - ¿El SC-004 (tests existentes pasan) es suficiente para garantizar que cambiar `RETRIEVER_ENV=azure` no rompa nada, o se necesita un criterio de aceptación específico para el switch de proveedor? [Acceptance Criteria Quality, Spec §SC-004]
- [ ] CHK018 - ¿Existe un criterio de aceptación que valide que el mismo query produce resultados comparables en ChromaDB local y en Azure AI Search (calidad de resultados equivalente)? [Gap, Measurability]

---

## Dependencies & Assumptions

- [ ] CHK019 - ¿La asunción de LM Studio como servidor de embeddings está documentada como exclusiva para el entorno local, y se documenta explícitamente qué servidor de embeddings se usaría en Azure? [Assumption, Spec §Assumptions]
- [ ] CHK020 - ¿La spec registra como dependencia que Azure AI Search requiere un servicio de Azure aprovisionado (y credenciales), y que esto es una pre-condición para la fase cloud? [Dependency, Gap]
- [ ] CHK021 - ¿El plan menciona que `_search_azure()` en `agent/retriever.py` actualmente es un placeholder vacío y que su implementación futura es un requisito pendiente? [Dependency, Spec §Plan — constitution placeholder]

---

## Non-functional Requirements — Portabilidad

- [ ] CHK022 - ¿La spec define un requisito de portabilidad del esquema de datos: que los documentos indexados en ChromaDB puedan ser re-ingestados en Azure AI Search sin transformaciones adicionales? [Non-functional, Gap]
- [ ] CHK023 - ¿Están especificados los requisitos de seguridad para el switch a Azure AI Search (manejo de API keys, secrets) diferenciados de los del entorno local? [Non-functional, Gap]
- [ ] CHK024 - ¿El plan o la spec documentan si la latencia de `_search_azure()` puede diferir de `_search_local()` y si eso afecta el SC-002 (< 2 segundos por query)? [Non-functional, Consistency, Spec §SC-002]

---

## Ambiguities & Conflicts

- [ ] CHK025 - ¿La constitution define que el agente debe ser testeable localmente con MVP env (LM Studio + ChromaDB) antes de Azure — ¿está este requisito de gate reflejado en la spec de la feature? [Ambiguity, Gap — constitution §Governance vs spec]
- [ ] CHK026 - ¿El término "escalable" en el contexto del proyecto está definido con criterios medibles (ej: X documentos, Y usuarios concurrentes, Z latencia p95)? [Clarity, Ambiguity]
- [ ] CHK027 - ¿Existe un potencial conflicto entre FR-005 (embeddings via LM Studio, sin dependencias extra) y el escenario Azure donde LM Studio no estaría disponible? ¿Está resuelto en los requisitos? [Conflict, Spec §FR-005 vs escenario cloud]

---

## Notes

- CHK items marcados como **[Gap]** identifican requisitos ausentes en la spec/plan actual que deben agregarse antes de la fase cloud
- Los ítems más críticos para responder la pregunta del usuario: **CHK001, CHK004, CHK006, CHK019, CHK021, CHK027**
- El diseño SÍ tiene la flexibilidad arquitectural correcta (el switch `RETRIEVER_ENV` existe en constitution y plan), pero la spec **no documenta suficientemente** el path de migración a Azure ni los contratos que los proveedores alternativos deben cumplir
- Recomendación: antes de implementar la fase cloud, actualizar spec con un User Story 4 (P4) que cubra la migración y los contratos del proveedor
