# app/src/routes/api_routes.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.nfc_service import NFCService
from app.src.routes.web_routes import WebRoutes
from app.src.routes.nfc_routes import NFCRoutes
from app.src.routes.youtube_routes import YouTubeRoutes
from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync
from app.src.routes.playlist_routes import PlaylistRoutes

logger = ImprovedLogger(__name__)

class APIRoutes:
    def __init__(self, app: FastAPI, socketio):
        self.app = app
        self.socketio = socketio

        # CORS est maintenant géré dans main_async.py

        # Create NFC service
        nfc_service = NFCService(socketio)

        # Initialisation des routes
        self.web_routes = WebRoutes(app)
        self.nfc_routes = NFCRoutes(app, nfc_service)
        self.youtube_routes = YouTubeRoutes(app, socketio)
        self.websocket_handlers = WebSocketHandlersAsync(socketio, app, nfc_service)
        self.playlist_routes = PlaylistRoutes(app)

    def init_routes(self):
        """Initialize toutes les routes de l'application."""
        try:
            logger.log(LogLevel.INFO, "Initializing routes")

            # Enregistrement des routes par domaine
            self.web_routes.register()
            self.nfc_routes.register()
            self.youtube_routes.register()
            self.websocket_handlers.register()
            self.playlist_routes.register()

            logger.log(LogLevel.INFO, "Routes initialized successfully")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize routes: {str(e)}")
            raise

def init_routes(app: FastAPI, socketio):
    """Point d'entrée pour l'initialisation des routes."""
    routes = APIRoutes(app, socketio)
    routes.init_routes()
    return routes