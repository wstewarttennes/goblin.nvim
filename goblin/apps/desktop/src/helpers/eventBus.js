const { EventEmitter } = require('events');

class EventBus extends EventEmitter {
    constructor() {
        super();
        this.handlers = {};
    }

    subscribe(event, handler) {
        this.on(event, handler);
        this.handlers[event] = this.handlers[event] || [];
        this.handlers[event].push(handler);
    }

    unsubscribe(event, handler) {
        this.removeListener(event, handler);
        if (this.handlers[event]) {
            this.handlers[event] = this.handlers[event]
                .filter(h => h !== handler);
        }
    }

    publish(event, data) {
        this.emit(event, data);
    }
}

module.exports = new EventBus();
