from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/eyes/screenshots/?$', consumers.ScreenshotConsumer.as_asgi()),
]
