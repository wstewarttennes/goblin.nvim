# goblin/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from ears import routing as ears_routing
from eyes import routing as eyes_routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goblin.settings')

websocket_patterns = []
websocket_patterns.extend(ears_routing.websocket_urlpatterns)
websocket_patterns.extend(eyes_routing.websocket_urlpatterns)

print("Available websocket routes:", [pattern.pattern for pattern in websocket_patterns])



application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_patterns)
    ),
})
