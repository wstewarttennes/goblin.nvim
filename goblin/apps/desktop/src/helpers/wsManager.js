const WebSocket = require('ws');
const { EventEmitter } = require('events');

class WebSocketManager extends EventEmitter {
    constructor(config) {
        super();
        this.config = config;
        this.ws = null;
        this.reconnectAttempts = 0;
    }

    connect() {
        this.ws = new WebSocket(this.config.websocket.url);
        
        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            this.emit('connected');
        };

        this.ws.onmessage = (event) => {
            this.emit('message', JSON.parse(event.data));
        };

        this.ws.onclose = () => {
            this.emit('disconnected');
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            this.emit('error', error);
        };
    }

    reconnect() {
        if (this.reconnectAttempts < this.config.websocket.reconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 
                this.config.websocket.reconnectInterval * this.reconnectAttempts);
        }
    }

    sendMessage(message) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
}

module.exports = WebSocketManager;

