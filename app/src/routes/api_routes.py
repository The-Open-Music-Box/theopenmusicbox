# app/src/routes/api_routes.py

from flask import Blueprint
from flask_cors import CORS

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .web_routes import WebRoutes
from .nfc_routes import NFCRoutes
from .youtube_routes import YouTubeRoutes
from .websocket_handlers import WebSocketHandlers

logger = ImprovedLogger(__name__)

class APIRoutes:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio

        # Configuration CORS
        CORS(self.app, origins=app.container.config.cors_allowed_origins)

        # Initialisation des routes
        self.web_routes = WebRoutes(app)
        self.nfc_routes = NFCRoutes(app)
        self.youtube_routes = YouTubeRoutes(app, socketio)
        self.websocket_handlers = WebSocketHandlers(socketio)

    def init_routes(self):
        """Initialize toutes les routes de l'application."""
        try:
            logger.log(LogLevel.INFO, "Initializing routes")

            # Enregistrement des routes par domaine
            self.web_routes.register()
            self.nfc_routes.register()
            self.youtube_routes.register()
            self.websocket_handlers.register()

            logger.log(LogLevel.INFO, "Routes initialized successfully")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize routes: {str(e)}")
            raise

def init_routes(app, socketio):
    """Point d'entrée pour l'initialisation des routes."""
    routes = APIRoutes(app, socketio)
    routes.init_routes()
    return routes