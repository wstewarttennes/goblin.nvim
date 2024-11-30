// renderer.js
class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('theme-toggle');
        this.themeIcon = document.getElementById('theme-icon');
        this.themeText = document.getElementById('theme-text');
        
        // Initialize theme from localStorage or default to dark
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.setTheme(savedTheme);
        
        // Bind event listener
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.updateThemeButton(theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    updateThemeButton(theme) {
        if (theme === 'dark') {
            this.themeIcon.textContent = '🌜';
            this.themeText.textContent = 'Light Mode';
        } else {
            this.themeIcon.textContent = '🌞';
            this.themeText.textContent = 'Dark Mode';
        }
    }
}


class MessageHandler {
    constructor() {
        this.chatContainer = document.getElementById('chat-container');
        this.currentMessageDiv = null;
    }

    displayUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'user-message');
        messageDiv.textContent = message;
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    handleStreamingMessage(data) {
        if (!this.currentMessageDiv && !data.is_complete) {
            this.currentMessageDiv = document.createElement('div');
            this.currentMessageDiv.classList.add('message', 'assistant-message');
            this.chatContainer.appendChild(this.currentMessageDiv);
        }

        if (!data.is_complete) {
            const formattedContent = this.formatText(data.message);
            this.currentMessageDiv.textContent += formattedContent;
            this.scrollToBottom();
        } else {
            if (this.currentMessageDiv) {
                this.formatCodeBlocks(this.currentMessageDiv);
                this.currentMessageDiv = null;
            }
        }
    }

    formatText(text) {
        // Simple text formatting - you can expand this as needed
        return text;
    }

    formatCodeBlocks(messageDiv) {
        // Simple code block detection and formatting
        const text = messageDiv.textContent;
        if (text.includes('```')) {
            const formattedHtml = text.replace(
                /```([\s\S]*?)```/g,
                (match, code) => `<pre><code>${this.escapeHtml(code.trim())}</code></pre>`
            );
            messageDiv.innerHTML = formattedHtml;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    displayErrorMessage(error) {
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('message', 'system-message');
        errorDiv.textContent = typeof error === 'string' ? error : error.message;
        this.chatContainer.appendChild(errorDiv);
        this.scrollToBottom();
    }
}

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.messageHandler = new MessageHandler();
        this.connectWebSocket();
        this.setupInputHandlers();
    }

    connectWebSocket() {
        const wsUrl = 'ws://localhost:8008/ws/chat/';
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            // Attempt to reconnect after a delay
            setTimeout(() => this.connectWebSocket(), 3000);
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error handling message:', error);
                this.messageHandler.displayErrorMessage('Error processing message');
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleMessage(data) {
        console.log('Received message:', data);
        
        switch (data.type) {
            case 'chat_message_chunk':
                this.messageHandler.handleStreamingMessage(data);
                break;
            case 'error':
                this.messageHandler.displayErrorMessage(data.message);
                break;
            case 'connection_status':
                this.updateConnectionStatus(data.status === 'connected');
                break;
        }
    }

    setupInputHandlers() {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');

        const sendMessage = () => {
            const message = messageInput.value.trim();
            if (message && this.ws?.readyState === WebSocket.OPEN) {
                this.messageHandler.displayUserMessage(message);
                this.ws.send(JSON.stringify({
                    message: message,
                    provider: 'anthropic'
                }));
                messageInput.value = '';
            }
        };

        sendButton.onclick = sendMessage;
        messageInput.onkeypress = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        };
    }

    updateConnectionStatus(isConnected) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (isConnected) {
            statusIndicator.classList.add('status-connected');
            statusText.textContent = 'Connected';
        } else {
            statusIndicator.classList.remove('status-connected');
            statusText.textContent = 'Disconnected';
        }
    }
}

class ChatApplication {
    constructor() {
        // Initialize both managers
        this.themeManager = new ThemeManager();
        this.wsManager = new WebSocketManager();
    }
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing chat application...');
    // new WebSocketManager();
    new ChatApplication()
});
