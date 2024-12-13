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
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connectWebSocket() {
        // Get the current hostname and port
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//localhost:8011/ws/chat/`;
        
        console.log('Attempting WebSocket connection to:', wsUrl);
        
        if (this.ws) {
            this.ws.close();
        }
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connection established');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket connection closed:', event);
                this.updateConnectionStatus(false);
                
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Reconnection attempt ${this.reconnectAttempts} of ${this.maxReconnectAttempts}`);
                    setTimeout(() => this.connectWebSocket(), 3000 * this.reconnectAttempts);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Received message:', data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error handling message:', error);
                    this.messageHandler.displayErrorMessage('Error processing message');
                }
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(isConnected) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (statusIndicator && statusText) {
            if (isConnected) {
                statusIndicator.classList.add('status-connected');
                statusText.textContent = 'Connected';
            } else {
                statusIndicator.classList.remove('status-connected');
                statusText.textContent = 'Disconnected';
            }
        }
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

}

class VoiceManager {
    constructor(wsManager) {
        this.wsManager = wsManager;
        this.recognition = null;
        this.isListening = false;
        this.voiceButton = document.getElementById('voice-toggle');
        this.voiceIcon = document.getElementById('voice-icon');
        this.voiceStatus = document.getElementById('voice-status');
        
        // Check if browser supports speech recognition
        if ('webkitSpeechRecognition' in window) {
            this.setupSpeechRecognition();
        } else {
            console.warn('Speech recognition not supported');
            this.voiceButton.style.display = 'none';
        }
    }

    setupSpeechRecognition() {
        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
            this.isListening = true;
            this.voiceButton.classList.add('active', 'speaking');
            this.voiceStatus.textContent = 'Listening...';
            console.log('Speech recognition started');
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.voiceButton.classList.remove('active', 'speaking');
            this.voiceStatus.textContent = 'Click to start';
            console.log('Speech recognition ended');
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('Recognized:', transcript);
            if (transcript.trim()) {
                // Update input field with transcript
                const messageInput = document.getElementById('message-input');
                messageInput.value = transcript;
                
                // Optionally, send immediately
                if (this.wsManager.ws?.readyState === WebSocket.OPEN) {
                    this.wsManager.ws.send(JSON.stringify({
                        message: transcript,
                        provider: 'anthropic'
                    }));
                    messageInput.value = ''; // Clear after sending
                }
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.voiceButton.classList.remove('active', 'speaking');
            this.voiceStatus.textContent = 'Error. Click to retry';
        };
    }

    toggleListening() {
        if (!this.recognition) {
            console.warn('Speech recognition not initialized');
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }
}

class ChatApplication {
    constructor() {
        // Initialize managers
        this.themeManager = new ThemeManager();
        this.wsManager = new WebSocketManager();
        this.voiceManager = new VoiceManager(this.wsManager);
        
        // Set up voice control event listener
        const voiceToggle = document.getElementById('voice-toggle');
        if (voiceToggle) {
            voiceToggle.addEventListener('click', () => {
                this.voiceManager.toggleListening();
            });
        }
    }
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing chat application...');
    // new WebSocketManager();
    new ChatApplication()
});
