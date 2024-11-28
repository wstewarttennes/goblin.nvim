
import os

from mouth.lib.eleven.eleven import Eleven

class Mouth():

    def __init__(self):
        pass
    
    # Defaults to Lily from Eleven
    def speak(self, text, provider="eleven", voice_id="pFZP5JQG7iQjIQuC4Bku"):

        if provider == "eleven":
            eleven = Eleven()
            return eleven.text_to_speech_file(text)
        return False

    def test_speak(self):
        self.speak("Hi, I'm Lily. The capital of Uzbekistan is Tashkent and the president of Tajikistan is Emomali Rahmon.")

