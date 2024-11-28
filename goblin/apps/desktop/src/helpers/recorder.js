const { EventEmitter } = require('events');

class AudioRecorder extends EventEmitter {
    constructor(config) {
        super();
        this.config = config;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.emit('recordingComplete', audioBlob);
                this.audioChunks = [];
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.emit('recordingStart');
        } catch (error) {
            this.emit('error', error);
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.emit('recordingStop');
        }
    }
}

module.exports = AudioRecorder;

