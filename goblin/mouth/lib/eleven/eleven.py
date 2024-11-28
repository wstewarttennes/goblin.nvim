import requests
import json
import os
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import uuid
from typing import IO
from io import BytesIO
from elevenlabs import play, stream, save


class Eleven():

    def __init__(self):
        self.API_KEY = os.environ.get("ELEVEN_LABS_API_KEY")
        self.BASE_URL = "https://api.elevenlabs.io/"
        self.DEFAULT_HEADERS = {
            "Accept": "application/json",
            "xi-api-key": self.API_KEY,
            "Content-Type": "application/json"
        }
        self.client = ElevenLabs(
            api_key=self.API_KEY,
        )

    def text_to_speech_file(self, text: str) -> str:
        # Calling the text_to_speech conversion API with detailed parameters
        response = self.client.text_to_speech.convert(
            voice_id="pFZP5JQG7iQjIQuC4Bku", # Lily pre-made voice
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_turbo_v2_5", # use the turbo model for low latency
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
            ),
        )

        # play(response)

        # Generating a unique file name for the output MP3 file
        save_file_path = f"{uuid.uuid4()}.mp3"

        # Writing the audio to a file
        with open(save_file_path, "wb") as f:
            for chunk in response:
                if chunk:
                    f.write(chunk)

        print(f"{save_file_path}: A new audio file was saved successfully!")

        # Return the path of the saved audio file
        return save_file_path

    def text_to_speech_stream(self, text: str) -> IO[bytes]:
        # Perform the text-to-speech conversion
        response = self.client.text_to_speech.convert(
            voice_id="pFZP5JQG7iQjIQuC4Bku", # Lily
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
            ),
        )

        # Create a BytesIO object to hold the audio data in memory
        audio_stream = BytesIO()

        # Write each chunk of audio data to the stream
        for chunk in response:
            if chunk:
                audio_stream.write(chunk)

        # Reset stream position to the beginning
        audio_stream.seek(0)

        # Return the stream for further use
        return audio_stream

    # def convert_text_to_speach_basic(self, text, voice_id):
    #     CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
    #     OUTPUT_PATH = "output.mp3"
    #
    #     data = {
    #         "text": text,
    #         "model_id": "eleven_multilingual_v2",
    #         "voice_settings": {
    #             "stability": 0.5,
    #             "similarity_boost": 0.8,
    #             "style": 0.0,
    #             "use_speaker_boost": True
    #         }
    #     }
    #
    #     response = requests.post(
    #         self.BASE_URL + f"v1/text-to-speech/{voice_id}/stream" , 
    #         headers=self.DEFAULT_HEADERS,
    #         json=data,
    #         stream=True
    #     )
    #
    #     # Check if the request was successful
    #     if response.ok:
    #         # Open the output file in write-binary mode
    #         with open(OUTPUT_PATH, "wb") as f:
    #             # Read the response in chunks and write to the file
    #             for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
    #                 f.write(chunk)
    #         # Inform the user of success
    #         print("Audio stream saved successfully.")
    #     else:
    #         # Print the error message if the request was not successful
    #         print(response.text)
    #






