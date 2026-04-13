# Data Model: Improve Main UI

El desarrollo para la modernización de la UI es estrictamente orientado a frontend, por lo que no se persistirán nuevas estructuras de base de datos ni modificaciones a tablas de backend. Los modelos descritos refieren a objetos de estado en Javascript que representarán la información visual en el sistema.

## Entidad: UI State

Representa el estado actual del chat dentro de la aplicación frontend.

**Campos principales**:
- `sessionId` (String): ID único de la sesión autogenerado (ej. `crypto.randomUUID()`).
- `currentUserRole` (String): "user", "helpdesk", o "admin". Define qué herramientas se muestran en el panel.
- `messages` (Array de MessageObj): El historial local de mensajes dibujados en el DOM.

## Entidad: MessageObj

Estructura de la burbuja resultante (Chat Bubble).

**Campos principales**:
- `id` (String): Identificador del mensaje.
- `role` (String): "user" o "assistant".
- `content` (String): Carga útil textual a mostrar o renderizar con parseo markdown.
- `action_executed` (String | null): Información de acción subyacente para renderizar un 'badge' visual.
