# urls.py
from django.urls import path
from mouth.views import stream_audio_view, mouth_test

urlpatterns = [
    path('stream-audio/', stream_audio_view, name='stream_audio'),
    path('test/', mouth_test, name='mouth')
]
