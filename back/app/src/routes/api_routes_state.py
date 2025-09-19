# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Server-Authoritative API Routes Integration

This module provides the integration layer for the server-authoritative state
management system, replacing the original api_routes.py with state broadcasting.
"""

from fastapi import FastAPI

# Legacy container removed - using domain bootstrap instead
from app.src.monitoring import get_logger
from app.src.services.error.unified_error_decorator import handle_errors
from app.src.monitoring.logging.log_level import LogLevel
from app.src.routes.nfc_unified_routes import UnifiedNFCRoutes
from app.src.routes.player_routes import PlayerRoutes
from app.src.routes.playlist_routes_state import PlaylistRoutesState
from app.src.routes.system_routes import SystemRoutes
from app.src.routes.web_routes import WebRoutes
from app.src.routes.youtube_routes import YouTubeRoutes

logger = get_logger(__name__)


class APIRoutesState:
    """
    Server-authoritative API routes organizer.

    This class replaces APIRoutes to integrate the server-authoritative
    state management system across all route handlers.
    """

    @handle_errors("api_routes_state_init", return_response=False)
    def __init__(self, app: FastAPI, socketio, config=None):
        """Initialize API routes with domain architecture.

        Args:
            app: FastAPI application instance
            socketio: Socket.IO server for real-time events
            config: Application configuration object
        """
        self.app = app
        self.socketio = socketio
        self.config = config

        # Initialize routes with server-authoritative state management
        self.web_routes = WebRoutes(app)

        # Initialize server-authoritative playlist routes with domain architecture
        self.playlist_routes = PlaylistRoutesState(app, socketio, config)

        # Initialize player routes with state management
        self.player_routes = PlayerRoutes(app, socketio)

        # Initialize domain-driven NFC routes
        self.nfc_routes = UnifiedNFCRoutes(app, socketio)
        # NFC state management is handled internally by UnifiedNFCRoutes
        logger.log(LogLevel.INFO, "Domain-driven NFC routes initialized")
        self.youtube_routes = YouTubeRoutes(app, socketio)
        # NFC routes now unified - removed nfc_associate_routes
        self.system_routes = SystemRoutes(app)

    @handle_errors("api_routes_state_init")
    def init_routes(self):
        """Initialize all application routes with server-authoritative state management."""
        logger.log(LogLevel.INFO, "🔧 DEBUG: Starting route registration...")
        logger.log(LogLevel.INFO, "🔧 Registering server-authoritative playlist routes...")
        # Register server-authoritative playlist routes first
        self.playlist_routes.register()
        logger.log(LogLevel.INFO, "🔧 DEBUG: Playlist routes registered")
        logger.log(LogLevel.INFO, "🔧 Registering player routes...")
        # Register player routes with state management
        self.player_routes.register_with_app()
        logger.log(LogLevel.INFO, "🔧 DEBUG: Player routes registered")
        logger.log(LogLevel.INFO, "🔧 Registering NFC routes...")
        # Register other routes
        if self.nfc_routes:
            self.nfc_routes.register_with_app()
        logger.log(LogLevel.INFO, "🔧 DEBUG: NFC routes registered")
        logger.log(LogLevel.INFO, "🔧 Registering YouTube routes...")
        self.youtube_routes.register()
        logger.log(LogLevel.INFO, "🔧 DEBUG: YouTube routes registered")
        logger.log(LogLevel.INFO, "🔧 Registering system routes...")
        self.system_routes.register()
        logger.log(LogLevel.INFO, "🔧 DEBUG: System routes registered")
        logger.log(LogLevel.INFO, "🔧 Registering web routes...")
        self.web_routes.register()
        logger.log(LogLevel.INFO, "🔧 DEBUG: Web routes registered")
        logger.log(LogLevel.INFO, "🔧 Starting background services...")
        # Start TrackProgressService after all routes are registered
        import asyncio

        logger.log(LogLevel.INFO, "🚀 ATTEMPTING to start TrackProgressService...")
        loop = asyncio.get_event_loop()
        logger.log(LogLevel.INFO, f"📋 Event loop status: running={loop.is_running()}")
        if loop.is_running():
            # Service is already initialized in PlaylistRoutesState, just start it
            if hasattr(self.playlist_routes, "progress_service"):
                logger.log(LogLevel.INFO, "✅ TrackProgressService found, starting...")
                loop.create_task(self.playlist_routes.progress_service.start())
                logger.log(
                    LogLevel.INFO,
                    "🎵 TrackProgressService started successfully - should emit position events every 200ms",
                )
                # Log service configuration
                service = self.playlist_routes.progress_service
                logger.log(
                    LogLevel.INFO,
                    f"🔧 TrackProgressService config: interval={service.interval}s, running={service.is_running}",
                )
            else:
                logger.log(LogLevel.ERROR, "❌ TrackProgressService NOT FOUND in playlist_routes!")
            # Start StateManager cleanup task for periodic maintenance
            logger.log(LogLevel.INFO, "🔧 Starting StateManager cleanup task...")
            loop.create_task(self.playlist_routes.state_manager.start_cleanup_task())
            logger.log(LogLevel.INFO, "✅ StateManager cleanup task started successfully")
            logger.log(LogLevel.INFO, "✅ All background services started successfully")
        else:
            logger.log(
                LogLevel.WARNING, "Event loop not running, background services will start with app"
            )
        logger.log(LogLevel.INFO, "🔧 DEBUG: Route initialization completed")


def init_api_routes_state(app: FastAPI, socketio, config=None):
    """Entry point for server-authoritative API route initialization with domain architecture."""
    routes_organizer = APIRoutesState(app, socketio, config)
    routes_organizer.init_routes()
    return routes_organizer
