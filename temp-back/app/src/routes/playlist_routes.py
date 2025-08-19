# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Refactored playlist routes using controllers and dependency injection.

This module provides clean route handlers that delegate business logic
to controllers, following separation of concerns and dependency injection
patterns.
"""

from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    Body,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from socketio import AsyncServer

from app.src.controllers.playlist_controller import PlaylistController
from app.src.controllers.upload_controller import UploadController
from app.src.controllers.audio_controller import AudioController
from app.src.core.service_container import ServiceContainer
from app.src.dependencies import get_audio, get_config
from app.src.helpers.error_handling import ErrorHandler
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class PlaylistRoutes:
    """
    Playlist routes with controller-based architecture.
    
    This class provides clean route handlers that delegate business logic
    to specialized controllers, maintaining separation of concerns.
    """

    def __init__(self, app: FastAPI, socketio: AsyncServer):
        """
        Initialize playlist routes with dependency injection.
        
        Args:
            app: FastAPI application instance.
            socketio: Socket.IO server for real-time events.
        """
        self.app = app
        self.router = APIRouter(prefix="/api/playlists", tags=["playlists"])
        self.socketio = socketio
        
        # Initialize service container and controllers
        self.service_container = ServiceContainer()
        self.playlist_controller = PlaylistController(self.service_container)
        self.upload_controller = UploadController(self.service_container, socketio)
        self.audio_controller = AudioController()
        self.error_handler = ErrorHandler()
        
        self._register_routes()

    def _setup_controls_integration(self):
        """Setup physical controls integration with audio controller."""
        try:
            physical_controls = self.service_container.get_physical_controls_manager()
            if physical_controls.initialize():
                logger.log(LogLevel.INFO, "Physical controls integration initialized successfully")
            else:
                logger.log(LogLevel.WARNING, "Failed to initialize physical controls integration")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting up physical controls integration: {str(e)}")

    def register(self):
        """Register playlist routes with the FastAPI app."""
        self.app.include_router(self.router)
        setattr(self.app, "playlist_routes", self)

    def _register_routes(self):
        """Register all playlist-related routes."""

        @self.router.get("/")
        async def list_playlists(page: int = 1, page_size: int = 50):
            """Get all playlists with pagination support."""
            try:
                result = self.playlist_controller.get_all_playlists(page, page_size)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to retrieve playlists")

        @self.router.post("/", response_model=Dict[str, Any])
        async def create_playlist(body: dict = Body(...)):
            """Create a new playlist."""
            try:
                title = body.get("title")
                if not title:
                    raise ValueError("Title is required")
                
                result = self.playlist_controller.create_playlist(title)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to create playlist")

        @self.router.get("/{playlist_id}", response_model=Dict[str, Any])
        async def get_playlist(playlist_id: str):
            """Get a playlist by ID."""
            try:
                playlist = self.playlist_controller.get_playlist_by_id(playlist_id)
                if not playlist:
                    raise HTTPException(status_code=404, detail="Playlist not found")
                return playlist
            except HTTPException:
                raise
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to retrieve playlist")

        @self.router.delete("/{playlist_id}", response_model=Dict[str, Any])
        async def delete_playlist(playlist_id: str):
            """Delete a playlist and its files."""
            try:
                result = self.playlist_controller.delete_playlist(playlist_id)
                return result
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to delete playlist")

        @self.router.post("/{playlist_id}/upload", response_model=Dict[str, Any])
        async def upload_files(
            playlist_id: str,
            files: List[UploadFile] = File(...),
            config=Depends(get_config),
        ):
            """Upload files to a playlist."""
            try:
                result = await self.upload_controller.upload_files(playlist_id, files, config)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to upload files")

        @self.router.post("/{playlist_id}/upload/init")
        async def create_upload_session(
            playlist_id: str,
            body: dict = Body(...),
            config=Depends(get_config),
        ):
            """Initialize a chunked upload session."""
            try:
                filename = body.get("filename")
                file_size = body.get("file_size")
                
                if not filename or not file_size:
                    raise ValueError("filename and file_size are required")
                
                result = await self.upload_controller.create_upload_session(
                    playlist_id, filename, file_size, config
                )
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to create upload session")

        @self.router.post("/{playlist_id}/upload/chunk")
        async def upload_chunk(
            playlist_id: str,
            session_id: str = Form(...),
            chunk_index: int = Form(...),
            chunk: UploadFile = File(...),
            config=Depends(get_config),
        ):
            """Upload a file chunk."""
            try:
                chunk_data = await chunk.read()
                result = await self.upload_controller.upload_chunk(
                    playlist_id, session_id, chunk_index, chunk_data, config
                )
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to upload chunk")

        @self.router.post("/{playlist_id}/upload/finalize")
        async def finalize_upload(
            playlist_id: str,
            body: dict = Body(...),
            config=Depends(get_config),
        ):
            """Finalize a chunked upload."""
            try:
                session_id = body.get("session_id")
                if not session_id:
                    raise ValueError("session_id is required")
                
                result = await self.upload_controller.finalize_upload(
                    playlist_id, session_id, config
                )
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to finalize upload")

        @self.router.get("/uploads/session/{session_id}")
        async def get_upload_session_status(
            session_id: str,
            config=Depends(get_config),
        ):
            """Get upload session status."""
            try:
                result = await self.upload_controller.get_upload_session_status(session_id, config)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to get session status")

        @self.router.post("/{playlist_id}/reorder", response_model=Dict[str, Any])
        async def reorder_tracks(playlist_id: str, body: dict = Body(...)):
            """Reorder tracks in a playlist."""
            try:
                track_order = body.get("track_order")
                if not track_order:
                    raise ValueError("track_order is required")
                
                result = self.playlist_controller.reorder_tracks(playlist_id, track_order)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to reorder tracks")

        @self.router.delete("/{playlist_id}/tracks", response_model=Dict[str, Any])
        async def delete_tracks(playlist_id: str, body: dict = Body(...)):
            """Delete multiple tracks from a playlist."""
            try:
                track_numbers = body.get("track_numbers")
                if not track_numbers:
                    raise ValueError("track_numbers is required")
                
                result = self.playlist_controller.delete_tracks(playlist_id, track_numbers)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to delete tracks")

        @self.router.post("/{playlist_id}/start", response_model=Dict[str, Any])
        async def start_playlist(playlist_id: str, audio=Depends(get_audio)):
            """Start playing a specific playlist."""
            try:
                result = self.playlist_controller.start_playlist(playlist_id, audio)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to start playlist")

        @self.router.post("/{playlist_id}/play/{track_number}", response_model=Dict[str, Any])
        async def play_track(
            playlist_id: str, track_number: int, audio=Depends(get_audio)
        ):
            """Play a specific track from a playlist."""
            try:
                result = self.playlist_controller.play_track(playlist_id, track_number, audio)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to play track")

        @self.router.post("/control", response_model=Dict[str, Any])
        async def control_playlist(
            request: Request, action: str = Body(..., embed=True)
        ):
            """Control playlist playback (play/pause/next/previous/stop)."""
            try:
                audio = self._get_audio_from_request(request)
                if not audio:
                    raise HTTPException(status_code=503, detail="Audio service not available")
                
                result = self.audio_controller.handle_playback_control(action, audio)
                return result
            except HTTPException:
                raise
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to control playback")

        @self.router.post("/nfc/{nfc_tag_id}/associate/{playlist_id}")
        async def associate_nfc_tag(nfc_tag_id: str, playlist_id: str):
            """Associate an NFC tag with a playlist."""
            try:
                result = self.playlist_controller.associate_nfc_tag(playlist_id, nfc_tag_id)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to associate NFC tag")

        @self.router.delete("/nfc/{playlist_id}")
        async def disassociate_nfc_tag(playlist_id: str):
            """Remove NFC tag association from a playlist."""
            try:
                result = self.playlist_controller.disassociate_nfc_tag(playlist_id)
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to disassociate NFC tag")

        @self.router.get("/nfc/{nfc_tag_id}")
        async def get_playlist_by_nfc_tag(nfc_tag_id: str):
            """Get a playlist by its associated NFC tag."""
            try:
                playlist = self.playlist_controller.get_playlist_by_nfc_tag(nfc_tag_id)
                if not playlist:
                    raise HTTPException(status_code=404, detail="No playlist associated with this NFC tag")
                return playlist
            except HTTPException:
                raise
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to retrieve playlist by NFC tag")

        @self.router.post("/sync")
        async def sync_with_filesystem():
            """Synchronize playlists with the filesystem."""
            try:
                result = self.playlist_controller.sync_with_filesystem()
                return result
            except Exception as e:
                return self.error_handler.handle_http_error(e, "Failed to sync with filesystem")

    def _get_audio_from_request(self, request: Request):
        """Get audio service from request context."""
        try:
            container = getattr(request.app, "container", None)
            if container and hasattr(container, "audio"):
                return container.audio
            return None
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error getting audio from request: {str(e)}")
            return None
