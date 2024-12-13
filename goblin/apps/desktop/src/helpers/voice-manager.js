// voice-manager.js (new file for renderer process)
class VoiceManager {
  constructor(webSocketManager) {
    this.wsManager = webSocketManager;
    this.recognition = null;
    this.synthesis = null;
    this.isListening = false;
    this.isSpeaking = false;
    
    this.initializeSpeechAPIs();
    this.setupEventListeners();
  }

  initializeSpeechAPIs() {
    // Initialize Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      
      this.setupRecognitionHandlers();
    }

    // Initialize Speech Synthesis
    this.synthesis = window.speechSynthesis;
  }

  setupRecognitionHandlers() {
    this.recognition.onresult = (event) => {
      const current = event.resultIndex;
      const transcript = event.results[current][0].transcript;
      
      if (event.results[current].isFinal) {
        // Send message through WebSocket
        this.wsManager.sendMessage({
          type: 'message',
          message: transcript
        });
      }
    };

    this.recognition.onend = () => {
      // Automatically restart if we're supposed to be listening
      if (this.isListening) {
        this.recognition.start();
      }
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      this.isListening = false;
      this.updateVoiceStatus();
    };
  }

  setupEventListeners() {
    // Listen for WebSocket messages to speak responses
    document.addEventListener('ws-message', (event) => {
      const data = event.detail;
      if (data.type === 'chat_message_chunk' && !data.is_complete) {
        this.speakResponse(data.message);
      }
    });
  }

  startListening() {
    if (this.recognition && !this.isListening) {
      this.recognition.start();
      this.isListening = true;
      this.updateVoiceStatus();
    }
  }

  stopListening() {
    if (this.recognition) {
      this.recognition.stop();
      this.isListening = false;
      this.updateVoiceStatus();
    }
  }

  toggleListening() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  speakResponse(text) {
    if (this.synthesis && !this.isSpeaking) {
      // Stop recognition while speaking to prevent feedback
      if (this.isListening) {
        this.recognition.stop();
      }

      const utterance = new SpeechSynthesisUtterance(text);
      
      utterance.onend = () => {
        this.isSpeaking = false;
        // Resume recognition if it was active
        if (this.isListening) {
          this.recognition.start();
        }
      };

      utterance.onstart = () => {
        this.isSpeaking = true;
      };

      this.synthesis.speak(utterance);
    }
  }

  updateVoiceStatus() {
    // Update UI elements
    const statusElement = document.getElementById('voice-status');
    if (statusElement) {
      statusElement.textContent = this.isListening ? 'Listening...' : 'Click to start';
      statusElement.className = this.isListening ? 'status-active' : 'status-inactive';
    }
  }
}
