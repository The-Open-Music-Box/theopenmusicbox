from .nfc_routes import NFCRoutes
from .web_routes import WebRoutes
from .youtube_routes import YouTubeRoutes

# WebSocketHandlers removed as it appears to be unused legacy code

__all__ = [
    "WebRoutes",
    "NFCRoutes",
    "YouTubeRoutes",
    # 'WebSocketHandlers' # Removed
]
