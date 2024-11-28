import json
import queue
import sounddevice as sd
import vosk
import numpy as np
import threading
import whisper
from anthropic import Anthropic
import sys
import time

class VoskWakeWordDetector:
    def __init__(self, sample_rate=16000):
        # Initialize Vosk model - using small model for speed
        vosk.SetLogLevel(-1)  # Reduce logging
        self.model = vosk.Model(lang="en-us", model_path="vosk-model-small-en-us")
        self.rec = vosk.KaldiRecognizer(self.model, sample_rate)
        
        # Set "Goblin" as wake word
        self.wake_word = "goblin"
        
        # Audio settings
        self.sample_rate = sample_rate
        self.block_size = 8000  # Process in chunks
        
class FastVoiceAssistant:
    def __init__(self):
        # Initialize audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.dtype = np.int16
        
        # Initialize wake word detector
        self.wake_detector = VoskWakeWordDetector(self.sample_rate)
        
        # Initialize Whisper for command recognition
        self.whisper_model = whisper.load_model("tiny", device="cuda")
        
        # Initialize Anthropic client
        self.anthropic = Anthropic(api_key="YOUR_API_KEY")
        
        # Queues for audio processing
        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # Buffer for continuous recording
        self.buffer = np.array([], dtype=self.dtype)
        
        # State flags
        self.listening_for_command = False
        self.running = False
        
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(status)
        
        # Add audio to processing queue
        self.audio_queue.put(bytes(indata))
        
    def process_audio(self):
        """Process audio stream for wake word detection"""
        while self.running:
            try:
                audio_chunk = self.audio_queue.get()
                
                if self.listening_for_command:
                    # Add to command buffer
                    self.buffer = np.append(self.buffer, 
                                          np.frombuffer(audio_chunk, dtype=self.dtype))
                    
                    # Check for end of command (silence or max duration)
                    if self._detect_silence(self.buffer) or len(self.buffer) > self.sample_rate * 10:
                        self._process_command(self.buffer)
                        self.buffer = np.array([], dtype=self.dtype)
                        self.listening_for_command = False
                        print("\nListening for wake word 'Goblin'...")
                
                else:
                    # Check for wake word
                    if self.wake_detector.rec.AcceptWaveform(audio_chunk):
                        result = json.loads(self.wake_detector.rec.Result())
                        
                        if 'text' in result and self.wake_detector.wake_word in result['text'].lower():
                            print("\nWake word detected! Listening for command...")
                            self.listening_for_command = True
                
            except Exception as e:
                print(f"Error processing audio: {e}")
                
    def _detect_silence(self, audio_data, threshold=500, duration=0.5):
        """Detect silence in audio data"""
        chunk_size = int(self.sample_rate * duration)
        if len(audio_data) < chunk_size:
            return False
            
        # Check last chunk for silence
        last_chunk = audio_data[-chunk_size:]
        return np.max(np.abs(last_chunk)) < threshold
        
    def _process_command(self, audio_data):
        """Process captured command"""
        try:
            # Convert to float32
            float_data = audio_data.astype(np.float32) / 32768.0
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                float_data,
                language="en",
                fp16=True
            )
            
            command_text = result["text"].strip()
            if command_text:
                print(f"You said: {command_text}")
                
                # Get LLM response
                response = self._get_llm_response(command_text)
                print(f"Assistant: {response}")
                
        except Exception as e:
            print(f"Error processing command: {e}")
            
    def _get_llm_response(self, text):
        """Get response from Claude"""
        try:
            message = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                temperature=0,
                system="You are a helpful voice assistant. Keep responses brief and casual.",
                messages=[{
                    "role": "user",
                    "content": text
                }]
            )
            return message.content
            
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return "Sorry, I couldn't process that request."
            
    def start(self):
        """Start the voice assistant"""
        try:
            self.running = True
            
            # Start audio stream
            self.stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.wake_detector.block_size,
                callback=self.audio_callback
            )
            
            # Start processing thread
            self.process_thread = threading.Thread(target=self.process_audio)
            self.process_thread.daemon = True
            self.process_thread.start()
            
            print("Started! Listening for wake word 'Goblin'...")
            
            with self.stream:
                while self.running:
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Error starting assistant: {e}")
            self.stop()
            
    def stop(self):
        """Stop the voice assistant"""
        self.running = False
        if hasattr(self, 'stream'):
            self.stream.stop()
        if hasattr(self, 'process_thread'):
            self.process_thread.join()
        print("Stopped voice assistant")

def main():
    # Download Vosk model if not present
    if not vosk.Model.model_path_exists("vosk-model-small-en-us"):
        print("Downloading Vosk model...")
        # You'll need to download the model from https://alphacephei.com/vosk/models
        # and extract it to vosk-model-small-en-us
        
    assistant = FastVoiceAssistant()
    try:
        assistant.start()
    except KeyboardInterrupt:
        print("\nStopping...")
        assistant.stop()
        print("Goodbye!")

if __name__ == "__main__":
    main()
