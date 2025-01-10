const { BrowserWindow } = require('electron');

class MainMessageHandler {
    constructor() {
        this.mainWindow = null;
    }

    setMainWindow(window) {
        this.mainWindow = window;
    }

    handleStreamingMessage(data) {
        if (this.mainWindow && !this.mainWindow.isDestroyed()) {
            // Format the message to match the chat interface expectations
            const messageData = {
                type: 'chat_message_chunk',
                message: data.message,
                is_complete: data.is_complete,
                source: 'screenshot'  // Add a source to identify screenshot messages
            };
            
            this.mainWindow.webContents.send('screenshot:analysis', messageData);
        }
    }

    displayErrorMessage(error) {
        if (this.mainWindow && !this.mainWindow.isDestroyed()) {
            this.mainWindow.webContents.send('screenshot:error', {
                type: 'error',
                message: typeof error === 'string' ? error : error.message,
                source: 'screenshot'
            });
        }
    }
}

module.exports = MainMessageHandler;
