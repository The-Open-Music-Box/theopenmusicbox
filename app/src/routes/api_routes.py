# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

from fastapi import FastAPI

from app.src.core.container_async import ContainerAsync
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.routes.nfc_routes import NFCRoutes
from app.src.routes.playlist_routes import PlaylistRoutes
from app.src.routes.system_routes import SystemRoutes
from app.src.routes.web_routes import WebRoutes
from app.src.routes.websocket_handlers_async import WebSocketHandlersAsync
from app.src.routes.youtube_routes import YouTubeRoutes

logger = ImprovedLogger(__name__)


class APIRoutes:
    """Organizes and initializes all API route groups for the application.

    This class instantiates and registers the various route handlers. It
    also manages their dependencies and provides a unified entry point
    for route initialization.
    """

    def __init__(self, app: FastAPI, socketio, container: ContainerAsync):
        self.app = app
        self.socketio = socketio
        self.container = container

        self.web_routes = WebRoutes(app)
        logger.log(
            LogLevel.INFO,
            f"APIRoutes: Checking NFC service availability. container.nfc is {self.container.nfc}",
        )
        if self.container.nfc:
            logger.log(
                LogLevel.INFO,
                f"APIRoutes: NFC service available, initializing NFC routes",
            )
            self.nfc_routes = NFCRoutes(app, socketio, self.container.nfc)
            self.websocket_handlers = WebSocketHandlersAsync(
                socketio, app, self.container.nfc
            )
        else:
            logger.log(
                LogLevel.WARNING,
                "APIRoutes: NFC service not available from container. NFC-dependent routes will not be initialized.",
            )
            self.nfc_routes = None
            self.websocket_handlers = None

        self.youtube_routes = YouTubeRoutes(app, socketio)
        self.playlist_routes = PlaylistRoutes(app)
        self.system_routes = SystemRoutes(app)

    def init_routes(self):
        """Initialize all application routes."""
        try:
            self.playlist_routes.register()
            if self.nfc_routes:
                self.nfc_routes.register()
            if self.websocket_handlers:
                self.websocket_handlers.register()
            self.youtube_routes.register()
            self.system_routes.register()
            self.web_routes.register()

            logger.log(LogLevel.INFO, "APIRoutes: Routes initialized successfully")

        except Exception as e:
            logger.log(
                LogLevel.ERROR, f"Failed to initialize routes: {str(e)}", exc_info=True
            )
            raise


def init_api_routes(app: FastAPI, socketio, container: ContainerAsync):
    """Entry point for API route initialization."""
    routes_organizer = APIRoutes(app, socketio, container)
    routes_organizer.init_routes()
    return routes_organizer
