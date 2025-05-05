# app/src/routes/__init__.py

from .web_routes import WebRoutes
from .nfc_routes import NFCRoutes
from .youtube_routes import YouTubeRoutes
from .websocket_handlers import WebSocketHandlers

__all__ = [
    'WebRoutes',
    'NFCRoutes',
    'YouTubeRoutes',
    'WebSocketHandlers'
]