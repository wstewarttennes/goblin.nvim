export class MessageHandler {
    constructor() {
        this.chatContainer = document.getElementById('chat-container');
        this.currentMessageDiv = null;
        this.setupScreenshotHandlers();
    }

    setupScreenshotHandlers() {
        if (window.electron) {
            window.electron.onScreenshotAnalysis((data) => {
                this.handleStreamingMessage(data);
            });
            
            window.electron.onScreenshotError((data) => {
                this.displayErrorMessage(data.message);
            });
        }
    }

    handleStreamingMessage(data) {
        // Create new message div if needed
        if (!this.currentMessageDiv && !data.is_complete) {
            this.currentMessageDiv = document.createElement('div');
            this.currentMessageDiv.classList.add('message', 'assistant-message');
            if (data.source === 'screenshot') {
                this.currentMessageDiv.classList.add('screenshot-message');
            }
            this.chatContainer?.appendChild(this.currentMessageDiv);
        }

        // Update message content
        if (!data.is_complete && data.message) {
            const formattedContent = this.formatText(data.message);
            if (this.currentMessageDiv) {
                // Use = for screenshots, += for normal streaming
                if (data.source === 'screenshot') {
                    this.currentMessageDiv.textContent = formattedContent;
                } else {
                    this.currentMessageDiv.textContent += formattedContent;
                }
            }
            this.scrollToBottom();
        } else if (data.is_complete && this.currentMessageDiv) {
            this.formatCodeBlocks(this.currentMessageDiv);
            this.currentMessageDiv = null;
        }
    }

    displayUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'user-message');
        messageDiv.textContent = message;
        this.chatContainer?.appendChild(messageDiv);
        this.scrollToBottom();
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
