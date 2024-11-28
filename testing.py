# server.py
from flask import Flask, request, jsonify
import whisper
import numpy as np
import pyaudio
import wave
import threading
import queue
import tempfile
import os

app = Flask(__name__)

class AudioProcessor:
    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name)
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.chunk_size = 1024
        self.format = pyaudio.paFloat32
        self.channels = 1
        self.rate = 16000  # Whisper expects 16kHz
        
        self.p = pyaudio.PyAudio()
        self.chunks = []
        
    def start_recording(self):
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.processing_thread = threading.Thread(target=self._process_audio)
        self.recording_thread.start()
        self.processing_thread.start()
    
    def stop_recording(self):
        self.is_recording = False
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join()
            self.processing_thread.join()
    
    def _record_audio(self):
        stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        while self.is_recording:
            data = stream.read(self.chunk_size)
            self.chunks.append(data)
            
            # Create a chunk every 3 seconds
            if len(self.chunks) * self.chunk_size >= self.rate * 3:
                self.audio_queue.put(b''.join(self.chunks))
                self.chunks = []
        
        stream.stop_stream()
        stream.close()
    
    def _process_audio(self):
        while self.is_recording or not self.audio_queue.empty():
            try:
                audio_data = self.audio_queue.get(timeout=1)
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
                    # Save audio chunk to temporary WAV file
                    with wave.open(temp_file.name, 'wb') as wf:
                        wf.setnchannels(self.channels)
                        wf.setsampwidth(self.p.get_sample_size(self.format))
                        wf.setframerate(self.rate)
                        wf.writeframes(audio_data)
                    
                    # Transcribe with Whisper
                    result = self.model.transcribe(temp_file.name)
                    if result["text"].strip():
                        print(f"Transcribed: {result['text']}")
                        # Send to client (you'll need to implement your preferred way
                        # of getting this back to Neovim)
            except queue.Empty:
                continue

processor = AudioProcessor()

@app.route('/start', methods=['POST'])
def start_recording():
    processor.start_recording()
    return jsonify({'status': 'started'})

@app.route('/stop', methods=['POST'])
def stop_recording():
    processor.stop_recording()
    return jsonify({'status': 'stopped'})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({'is_recording': processor.is_recording})

if __name__ == '__main__':
    app.run(host='localhost', port=8765)
