from django.shortcuts import render
from django.http import StreamingHttpResponse
from mouth.lib.eleven.eleven import Eleven
import re


def mouth_test(request):
    return render(request, 'mouth_test.html')

def stream_audio_view(request):
    text = request.GET.get('text', 'Hello, this is a test.')

    eleven_api = Eleven()

    # Split the text into sentences using a regex
    sentences = re.split(r'(?<=[.!?]) +', text)

    def sentence_audio_generator(sentences):
        for sentence in sentences:
            if sentence.strip():
                audio_stream = eleven_api.text_to_speech_stream(sentence)

                # Read and yield chunks of audio data for each sentence
                while True:
                    chunk = audio_stream.read(1024)  # Adjust chunk size if needed
                    if not chunk:
                        break
                    yield chunk

    # Create a streaming response that sends audio data progressively
    response = StreamingHttpResponse(sentence_audio_generator(sentences), content_type='audio/mpeg')
    response['Content-Disposition'] = 'inline; filename="output.mp3"'
    return response
