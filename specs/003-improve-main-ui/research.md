# Phase 0: Research & Architecture Decisions

## Tech Stack para Frontend

**Decision**: Reemplazar la aplicación actual de Streamlit y migrar hacia un frontend Vanilla HTML, CSS y JS puro.  
**Rationale**: El mandato dictamina explícitamente "Use HTML for structure and Javascript for logic. Use Vanilla CSS for styling... Use Rich Aesthetics". Streamlit es inherentemente restrictivo respecto al CSS personalizado y es particularmente difícil inyectar tipografías nuevas de fuentes externas y animaciones complejas (microanimaciones fluidas a 60 fps). Construyendo un frontend desde cero en una carpeta `frontend/` permite tener el control al 100% requerido por el Principio VI, garantizando que el diseño sea premium.  
**Alternatives considered**: 
- *Inyección de HTML/CSS en Streamlit* (`st.markdown(unsafe_allow_html=True)`). Se descartó porque se vuelve inmanejable para animaciones complejas de múltiples componentes y dificulta enormemente el "dynamic design" pedido.
- *React / Next.js / Vite*. Se descartó porque las directrices exigen "Vanilla CSS y JS" a menos que el usuario pida explícitamente una web app compleja. Para un Chatbot interactivo y un panel de herramientas de soporte, Vanilla JS y web sockets / APIs resultan más que suficientes y más rápidos.

## Tipografía y Tema

**Decision**: Utilizar 'Inter' (una tipografía moderna y de gran calidad visual recomendada) desde Google Fonts, y paletas de colores oscuras "dark mode" con tonos acentuados sutiles (variables CSS `var(--color-primary)`, etc). Uso de Glassmorphism. Animaciones a través de la propiedad `transition` de CSS.  
**Rationale**: Garantizar una experiencia visual de vanguardia y que la UI se perciba como de alta calidad (premium).  
**Alternatives considered**: Basarse en plantillas Bootstrap, que se descartó por lucir "genéricos y básicos".
