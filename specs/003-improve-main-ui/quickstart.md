# Quickstart: Mejoras a la UI Principal (Frontend)

Este documento esboza cómo arrancar la aplicación nativa luego de los cambios realizados durante la Fase de Implementación.

**Requisitos Previos**
- Backend (FastAPI + LangGraph) corriendo en `http://localhost:8000`.

**Ejecución de la Interfaz Web:**
Dado que la UI se sustituyó por Vanilla HTML/JS, ya no se utiliza `streamlit run app.py`.
En su lugar, el acceso al frontend se realiza simplemente abriendo el archivo central HTML desde un navegador, o (recomendado) mediante un entorno de desarrollo local rápido:

```bash
cd frontend
# Utilizando Python, que ya está instalado como el entorno nativo
python -m http.server 8080
```
Luego visitar: `http://localhost:8080`

La aplicación cargará automáticamente los hooks CSS y JS modernos para interactuar fluidamente con el modelo de soporte IT y mostrar la interfaz de calidad requerida.
