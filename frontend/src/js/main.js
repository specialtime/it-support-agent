/**
 * UI State Management
 */
const UIState = {
    sessionId: crypto.randomUUID(),
    currentUserRole: 'user',
    messages: []
};

/**
 * Update the user role in the state
 * @param {string} role 
 */
function setRole(role) {
    UIState.currentUserRole = role;
    console.log(`Role updated to: ${role}`);
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
        action_executed: actionExecuted
    };
    UIState.messages.push(msg);
    return msg;
}

// Event Listeners for initialization
document.addEventListener("DOMContentLoaded", () => {
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
        themeToggle.addEventListener("change", (e) => {
            if (e.target.checked) {
                document.body.classList.remove('disable-animations');
            } else {
                document.body.classList.add('disable-animations');
            }
        });
    }

    const chatForm = document.getElementById("chat-form");
    if (chatForm) {
        chatForm.addEventListener("submit", handleChatSubmit);
    }
});

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
}

/**
 * Render all messages from state to DOM
 */
function renderMessages() {
    const messagesArea = document.getElementById("messages-area");
    if (!messagesArea) return;
    
    messagesArea.innerHTML = "";
    
    UIState.messages.forEach(msg => {
        const div = document.createElement("div");
        div.className = `message ${msg.role}`;
        
        let contentHtml = escapeHtml(msg.content.trim()).replace(/\n/g, '<br>');
        
        if (msg.action_executed) {
            contentHtml += `<br><span class="action-badge">Action: ${escapeHtml(msg.action_executed)}</span>`;
        }
        
        div.innerHTML = contentHtml;
        messagesArea.appendChild(div);
    });
    
    scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const messagesArea = document.getElementById("messages-area");
    if (!messagesArea) return;
    
    removeTypingIndicator(); // Ensure no duplicates
    
    const div = document.createElement("div");
    div.className = "typing-indicator";
    div.id = "typing-indicator";
    
    div.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
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
 * Simple HTML escape
 */
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
