const WebSocket = require('ws');
const socket = new WebSocket('ws://localhost:8000/ws/chat/');

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
