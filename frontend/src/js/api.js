const API_URL = "http://localhost:8000/ask";

/**
 * Handles communication with the FastAPI backend
 */
class ApiClient {
    /**
     * Send a question to the backend to get a response
     * @param {string} question - The user's prompt
     * @param {string} sessionId - Current session UUID
     * @param {string} role - The chosen role (user, helpdesk, admin)
     * @returns {Promise<Object>} - The API response parsed as JSON
     */
    static async askQuestion(question, sessionId, role) {
        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question,
                    session_id: sessionId,
                    role: role
                })
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Connection failed: ", error);
            throw error;
        }
    }
}

// Expose to global scope for the main logic
window.ApiClient = ApiClient;
