# Research & Architectural Decisions

## 1. Agente Orquestador (LangGraph vs genérico)
- **Decision:** Uso de LangGraph 0.3+ como motor de estado del agente.
- **Rationale:** Permite un pipeline de estado estrictamente tipado y predecible que soporta ejecución concurrente (fundamental para el pipeline de RAG multi-fuente simultáneo) y ruteos condicionales.
- **Alternatives considered:** ReAct genérico via LangChain o implementaciones condicionales duras. Descartados debido a que fallan en el Fan-out de fuentes en paralelo y dificultan el rastreo visual.

## 2. Ingesta de SharePoint
- **Decision:** Procesar manuales como archivos `.html` a través del ETL de mock SharePoint, extrayendo texto vía BeautifulSoup u otro analizador semántico HTML.
- **Rationale:** La política de desarrollo constitucional demanda el consumo estricto de `.html` para reflejar con mayor precisión las jerarquías asiladas que entrega SharePoint originalmente, eliminando la dependencia sobre archivos `.md` pre-formateados. Configurar el parseador en esta etapa valida la madurez del producto final.
- **Alternatives considered:** Parsing nativo sobre Markdown. Descartado por requerimiento explícito del usuario y por constituir una simplificación de la realidad.

## 3. Retriever Agnóstico
- **Decision:** Definir un método abstracto de indexación / búsqueda polimórfico manipulado únicamente por la variable global `RETRIEVER_ENV` (cuyos valores válidos son "local" y "azure").
- **Rationale:** Separación de dominios. El Grafo (Graph runtime) no debe saber ni de SQLite, ni de LocalVectorStore, ni de Azure AI Search. Esto facilita probar el "happy path" algorítmico y luego delegar la resolución e integración a operaciones DevOps sin alterar base codebase.
- **Alternatives considered:** Múltiples clases de retrievers atadas al framework instanciadas estáticamente. Demasiado acoplamiento.

## 4. Clasificación de Tareas e Intenciones
- **Decision:** El nodo `classify_intent` usa el LLM local vía `with_structured_output(IntentClassification)` donde `IntentClassification` es un modelo Pydantic v2 con un campo `intent: Literal["query", "jira_search", "action"]`. Si el LLM no está disponible, cae a un router determinista basado en keywords como fallback.
- **Rationale:** El LLM maneja cualquier formulación del usuario (formal, coloquial, con errores) sin depender de palabras clave anticipadas. El `structured_output` con Pydantic fuerza el schema al modelo, eliminando alucinaciones en el valor de `intent` y haciendo el resultado directamente consumible por el grafo sin parsing adicional. El fallback garantiza disponibilidad en entornos sin LLM (CI, tests unitarios sin servidor).
- **Alternatives considered:** 
  - *Regex/keywords puro (implementación inicial)*: Frágil ante variaciones de lenguaje natural. Descartado para producción.
  - *ReAct loop con tool calling nativo*: Incompatible con el fan-out paralelo explícito del grafo — el LLM ejecutaría las 3 fuentes RAG secuencialmente. Descartado.
- **Tradeoff:** Agrega ~0.5-1s de latencia al primer nodo del grafo. Aceptable dado el objetivo de <8s end-to-end (SC-002).
