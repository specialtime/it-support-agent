/**
 * IT Command Center — Main UI Logic
 * Handles state, rendering, animations and API communication.
 */

/* =========================================================
   STATE
   ========================================================= */
const ROLE_LABELS = {
    user:     "Usuario Final",
    helpdesk: "Mesa de Ayuda",
    admin:    "Administrador"
};

const UIState = {
    sessionId:       crypto.randomUUID(),
    currentUserRole: "user",
    theme:           "dark",
    animationsOn:    true,
    messages:        []
};

/* =========================================================
   UTILITIES
   ========================================================= */
function generateMessageId() {
    return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

function formatTime(isoString) {
    return new Date(isoString).toLocaleTimeString("es-ES", {
        hour:   "2-digit",
        minute: "2-digit"
    });
}

function getRoleLabel(role) {
    return ROLE_LABELS[role] || role;
}

/* =========================================================
   STATE MUTATIONS
   ========================================================= */
function setRole(role) {
    UIState.currentUserRole = role;
    syncRolePill();
}

function addMessage(role, content, actionExecuted = null) {
    const msg = {
        id:              generateMessageId(),
        role,
        content,
        action_executed: actionExecuted,
        createdAt:       new Date().toISOString()
    };
    UIState.messages.push(msg);
    return msg;
}

/* =========================================================
   INITIALIZATION
   ========================================================= */
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSidebar();
    initControls();
    syncPills();
    renderMessages();
});

function initTheme() {
    const themeSelect = document.getElementById("theme-select");
    const saved = localStorage.getItem("it-cmd-theme") || "dark";
    applyTheme(saved);
    if (themeSelect) themeSelect.value = saved;
}

function applyTheme(theme) {
    const resolved = theme === "light" ? "light" : "dark";
    UIState.theme = resolved;
    document.documentElement.setAttribute("data-theme", resolved);
    document.body.setAttribute("data-theme", resolved);
    localStorage.setItem("it-cmd-theme", resolved);
}

function initControls() {
    // Role selector
    const roleSelect = document.getElementById("role-select");
    if (roleSelect) {
        roleSelect.addEventListener("change", e => {
            setRole(e.target.value);
            flashBorder(roleSelect);
        });
    }

    // Theme selector
    const themeSelect = document.getElementById("theme-select");
    if (themeSelect) {
        themeSelect.addEventListener("change", e => applyTheme(e.target.value));
    }

    // Animations toggle
    const animToggle = document.getElementById("theme-toggle");
    if (animToggle) {
        animToggle.addEventListener("change", e => {
            UIState.animationsOn = e.target.checked;
            document.body.classList.toggle("disable-animations", !e.target.checked);
            syncVisualPill();
        });
    }

    // Chat form
    const chatForm = document.getElementById("chat-form");
    if (chatForm) chatForm.addEventListener("submit", handleChatSubmit);

    // Quick prompt chips (delegated)
    document.addEventListener("click", e => {
        const chip = e.target.closest("[data-prompt]");
        if (!chip) return;
        const input = document.getElementById("chat-input");
        if (!input) return;
        input.value = chip.dataset.prompt || "";
        input.focus();
        const end = input.value.length;
        input.setSelectionRange(end, end);
        chip.style.transform = "scale(0.98)";
        setTimeout(() => { chip.style.transform = ""; }, 120);
    });
}

function initSidebar() {
    const app      = document.getElementById("app");
    const toggle   = document.getElementById("sidebar-collapse-toggle");
    if (!app || !toggle) return;

    toggle.addEventListener("click", () => {
        const collapsed = app.classList.toggle("sidebar-collapsed");
        toggle.setAttribute("aria-expanded", String(!collapsed));
        toggle.setAttribute("aria-label", collapsed ? "Expandir panel lateral" : "Colapsar panel lateral");
    });
}

/* =========================================================
   UI SYNC
   ========================================================= */
function syncPills() {
    syncRolePill();
    syncVisualPill();
}

function syncRolePill() {
    const pill = document.getElementById("current-role-pill");
    if (pill) pill.textContent = `Rol: ${getRoleLabel(UIState.currentUserRole)}`;
}

function syncVisualPill() {
    const pill = document.getElementById("visual-mode-pill");
    if (!pill) return;
    const off = document.body.classList.contains("disable-animations");
    pill.textContent = off ? "Animaciones pausadas" : "Animación activa";
}

function syncConnectionStatus(status) {
    const pill = document.getElementById("connection-status-pill");
    if (!pill) return;
    const map = {
        online:    { text: "En línea",      cls: "status-pill--live"    },
        thinking:  { text: "Procesando...", cls: "status-pill--thinking" },
        error:     { text: "Error",         cls: "status-pill--error"   }
    };
    const cfg = map[status] || map.online;
    pill.className = `status-pill status-pill--live`;
    if (status !== "online") pill.classList.remove("status-pill--live");
    pill.textContent = cfg.text;
}

/* =========================================================
   MICRO-INTERACTIONS
   ========================================================= */
function flashBorder(el) {
    el.style.borderColor = "var(--pantone-219c)";
    el.style.boxShadow   = "0 0 0 3px var(--pantone-219c-soft)";
    setTimeout(() => {
        el.style.borderColor = "";
        el.style.boxShadow   = "";
    }, 400);
}

/* =========================================================
   CHAT SUBMIT
   ========================================================= */
async function handleChatSubmit(e) {
    e.preventDefault();

    const input = document.getElementById("chat-input");
    const text  = input?.value.trim();
    if (!text) return;

    input.value = "";
    addMessage("user", text);
    renderMessages();
    showTypingIndicator();
    syncConnectionStatus("thinking");

    const sendBtn = document.getElementById("send-button");
    if (sendBtn) sendBtn.disabled = true;

    try {
        const res    = await ApiClient.askQuestion(text, UIState.sessionId, UIState.currentUserRole);
        removeTypingIndicator();
        syncConnectionStatus("online");

        const answer = res.answer        || "No se recibió respuesta.";
        const action = res.action_executed || null;
        addMessage("assistant", answer, action);
        renderMessages();

    } catch (err) {
        removeTypingIndicator();
        syncConnectionStatus("error");
        addMessage("assistant", `⚠ Error de sistema: ${err.message}`);
        renderMessages();

    } finally {
        if (sendBtn) sendBtn.disabled = false;
        input?.focus();
    }
}

/* =========================================================
   RENDERING
   ========================================================= */
function renderMessages() {
    const area = document.getElementById("messages-area");
    if (!area) return;

    area.innerHTML = "";
    area.classList.toggle("messages-area--empty", UIState.messages.length === 0);

    if (UIState.messages.length === 0) {
        renderWelcome(area);
        return;
    }

    UIState.messages.forEach((msg, index) => {
        const row = buildMessageRow(msg);
        area.appendChild(row);
        // Staggered entrance
        if (UIState.animationsOn) {
            const delay = Math.min(index * 40, 200);
            row.style.animationDelay = `${delay}ms`;
        }
    });

    scrollToBottom();
}

function buildMessageRow(msg) {
    const row = document.createElement("article");
    row.className = `message message-row ${msg.role}`;
    row.setAttribute("data-message-id", msg.id);

    // Avatar
    const avatar = document.createElement("div");
    avatar.className = `message-avatar ${msg.role}`;
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = msg.role === "user" ? "TÚ" : "AI";

    // Bubble
    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${msg.role}`;

    // Meta line
    const meta = document.createElement("div");
    meta.className = "message-meta";

    const role = document.createElement("span");
    role.className = "message-role";
    role.textContent = msg.role === "user" ? "Tú" : "Asistente";

    const time = document.createElement("time");
    time.className = "message-time";
    time.dateTime  = msg.createdAt;
    time.textContent = formatTime(msg.createdAt);

    meta.append(role, time);

    // Content
    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = msg.content.trim();

    bubble.append(meta, content);

    // Action badge
    if (msg.action_executed) {
        const footer = document.createElement("div");
        footer.className = "message-footer";

        const badge = document.createElement("span");
        badge.className = "action-badge";
        badge.textContent = `⚡ ${msg.action_executed}`;

        footer.append(badge);
        bubble.append(footer);
    }

    row.append(avatar, bubble);
    return row;
}

function renderWelcome(area) {
    const welcome = document.createElement("section");
    welcome.className = "welcome-state";
    welcome.setAttribute("aria-label", "Pantalla de bienvenida");
    welcome.innerHTML = `
        <div class="welcome-state__icon" aria-hidden="true">✦</div>
        <p class="welcome-state__eyebrow">Inicio de sesión</p>
        <h2>¿Qué necesitás resolver?</h2>
        <p class="welcome-state__copy">
            Analizando solicitudes en tiempo real. Selecciona un acceso rápido o describe tu duda.
        </p>
        <div class="prompt-grid" role="list">
            <button type="button" class="prompt-chip" role="listitem"
                data-prompt="No puedo iniciar sesión en el sistema."
                aria-label="Consulta rápida: No puedo iniciar sesión">
                No puedo iniciar sesión
            </button>
            <button type="button" class="prompt-chip" role="listitem"
                data-prompt="Necesito el estado del ticket #1024."
                aria-label="Consulta rápida: Buscar estado de un ticket">
                Estado de ticket
            </button>
            <button type="button" class="prompt-chip" role="listitem"
                data-prompt="Necesito documentación sobre el proceso de onboarding."
                aria-label="Consulta rápida: Ver documentación técnica">
                Documentación técnica
            </button>
            <button type="button" class="prompt-chip" role="listitem"
                data-prompt="Necesito restablecer la contraseña de un usuario."
                aria-label="Consulta rápida: Restablecer contraseña">
                Restablecer contraseña
            </button>
        </div>
    `;
    area.appendChild(welcome);
}

/* =========================================================
   TYPING INDICATOR
   ========================================================= */
function showTypingIndicator() {
    const area = document.getElementById("messages-area");
    if (!area) return;
    removeTypingIndicator();

    const indicator = document.createElement("article");
    indicator.id = "typing-indicator";
    indicator.className = "typing-indicator";
    indicator.setAttribute("aria-label", "El asistente está generando una respuesta");
    indicator.innerHTML = `
        <div class="message-avatar assistant" aria-hidden="true">AI</div>
        <div class="typing-bubble">
            <span class="typing-label">Generando respuesta</span>
            <div class="typing-dots" aria-hidden="true">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;

    area.appendChild(indicator);
    scrollToBottom();
}

function removeTypingIndicator() {
    document.getElementById("typing-indicator")?.remove();
}

/* =========================================================
   SCROLL
   ========================================================= */
function scrollToBottom() {
    const area = document.getElementById("messages-area");
    if (area) {
        area.scrollTo({ top: area.scrollHeight, behavior: "smooth" });
    }
}
