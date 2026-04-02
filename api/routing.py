"""
WebSocket URL routing configuration.
"""
from django.urls import path
from api.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/", ChatConsumer.as_asgi()),
]
