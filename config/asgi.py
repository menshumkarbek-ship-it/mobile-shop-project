import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize the core ASGI application
django_asgi_app = get_asgi_application()

# Handle standard web traffic alongside stateful persistent WebSocket loops
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            [path("ws/live-updates/", django_asgi_app)])
    ),
})