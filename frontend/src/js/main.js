/**
 * UI State Management
 */
const ROLE_LABELS = {
    user: "Usuario",
    helpdesk: "Mesa de ayuda",
    admin: "Administrador"
};

const UIState = {
    sessionId: crypto.randomUUID(),
    currentUserRole: 'user',
    theme: 'light',
    messages: []
};

/**
 * Update the user role in the state
 * @param {string} role 
 */
function setRole(role) {
    UIState.currentUserRole = role;
    syncRoleChip();
    console.log(`Role updated to: ${role}`);
}

/**
 * Get a human-readable label for a role
 * @param {string} role
 * @returns {string}
 */
function getRoleLabel(role) {
    return ROLE_LABELS[role] || role;
}

/**
 * Generate a unique ID for messages
 * @returns {string} pseudo-random ID
 */
function generateMessageId() {
    return Math.random().toString(36).substring(2, 9);
}

/**
 * Add a message to the UI state
 * @param {string} role 'user' or 'assistant'
 * @param {string} content Text of the message
 * @param {string|null} actionExecuted Any action executed by the assistant
 * @returns {Object} The message object
 */
function addMessageToState(role, content, actionExecuted = null) {
    const msg = {
        id: generateMessageId(),
        role: role,
        content: content,
        action_executed: actionExecuted,
        createdAt: new Date().toISOString()
    };
    UIState.messages.push(msg);
    return msg;
}

// Event Listeners for initialization
document.addEventListener("DOMContentLoaded", () => {
    initSidebarCollapse();
    initThemeSelector();

    // Initial role setup
    const roleSelect = document.getElementById("role-select");
    if (roleSelect) {
        roleSelect.addEventListener("change", (e) => {
            setRole(e.target.value);
            // Micro-animation effect
            roleSelect.style.transform = 'scale(0.98)';
            setTimeout(() => roleSelect.style.transform = 'scale(1)', 150);
        });
    }

    const themeToggle = document.getElementById("theme-toggle");
    if (themeToggle) {
        document.body.classList.toggle('disable-animations', !themeToggle.checked);
        themeToggle.addEventListener("change", (e) => {
            document.body.classList.toggle('disable-animations', !e.target.checked);
            syncVisualModeChip();
        });
    }

    const chatForm = document.getElementById("chat-form");
    if (chatForm) {
        chatForm.addEventListener("submit", handleChatSubmit);
    }

    document.addEventListener("click", (event) => {
        const promptButton = event.target.closest("[data-prompt]");
        if (!promptButton) return;

        const inputField = document.getElementById("chat-input");
        if (!inputField) return;

        inputField.value = promptButton.dataset.prompt || "";
        inputField.focus();
        if (typeof inputField.setSelectionRange === "function") {
            const endPosition = inputField.value.length;
            inputField.setSelectionRange(endPosition, endPosition);
        }
    });

    syncChromeState();
    renderMessages();
});

/**
 * Initialize theme selector and restore persisted preference
 */
function initThemeSelector() {
    const themeSelect = document.getElementById("theme-select");
    if (!themeSelect) return;

    const savedTheme = localStorage.getItem("ui-theme");
    const initialTheme = savedTheme === "dark" ? "dark" : "light";

    applyTheme(initialTheme);
    themeSelect.value = initialTheme;

    themeSelect.addEventListener("change", (e) => {
        applyTheme(e.target.value);
    });
}

/**
 * Apply selected theme to the document and persist preference
 * @param {string} theme
 */
function applyTheme(theme) {
    const resolvedTheme = theme === "dark" ? "dark" : "light";
    UIState.theme = resolvedTheme;
    document.body.setAttribute("data-theme", resolvedTheme);
    localStorage.setItem("ui-theme", resolvedTheme);
}

/**
 * Enable collapsing sidebar in desktop layouts
 */
function initSidebarCollapse() {
    const app = document.getElementById("app");
    const collapseButton = document.getElementById("sidebar-collapse-toggle");
    if (!app || !collapseButton) return;

    const setCollapsedState = (isCollapsed) => {
        app.classList.toggle("sidebar-collapsed", isCollapsed);
        collapseButton.setAttribute("aria-expanded", String(!isCollapsed));
        collapseButton.setAttribute("aria-label", isCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral");
    };

    collapseButton.addEventListener("click", () => {
        const isCollapsed = app.classList.toggle("sidebar-collapsed");
        collapseButton.setAttribute("aria-expanded", String(!isCollapsed));
        collapseButton.setAttribute("aria-label", isCollapsed ? "Expandir barra lateral" : "Colapsar barra lateral");
    });

    setCollapsedState(false);
}

/**
 * Synchronize header chips with current UI state
 */
function syncChromeState() {
    syncRoleChip();
    syncVisualModeChip();
}

/**
 * Update the role chip in the header
 */
function syncRoleChip() {
    const roleChip = document.getElementById("current-role-pill");
    if (roleChip) {
        roleChip.textContent = `Rol: ${getRoleLabel(UIState.currentUserRole)}`;
    }
}

/**
 * Update the visual mode chip in the header
 */
function syncVisualModeChip() {
    const visualChip = document.getElementById("visual-mode-pill");
    const animationsDisabled = document.body.classList.contains('disable-animations');

    if (visualChip) {
        visualChip.textContent = animationsDisabled ? "Animaciones pausadas" : "Animación activa";
        visualChip.classList.toggle("status-pill--muted", animationsDisabled);
    }
}

/**
 * Handle form submission
 * @param {Event} e 
 */
async function handleChatSubmit(e) {
    e.preventDefault();
    
    const inputField = document.getElementById("chat-input");
    const text = inputField.value.trim();
    
    if (!text) return;
    
    // Clear input
    inputField.value = "";
    
    // Add user message to state and UI
    addMessageToState("user", text);
    renderMessages();
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await ApiClient.askQuestion(text, UIState.sessionId, UIState.currentUserRole);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add assistant message
        const answer = response.answer || "No response";
        const action = response.action_executed || null;
        
        addMessageToState("assistant", answer, action);
        renderMessages();
        
    } catch (error) {
        removeTypingIndicator();
        addMessageToState("assistant", `Error: ${error.message}`);
        renderMessages();
    }

    inputField.focus();
}

/**
 * Render all messages from state to DOM
 */
function renderMessages() {
    const messagesArea = document.getElementById("messages-area");
    if (!messagesArea) return;
    
    messagesArea.innerHTML = "";
    messagesArea.classList.toggle("messages-area--empty", UIState.messages.length === 0);

    if (UIState.messages.length === 0) {
        renderEmptyState(messagesArea);
        return;
    }
    
    UIState.messages.forEach(msg => {
        const row = document.createElement("article");
        row.className = `message message-row ${msg.role}`;

        const avatar = document.createElement("div");
        avatar.className = `message-avatar ${msg.role}`;
        avatar.textContent = msg.role === "user" ? "TU" : "AI";

        const bubble = document.createElement("div");
        bubble.className = `message-bubble ${msg.role}`;

        const meta = document.createElement("div");
        meta.className = "message-meta";

        const roleLabel = document.createElement("span");
        roleLabel.className = "message-role";
        roleLabel.textContent = msg.role === "user" ? "Tú" : "Asistente";

        const timeLabel = document.createElement("time");
        timeLabel.className = "message-time";
        timeLabel.dateTime = msg.createdAt;
        timeLabel.textContent = formatMessageTime(msg.createdAt);

        meta.append(roleLabel, timeLabel);

        const content = document.createElement("div");
        content.className = "message-content";
        content.textContent = msg.content.trim();

        bubble.append(meta, content);

        if (msg.action_executed) {
            const footer = document.createElement("div");
            footer.className = "message-footer";

            const actionBadge = document.createElement("span");
            actionBadge.className = "action-badge";
            actionBadge.textContent = `Acción: ${msg.action_executed}`;

            footer.append(actionBadge);
            bubble.append(footer);
        }

        row.append(avatar, bubble);
        messagesArea.appendChild(row);
    });
    
    scrollToBottom();
}

/**
 * Render the initial empty state with quick prompts
 * @param {HTMLElement} messagesArea
 */
function renderEmptyState(messagesArea) {
    const welcomeState = document.createElement("section");
    welcomeState.className = "welcome-state";
    welcomeState.innerHTML = `
        <div class="welcome-state__icon" aria-hidden="true">✦</div>
        <p class="welcome-state__eyebrow">Inicio rápido</p>
        <h2>¿Qué necesitás resolver hoy?</h2>
        <p class="welcome-state__copy">Elegí un acceso rápido o escribí tu consulta. El panel lateral ajusta el contexto de respuesta según el rol.</p>
        <div class="prompt-grid">
            <button type="button" class="prompt-chip" data-prompt="No puedo iniciar sesión en Jira.">No puedo iniciar sesión</button>
            <button type="button" class="prompt-chip" data-prompt="Necesito buscar un ticket por número.">Buscar un ticket</button>
            <button type="button" class="prompt-chip" data-prompt="Necesito documentación sobre un proceso de soporte.">Ver documentación</button>
            <button type="button" class="prompt-chip" data-prompt="Restablecer contraseña de un usuario.">Restablecer contraseña</button>
        </div>
    `;

    messagesArea.appendChild(welcomeState);
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const messagesArea = document.getElementById("messages-area");
    if (!messagesArea) return;
    
    removeTypingIndicator(); // Ensure no duplicates
    
    const div = document.createElement("article");
    div.className = "typing-indicator";
    div.id = "typing-indicator";
    
    div.innerHTML = `
        <div class="message-avatar assistant">AI</div>
        <div class="typing-bubble">
            <span class="typing-label">Generando respuesta</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    
    messagesArea.appendChild(div);
    scrollToBottom();
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator() {
    const indicator = document.getElementById("typing-indicator");
    if (indicator) {
        indicator.parentElement.removeChild(indicator);
    }
}

/**
 * Scroll message area to bottom
 */
function scrollToBottom() {
    const messagesArea = document.getElementById("messages-area");
    if (messagesArea) {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }
}

/**
 * Format a message timestamp for display
 * @param {string} createdAt
 * @returns {string}
 */
function formatMessageTime(createdAt) {
    const date = new Date(createdAt);
    return date.toLocaleTimeString("es-ES", {
        hour: "2-digit",
        minute: "2-digit"
    });
}
