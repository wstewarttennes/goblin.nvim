module.exports = {
    websocket: {
        url: 'ws://localhost:8000/ws/chat/',
        reconnectAttempts: 5,
        reconnectInterval: 1000
    },
    recording: {
        sampleRate: 44100,
        channels: 1,
        format: 'wav'
    },
    window: {
        width: 800,
        height: 600,
        minWidth: 400,
        minHeight: 300
    }
};
