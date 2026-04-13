# Quickstart: Local Vector Database

**Feature**: `002-local-vector-db`

## Prerequisitos

### 1. LM Studio (servidor de embeddings)

1. Abrir **LM Studio**
2. En la pestaña **My Models**, buscar y descargar: `nomic-embed-text-v1.5` (GGUF Q4_K_M, ~274 MB)
   - Alternativa más liviana: `bge-small-en-v1.5`
3. Ir a la pestaña **Local Server** (ícono `</>`)
4. Seleccionar el modelo descargado
5. Hacer click en **Start Server** → el servidor quedará en `http://localhost:1234`

### 2. Variables de entorno

Agregar al archivo `.env` del proyecto:

```env
# LM Studio — Embedding server
LMS_BASE_URL=http://localhost:1234/v1
LMS_EMBED_MODEL=nomic-embed-text-v1.5
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

---

## Ejecutar la ingesta

```powershell
# Desde la raíz del proyecto, con el venv activado y LM Studio corriendo:
python -m etl.ingest
```

Salida esperada:
```
[sharepoint]  12 documentos ingestados ✓
[jira_onprem] 87 documentos ingestados ✓
[jira_cloud]  143 documentos ingestados ✓
Ingesta completada. Índice en: data/chroma_db/
```

> **Nota**: Solo es necesario re-ejecutar cuando cambian los datos de origen. El índice persiste en disco.

---

## Verificar que funciona

```python
# test rápido desde Python REPL
from agent.retriever import search
results = search("vpn no conecta contraseña", source_type="jira_cloud", top=3)
for r in results:
    print(r["title"], "|", r["source"])
```

---

## Flujo completo de desarrollo

```
1. LM Studio → Start Server (nomic-embed-text-v1.5)
2. python -m etl.ingest           ← indexa datos
3. python -m uvicorn api.main:app --reload  ← levanta el agente
```

---

## Troubleshooting

| Problema | Causa probable | Solución |
|---|---|---|
| `ConnectionRefusedError` en ingesta | LM Studio no está corriendo | Iniciar LM Studio y hacer Start Server |
| `Collection not found` al consultar | Ingesta no ejecutada aún | `python -m etl.ingest` |
| Embeddings incorrectos / error de dimensión | Modelo diferente al usado en ingesta | Limpiar `data/chroma_db/` y re-ingestar con el modelo correcto |
| `data/chroma_db/` en git | `.gitignore` no configurado | Agregar `data/chroma_db/` al `.gitignore` |
