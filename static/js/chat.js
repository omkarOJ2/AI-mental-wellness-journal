
// ===================================
// MODERN PROFESSIONAL CHATBOT
// Industry Standard Implementation
// ===================================

let currentChatEntryId = null;
let chatHistory = [];
let isChatPanelOpen = false;

// Toggle chat panel with modern animations
function toggleChatPanel() {
    const panel = document.getElementById('chatPanel');
    const button = document.querySelector('.chat-widget-button');
    isChatPanelOpen = !isChatPanelOpen;

    if (isChatPanelOpen) {
        panel.classList.add('open');
        button.classList.add('open');
        hideBadge();

        // Show welcome screen if first time (no auto-messages)
        if (chatHistory.length === 0) {
            showWelcomeScreen();
        }
    } else {
        panel.classList.remove('open');
        button.classList.remove('open');
    }
}

// Show welcome screen
function showWelcomeScreen() {
    const messagesDiv = document.getElementById("chatMessages");
    messagesDiv.innerHTML = `
        <div class="chat-welcome">
            <div class="chat-welcome-icon">🧠</div>
            <h4>Your Personal Wellness Assistant</h4>
            <p>I'm here to help you with journaling tips, progress tracking, and mental wellness guidance. Ask me anything!</p>
        </div>
    `;

    // Show helpful starting prompts
    updateSuggestedPrompts([
        "Hi, how can you help me?",
        "Give me journaling tips",
        "Show my progress",
        "What should I write about?"
    ]);
}

// Send chat message with modern UX
async function sendChatMessage() {
    const input = document.getElementById("chatInput");
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addUserMessage(message);
    input.value = "";

    // Add to history
    chatHistory.push({ role: "user", content: message });

    // Show typing indicator
    showTypingIndicator();

    try {
        // Get most recent entry if no specific entry selected
        if (!currentChatEntryId) {
            const entries = await fetch('/api/journal/entries').then(r => r.json());
            if (entries.entries && entries.entries.length > 0) {
                currentChatEntryId = entries.entries[0].id;
            }
        }

        const response = await fetch("/api/chat/reflect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                entry_id: currentChatEntryId,
                message: message,
                history: chatHistory
            })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator();

        if (data.reply) {
            addAIMessage(data.reply);
            chatHistory.push({ role: "assistant", content: data.reply });

            // Update suggested prompts
            if (data.suggested_prompts && data.suggested_prompts.length > 0) {
                updateSuggestedPrompts(data.suggested_prompts);
            }
        }
    } catch (error) {
        removeTypingIndicator();
        addAIMessage("I'm having trouble connecting right now. Please try again in a moment.");
        console.error("Chat error:", error);
    }
}

// Use suggested prompt
function useSuggestedPrompt(prompt) {
    document.getElementById("chatInput").value = prompt;
    document.getElementById("suggestedPrompts").innerHTML = '';
    sendChatMessage();
}

// Add user message with timestamp
function addUserMessage(text) {
    const messagesDiv = document.getElementById("chatMessages");

    // Remove welcome screen if present
    const welcome = messagesDiv.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement("div");
    messageDiv.className = "chat-message user";
    messageDiv.innerHTML = `
        <div class="chat-message-avatar">👤</div>
        <div class="chat-message-content">
            <div class="chat-message-bubble">${escapeHtml(text)}</div>
            <div class="chat-message-time">${getCurrentTime()}</div>
        </div>
    `;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Add AI message with timestamp
function addAIMessage(text) {
    const messagesDiv = document.getElementById("chatMessages");

    // Remove welcome screen if present
    const welcome = messagesDiv.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement("div");
    messageDiv.className = "chat-message ai";
    messageDiv.innerHTML = `
        <div class="chat-message-avatar">🤖</div>
        <div class="chat-message-content">
            <div class="chat-message-bubble">${escapeHtml(text)}</div>
            <div class="chat-message-time">${getCurrentTime()}</div>
        </div>
    `;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    const messagesDiv = document.getElementById("chatMessages");
    const typingDiv = document.createElement("div");
    typingDiv.id = "typingIndicator";
    typingDiv.className = "chat-message ai";
    typingDiv.innerHTML = `
        <div class="chat-message-avatar">🤖</div>
        <div class="chat-message-content">
            <div class="chat-message-bubble chat-typing-indicator">
                <div class="chat-typing-dot"></div>
                <div class="chat-typing-dot"></div>
                <div class="chat-typing-dot"></div>
            </div>
        </div>
    `;
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.getElementById("typingIndicator");
    if (indicator) indicator.remove();
}

// Update suggested prompts
function updateSuggestedPrompts(prompts) {
    const promptsDiv = document.getElementById("suggestedPrompts");
    promptsDiv.innerHTML = prompts.map(prompt => `
        <button class="chat-prompt-btn" onclick="useSuggestedPrompt(\`${escapeHtml(prompt)}\`)">
            ${escapeHtml(prompt)}
        </button>
    `).join("");
}

// Get current time formatted
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// Hide badge
function hideBadge() {
    const badge = document.getElementById('chatBadge');
    if (badge) badge.style.display = 'none';
}

// Show welcome notification when page loads
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(() => {
        const badge = document.getElementById('chatBadge');
        if (badge && chatHistory.length === 0) {
            badge.style.display = 'flex';
        }
    }, 3000);
});
