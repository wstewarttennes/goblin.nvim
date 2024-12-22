// Define backend URL based on environment
const isDev = window.electron?.env?.NODE_ENV === 'development';
const BACKEND_URL = isDev 
  ? 'ws://localhost:8011' 
  : 'wss://api.hellogobl.in';

class MessageHandler {
    constructor() {
        this.chatContainer = document.getElementById('chat-container');
        this.currentMessageDiv = null;
    }

    displayUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'user-message');
        messageDiv.textContent = message;
        this.chatContainer?.appendChild(messageDiv);
        this.scrollToBottom();
    }

    handleStreamingMessage(data) {
        if (!this.currentMessageDiv && !data.is_complete) {
            this.currentMessageDiv = document.createElement('div');
            this.currentMessageDiv.classList.add('message', 'assistant-message');
            this.chatContainer?.appendChild(this.currentMessageDiv);
        }

        if (!data.is_complete) {
            const formattedContent = this.formatText(data.message);
            if (this.currentMessageDiv) {
                this.currentMessageDiv.textContent += formattedContent;
            }
            this.scrollToBottom();
        } else if (this.currentMessageDiv) {
            this.formatCodeBlocks(this.currentMessageDiv);
            this.currentMessageDiv = null;
        }
    }

    formatText(text) {
        return text;
    }

    formatCodeBlocks(messageDiv) {
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
        if (this.chatContainer) {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }
    }

    displayErrorMessage(error) {
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('message', 'system-message');
        errorDiv.textContent = typeof error === 'string' ? error : error.message;
        this.chatContainer?.appendChild(errorDiv);
        this.scrollToBottom();
    }
}

class WebSocketManager {
    constructor(settingsManager) {
        this.settingsManager = settingsManager;  // Store reference to settings manager
        this.ws = null;
        this.messageHandler = new MessageHandler();
        this.connectWebSocket();
        this.setupInputHandlers();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connectWebSocket() {
        const wsUrl = `${BACKEND_URL}/ws/ears/chat/`;
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

        if (!messageInput || !sendButton) return;

        const sendMessage = () => {
            const message = messageInput.value.trim();
            // Get settings from the stored settings manager reference
            const currentProject = this.settingsManager.settings.project;
            const currentProvider = this.settingsManager.settings.provider;

            if (message && this.ws?.readyState === WebSocket.OPEN) {
                this.messageHandler.displayUserMessage(message);
                this.ws.send(JSON.stringify({
                    message: message,
                    provider: currentProvider || 'anthropic',  // Default to anthropic if not set
                    project: currentProject || 'goblin'  // Default to goblin if not set
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
        
        if ('webkitSpeechRecognition' in window) {
            this.setupSpeechRecognition();
        } else {
            console.warn('Speech recognition not supported');
            if (this.voiceButton) {
                this.voiceButton.style.display = 'none';
            }
        }
    }

    setupSpeechRecognition() {
        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
            this.isListening = true;
            this.voiceButton?.classList.add('active', 'speaking');
            if (this.voiceStatus) {
                this.voiceStatus.textContent = 'Listening...';
            }
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.voiceButton?.classList.remove('active', 'speaking');
            if (this.voiceStatus) {
                this.voiceStatus.textContent = 'Click to start';
            }
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (transcript.trim()) {
                const messageInput = document.getElementById('message-input');
                if (messageInput) {
                    messageInput.value = transcript;
                }
                
                if (this.wsManager.ws?.readyState === WebSocket.OPEN) {
                    this.wsManager.ws.send(JSON.stringify({
                        message: transcript,
                        provider: 'anthropic'
                    }));
                    if (messageInput) {
                        messageInput.value = '';
                    }
                }
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this.voiceButton?.classList.remove('active', 'speaking');
            if (this.voiceStatus) {
                this.voiceStatus.textContent = 'Error. Click to retry';
            }
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

class SettingsManager {
    constructor() {
        this.settings = this.loadSettings();
        this.setupEventListeners();
        this.applySettings();
        
        // Only send settings if electron is available
        if (window.electron) {
            window.electron.send('settings:updated', this.settings);
        } else {
            console.log('Electron API not available - running in web mode');
        }
    }


    loadSettings() {
        const savedSettings = JSON.parse(localStorage.getItem('goblinSettings') || '{}');
        return {
            theme: savedSettings.theme || 'light',
            fontSize: savedSettings.fontSize || 'medium',
            notifications: savedSettings.notifications !== undefined ? savedSettings.notifications : true,
            autoSave: savedSettings.autoSave !== undefined ? savedSettings.autoSave : true,
            screenshots: savedSettings.screenshots !== undefined ? savedSettings.screenshots : true,
            screenshotFrequency: savedSettings.screenshotFrequency || 5,
            project: savedSettings.project || 'goblin'
        };
    }

    setupEventListeners() {
        const settingsButton = document.querySelector('.settings-button');
        const settingsMenu = document.querySelector('.settings-menu');
        
        if (settingsButton && settingsMenu) {
            settingsButton.addEventListener('click', (e) => {
                e.stopPropagation();
                settingsMenu.classList.toggle('show');
            });

            document.addEventListener('click', (e) => {
                if (!settingsMenu.contains(e.target) && !settingsButton.contains(e.target)) {
                    settingsMenu.classList.remove('show');
                }
            });
        }

        const screenshotsToggle = document.getElementById('screenshots-toggle');
        const frequencyContainer = document.getElementById('screenshot-frequency-container');
        const frequencyInput = document.getElementById('screenshot-frequency');

        if (screenshotsToggle) {
            screenshotsToggle.checked = this.settings.screenshots;
            if (frequencyContainer) {
                frequencyContainer.style.display = this.settings.screenshots ? 'block' : 'none';
            }

            screenshotsToggle.addEventListener('change', (e) => {
                const isEnabled = e.target.checked;
                if (frequencyContainer) {
                    frequencyContainer.style.display = isEnabled ? 'block' : 'none';
                }
                this.updateSetting('screenshots', isEnabled);
            });
        }

        if (frequencyInput) {
            frequencyInput.value = this.settings.screenshotFrequency;
            frequencyInput.addEventListener('change', (e) => {
                const frequency = parseInt(e.target.value, 10);
                if (!isNaN(frequency) && frequency >= 1) {
                    this.updateSetting('screenshotFrequency', frequency);
                }
            });
        }

        // Setup individual setting listeners
        this.setupSettingListener('theme-select', 'theme');
        this.setupSettingListener('notifications-toggle', 'notifications', 'checked');
        this.setupSettingListener('font-size', 'fontSize', 'checked');
        this.setupSettingListener('auto-save-toggle', 'autoSave', 'checked');
        this.setupSettingListener('screenshots-toggle', 'screenshots', 'checked');
        this.setupSettingListener('screenshots-frequency', 'screenshotsFrequency', 'checked');
        this.setupSettingListener('project-select', 'project');
        this.setupSettingListener('provider-select', 'provider');
    }

    setupSettingListener(elementId, settingKey, property = 'value') {
        const element = document.getElementById(elementId);
        if (element) {
            element[property] = this.settings[settingKey];
            element.addEventListener('change', (e) => {
                this.updateSetting(settingKey, e.target[property]);
            });
        }
    }

   updateSetting(key, value) {
        this.settings[key] = value;
        localStorage.setItem('goblinSettings', JSON.stringify(this.settings));
        this.applySetting(key, value);

        // Notify main process about settings changes
        if (window.electron) {
            window.electron.send('settings:updated', this.settings);

            // Handle screenshot-specific updates
            if (key === 'screenshots' || key === 'screenshotFrequency') {
                if (this.settings.screenshots) {
                    window.electron.send('settings:updated', {
                        screenshots: true,
                        screenshotFrequency: this.settings.screenshotFrequency,
                        project: this.settings.project
                    });
                } else {
                    window.electron.send('settings:updated', {
                        screenshots: false
                    });
                }
            }

            if (key === 'project') {
                window.electron.send('project:changed', value);
            }
        }
    }

    applySetting(key, value) {
        switch (key) {
            case 'theme':
                document.documentElement.setAttribute('data-theme', value);
                break;
            case 'fontSize':
                document.body.style.fontSize = {
                    small: '14px',
                    medium: '16px',
                    large: '18px'
                }[value] || '16px';
                break;
        }
    }

    applySettings() {
        Object.entries(this.settings).forEach(([key, value]) => {
            this.applySetting(key, value);
        });
    }
}

class ChatApplication {
    constructor() {
        console.log('Initializing chat application...');
        // Create settings manager first
        this.settingsManager = new SettingsManager();
        // Pass settings manager to websocket manager
        this.wsManager = new WebSocketManager(this.settingsManager);
        // Pass websocket manager to voice manager
        this.voiceManager = new VoiceManager(this.wsManager);
        
        const voiceToggle = document.getElementById('voice-toggle');
        if (voiceToggle) {
            voiceToggle.addEventListener('click', () => {
                this.voiceManager.toggleListening();
            });
        }
    }
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.app = new ChatApplication();
    } catch (error) {
        console.error('Error initializing chat application:', error);
    }
});
