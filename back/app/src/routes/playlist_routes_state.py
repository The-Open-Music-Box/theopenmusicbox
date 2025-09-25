# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Server-Authoritative Playlist Routes

This module provides HTTP routes that integrate with the StateManager to ensure
all playlist operations broadcast state changes to subscribed clients.
"""

from typing import Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    FastAPI,
    File,
    Query,
    Request,
    UploadFile,
)
from socketio import AsyncServer

from app.src.application.controllers.unified_controller import (
    unified_controller as PlaylistControllerState,
)
from app.src.controllers.upload_controller import UploadController
from app.src.dependencies import get_audio_service
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.state_manager import StateManager, StateEventType
from app.src.routes.websocket_handlers_state import WebSocketStateHandlers

# REFACTORING: Import unified services to eliminate duplications
from app.src.services.response.unified_response_service import UnifiedResponseService
from app.src.services.serialization.unified_serialization_service import UnifiedSerializationService
from app.src.services.broadcasting.unified_broadcasting_service import UnifiedBroadcastingService
from app.src.services.validation.unified_validation_service import UnifiedValidationService
from app.src.services.error.unified_error_decorator import handle_http_errors

logger = get_logger(__name__)


class PlaylistRoutesState:
    """
    Server-authoritative playlist routes with state broadcasting.

    This class provides HTTP endpoints that integrate with the StateManager
    to broadcast all changes to subscribed clients in real-time.
    """

    def __init__(self, app: FastAPI, socketio: AsyncServer, config=None):
        """
        Initialize server-authoritative playlist routes with domain architecture.

        Args:
            app: FastAPI application instance.
            socketio: Socket.IO server for real-time events.
            config: Application configuration object.
        """
        self.app = app
        self.router = APIRouter(prefix="/api/playlists", tags=["playlists"])
        self.socketio = socketio
        self.config = config

        # Domain-driven architecture - no container needed

        # Initialize state management system
        from app.src.services.state_manager import StateManager

        self.state_manager = StateManager(socketio)

        # REFACTORING: Initialize unified broadcasting service
        self.broadcasting_service = UnifiedBroadcastingService(self.state_manager)

        # Use unified domain controllers with StateManager integration
        self.playlist_controller = PlaylistControllerState  # Already imported unified controller
        # Inject StateManager into unified controller for proper state broadcasting
        self.playlist_controller._state_manager = self.state_manager

        # Initialize upload controller with domain architecture dependencies
        self.upload_controller = UploadController(self.config, socketio)

        # DOMAIN ARCHITECTURE: Initialize AudioController with domain audio engine
        from app.src.controllers.audio_controller import AudioController
        from app.src.domain.audio.container import audio_domain_container

        if audio_domain_container.is_initialized:
            # Use domain audio engine for pure architecture
            domain_audio_engine = audio_domain_container.audio_engine
            self.audio_controller = AudioController(
                audio_service=domain_audio_engine, state_manager=self.state_manager
            )
            logger.log(
                LogLevel.INFO,
                f"✅ AudioController initialized with domain audio engine: "
                f"{type(domain_audio_engine).__name__}",
            )
        else:
            # Fallback: Create AudioController without domain audio engine
            self.audio_controller = AudioController(None, state_manager=self.state_manager)
            logger.log(
                LogLevel.WARNING, "⚠️ AudioController initialized without domain audio engine"
            )

        from app.src.infrastructure.error_handling.unified_error_handler import unified_error_handler

        self.error_handler = unified_error_handler

        # Initialize centralized PlayerStateService
        from app.src.services.player_state_service import PlayerStateService

        self.player_state_service = PlayerStateService(self.audio_controller, self.state_manager)

        # Initialize PhysicalControlsManager with GPIO integration
        from app.src.controllers.physical_controls_manager import PhysicalControlsManager

        self.physical_controls_manager = PhysicalControlsManager(
            audio_controller=self.audio_controller,
            hardware_config=self.config.hardware_config if self.config else None
        )

        # Initialize track progress service (server-authoritative progress events)
        from app.src.services.track_progress_service import TrackProgressService

        # Use default interval from SocketConfig (200ms for smooth updates)
        logger.log(LogLevel.INFO, "🎯 Creating TrackProgressService...")
        self.progress_service = TrackProgressService(self.state_manager, self.audio_controller)
        logger.log(
            LogLevel.INFO,
            f"✅ TrackProgressService created with interval={self.progress_service.interval}s",
        )

        # PURE DOMAIN ARCHITECTURE: No legacy services - use application services only
        from app.src.application.services.playlist_application_service import playlist_app_service

        self.playlist_app_service = playlist_app_service
        logger.log(LogLevel.INFO, "🎼 Pure domain architecture - Application service initialized")

        # Connect PlaybackSubject to StateManager for real-time player events
        self._setup_playback_subject_bridge()

        # Initialize WebSocket handlers
        self.websocket_handlers = WebSocketStateHandlers(socketio, app, self.state_manager)

        self._register_routes()

        # Start TrackProgressService immediately after initialization
        self._start_background_services()

        logger.log(LogLevel.INFO, "Server-authoritative playlist routes initialized")

    def register(self):
        """Register playlist routes and WebSocket handlers with the FastAPI app."""
        self.app.include_router(self.router)
        self.websocket_handlers.register()
        setattr(self.app, "playlist_routes_state", self)
        setattr(self.app, "state_manager", self.state_manager)

        # Background services are started in __init__ via _start_background_services()
        logger.log(LogLevel.INFO, "PlaylistRoutesState registered with FastAPI app")

    @handle_http_errors()
    def _start_background_services(self):
        """Start background services required for real-time updates."""
        import asyncio

        # Store reference to progress task for later cleanup if needed
        self._progress_task = None
        # Don't start here - let APIRoutesState handle it after all routes are registered
        logger.log(
            LogLevel.INFO,
            "TrackProgressService will be started by APIRoutesState after route registration",
        )
        # StateManager components are initialized automatically
        logger.log(LogLevel.INFO, "Background services initialization completed")

    def _register_routes(self):
        """Register all server-authoritative playlist routes."""

        @self.router.get("/test-route")
        async def test_route():
            """Test route to verify router is working."""
            return {"status": "success", "message": "Test route working"}

        @self.router.get("/debug")
        @handle_http_errors()
        async def debug_playlists():
            """Debug route to test playlist logic."""
            playlists = self.playlist_controller.get_all_playlists(1, 10)
            return {
                "status": "success",
                "debug": True,
                "playlists_count": len(playlists) if playlists else 0,
                "first_playlist": playlists[0] if playlists else None,
                "playlists": playlists,
            }

        # Handle both with and without trailing slash
        @self.router.get("")
        @self.router.get("/")
        async def list_playlists_index(
            page: int = Query(1, description="Page number"),
            limit: int = Query(50, description="Number of playlists to return"),
            request: Request = None,
        ):
            """Get all playlists with pagination."""
            try:
                playlists = await self.playlist_controller.get_all_playlists(page, limit)

                if playlists is None:
                    playlists = []

                # REFACTORING: Use UnifiedSerializationService for
                # consistent playlist formatting
                serialized_playlists = UnifiedSerializationService.serialize_bulk_playlists(
                    playlists,
                    format=UnifiedSerializationService.FORMAT_API,
                    include_tracks=True,  # Include tracks for full data
                )

                total_count = len(serialized_playlists)
                total_pages = (total_count + limit - 1) // limit

                data = {
                    "playlists": serialized_playlists,
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "total_pages": total_pages,
                }

                # REFACTORING: Use UnifiedResponseService for consistent response format
                return UnifiedResponseService.success(
                    message="Playlists retrieved successfully",
                    data=data,
                    server_seq=self.state_manager.get_global_sequence(),
                )

            except Exception as e:
                logger.log(
                    LogLevel.ERROR,
                    f"Error in list_playlists_index: {str(e)}",
                    extra={"traceback": True},
                )
                # REFACTORING: Use UnifiedResponseService for error responses
                return UnifiedResponseService.internal_error(
                    message="Failed to retrieve playlists", operation="list_playlists_index"
                )

        @self.router.post("")
        @self.router.post("/")
        async def create_playlist(body: dict = Body(...)):
            """Create a new playlist with state broadcasting."""
            try:
                # REFACTORING: Use UnifiedValidationService for
                # input validation
                is_valid, validation_errors = UnifiedValidationService.validate_playlist_data(
                    body, context="api"
                )

                if not is_valid:
                    return UnifiedResponseService.validation_error(
                        errors=validation_errors, client_op_id=body.get("client_op_id")
                    )

                title = body.get("title")
                description = body.get("description", "")
                client_op_id = body.get("client_op_id")

                # Use the controller for proper state management
                result = await self.playlist_controller.create_playlist(
                    title, description, client_op_id
                )

                if not result or result.get("status") != "success":
                    return UnifiedResponseService.internal_error(
                        message="Failed to create playlist",
                        operation="create_playlist",
                        client_op_id=client_op_id,
                    )

                # REFACTORING: Use UnifiedSerializationService for consistent formatting
                playlist_data = result.get("playlist")
                serialized_playlist = UnifiedSerializationService.serialize_playlist(
                    playlist_data,
                    format=UnifiedSerializationService.FORMAT_API,
                    include_tracks=True,
                )

                # REFACTORING: Use UnifiedResponseService for created response
                return UnifiedResponseService.created(
                    message="Playlist created successfully",
                    data=serialized_playlist,
                    client_op_id=client_op_id,
                )

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error creating playlist: {str(e)}")
                return UnifiedResponseService.internal_error(
                    message="Failed to create playlist",
                    operation="create_playlist",
                    client_op_id=body.get("client_op_id") if isinstance(body, dict) else None,
                )

        @self.router.get("/{playlist_id}")
        async def get_playlist(playlist_id: str):
            """Get a specific playlist (read-only, no state broadcast)."""
            try:
                logger.log(LogLevel.INFO, f"GET /api/playlists/{playlist_id} called")
                result = await self.playlist_controller.get_playlist(playlist_id)

                if result is None:
                    logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
                    return UnifiedResponseService.not_found(
                        resource="Playlist", resource_id=playlist_id
                    )

                # REFACTORING: Use UnifiedSerializationService for consistent formatting
                serialized_playlist = UnifiedSerializationService.serialize_playlist(
                    result,
                    format=UnifiedSerializationService.FORMAT_API,
                    include_tracks=True,
                    calculate_duration=True,
                )

                # REFACTORING: Use UnifiedResponseService for success response
                logger.log(
                    LogLevel.INFO,
                    f"Returning playlist with {len(serialized_playlist.get('tracks', []))} tracks",
                )
                return UnifiedResponseService.success(
                    message="Playlist retrieved successfully",
                    data=serialized_playlist,
                    server_seq=self.state_manager.get_global_sequence(),
                )

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error getting playlist {playlist_id}: {str(e)}")
                return UnifiedResponseService.internal_error(
                    message="Failed to retrieve playlist", operation="get_playlist"
                )

        @self.router.put("/{playlist_id}")
        @handle_http_errors()
        async def update_playlist(
            playlist_id: str, body: dict = Body(...), request: Request = None
        ):
            """Update a playlist with state broadcasting."""
            updates = {"title": body.get("title"), "description": body.get("description")}
            # Remove None values
            updates = {k: v for k, v in updates.items() if v is not None}
            client_op_id = body.get("client_op_id")
            if not updates:
                return UnifiedResponseService.bad_request(message="No valid updates provided")
            result = await self.playlist_controller.update_playlist(
                playlist_id, updates, client_op_id
            )
            return result

        @self.router.delete("/{playlist_id}", status_code=204)
        @handle_http_errors()
        async def delete_playlist(playlist_id: str, body: dict = Body(...)):
            """Delete a playlist with state broadcasting."""
            client_op_id = body.get("client_op_id")  # Optional for HTTP requests
            result = await self.playlist_controller.delete_playlist(playlist_id, client_op_id)
            return None  # 204 No Content

        @self.router.post("/{playlist_id}/reorder")
        @handle_http_errors()
        async def reorder_tracks(playlist_id: str, body: dict = Body(...), request: Request = None):
            """Reorder tracks with state broadcasting."""
            track_order = body.get("track_order")
            client_op_id = body.get("client_op_id")
            if not track_order or not isinstance(track_order, list):
                return UnifiedResponseService.bad_request(
                    message="track_order must be a non-empty list"
                )
            result = await self.playlist_controller.reorder_tracks(
                playlist_id, track_order, client_op_id
            )
            if not result or result.get("status") != "success":
                return UnifiedResponseService.internal_error(
                    message=result.get("message", "Failed to reorder tracks")
                )
            return result

        @self.router.delete("/{playlist_id}/tracks")
        @handle_http_errors()
        async def delete_tracks(playlist_id: str, body: dict = Body(...), request: Request = None):
            """Delete tracks with state broadcasting."""
            logger.log(
                LogLevel.DEBUG,
                f"Deleting tracks from playlist {playlist_id}: {len(body.get('track_numbers', []))} tracks",
            )
            track_numbers = body.get("track_numbers")
            client_op_id = body.get("client_op_id")
            if not track_numbers or not isinstance(track_numbers, list):
                return UnifiedResponseService.bad_request(
                    message="track_numbers must be a non-empty list"
                )
            result = await self.playlist_controller.delete_tracks(
                playlist_id, track_numbers, client_op_id
            )
            return result

        # Upload routes with state broadcasting
        @self.router.post("/{playlist_id}/uploads/session", status_code=201)
        @handle_http_errors()
        async def init_upload_session(
            playlist_id: str, body: dict = Body(...), request: Request = None
        ):
            """Initialize chunked upload session."""
            filename = body.get("filename")
            file_size = body.get("file_size")
            chunk_size = body.get("chunk_size", 1024 * 1024)  # Default 1MB
            file_hash = body.get("file_hash")  # Optional
            if not filename or not file_size:
                return UnifiedResponseService.bad_request(
                    message="filename and file_size are required"
                )
            result = await self.upload_controller.init_upload_session(
                playlist_id, filename, file_size, chunk_size, file_hash
            )
            # Return standardized API response format
            return UnifiedResponseService.success(
                message="Upload session initialized successfully", data=result
            )

        @self.router.put("/{playlist_id}/uploads/{session_id}/chunks/{chunk_index}")
        @handle_http_errors()
        async def upload_chunk(
            playlist_id: str,
            session_id: str,
            chunk_index: int,
            file: UploadFile = File(...),
            request: Request = None,
        ):
            """Upload a file chunk."""
            result = await self.upload_controller.upload_chunk(
                playlist_id=playlist_id,
                session_id=session_id,
                chunk_index=chunk_index,
                chunk_data=await file.read(),
            )
            # Return standardized API response format
            return UnifiedResponseService.success(
                message="Chunk uploaded successfully", data=result
            )

        @self.router.post("/{playlist_id}/uploads/{session_id}/finalize")
        @handle_http_errors()
        async def finalize_upload(
            playlist_id: str,
            session_id: str,
            body: dict = Body(default={}),
            request: Request = None,
        ):
            """Finalize upload and broadcast track addition."""
            client_op_id = body.get("client_op_id")
            logger.log(
                LogLevel.INFO,
                f"Finalizing upload for session {session_id} in playlist {playlist_id}",
            )
            # Finalize upload via upload controller
            result = await self.upload_controller.finalize_upload(
                playlist_id=playlist_id,
                session_id=session_id,
                file_hash=body.get("file_hash"),
                metadata_override=body.get("metadata_override"),
            )
            logger.log(
                LogLevel.INFO,
                f"Upload controller finalize result: {result.get('status', 'unknown')}",
            )

            # Check if upload controller failed
            if result.get("status") != "success":
                logger.log(
                    LogLevel.ERROR,
                    f"Upload controller failed: {result.get('message', 'Unknown error')}",
                )
                return UnifiedResponseService.internal_error(
                    message=result.get("message", "Upload finalization failed"),
                    operation="finalize_upload",
                )

            # Upload successful, now integrate with playlist
            if result.get("track"):
                integration_result = await self.playlist_controller.handle_upload_complete(
                    playlist_id, result["track"], client_op_id
                )

                # Check if playlist integration failed
                if integration_result.get("status") != "success":
                    logger.log(
                        LogLevel.ERROR,
                        f"Playlist integration failed: {integration_result.get('message')}",
                    )
                    return UnifiedResponseService.internal_error(
                        message=integration_result.get(
                            "message", "Failed to integrate track into playlist"
                        ),
                        operation="finalize_upload",
                    )

                logger.log(
                    LogLevel.INFO, f"✅ Upload and playlist integration completed successfully"
                )

            # Return success response
            return UnifiedResponseService.success(
                message="Upload finalized and track added to playlist successfully", data=result
            )

        # Upload session status
        @self.router.get("/{playlist_id}/uploads/{session_id}")
        @handle_http_errors()
        async def get_upload_status(playlist_id: str, session_id: str):
            result = await self.upload_controller.get_session_status(session_id)
            # Return standardized API response format
            return UnifiedResponseService.success(
                message="Upload status retrieved successfully", data=result
            )

        # Playback control routes (remove legacy duplicate; keep authoritative one below)

        @self.router.post("/{playlist_id}/play/{track_number}")
        @handle_http_errors()
        async def play_track(playlist_id: str, track_number: int, audio=Depends(get_audio_service)):
            """Play a specific track."""
            result = await self.audio_controller.handle_playback_control("play")
            return result

        @self.router.post("/control")
        @handle_http_errors()
        async def control_playback(body: dict = Body(...), audio=Depends(get_audio_service)):
            """Control playback (play/pause/next/previous/stop)."""
            action = body.get("action")
            if not action:
                return UnifiedResponseService.bad_request(message="action is required")
            result = await self.audio_controller.handle_playback_control(action)
            return result

        # Start playlist playback (server-authoritative)
        @self.router.post("/{playlist_id}/start")
        @handle_http_errors()
        async def start_playlist(playlist_id: str, body: dict = Body(default={})):
            """Load and start a playlist, then broadcast player state."""
            client_op_id = body.get("client_op_id")
            # Start playlist using the playlist service and audio controller with detailed error handling
            # Use domain architecture playlist service
            from app.src.application.services.playlist_application_service import (
                playlist_app_service,
            )

            playlist_service = playlist_app_service
            audio = self.audio_controller.audio_service
            result = await playlist_service.start_playlist_with_details(playlist_id, audio)
            if result["success"]:
                logger.log(
                    LogLevel.INFO, f"🎵 Playlist UI démarrée via orchestrateur: {playlist_id}"
                )
                # Update AudioController state tracking after successful playlist start
                # Update controller state directly instead of using deprecated load_playlist()
                # Get the playlist data that was just started
                # Use same playlist service instance created above
                # playlist_service is already available from previous lines
                playlist_result = await playlist_service.get_playlist_use_case(playlist_id)
                playlist_data = (
                    playlist_result.get("playlist")
                    if playlist_result.get("status") == "success"
                    else None
                )
                if playlist_data:
                    # Convert dictionary to Playlist object for AudioController compatibility
                    from app.src.domain.data.models.playlist import Playlist
                    from app.src.domain.data.models.track import Track

                    # Create Track objects from dictionary data
                    tracks = []
                    if "tracks" in playlist_data:
                        for track_dict in playlist_data["tracks"]:
                            track = Track(
                                track_number=track_dict.get("track_number", 0),
                                title=track_dict.get("title", ""),
                                filename=track_dict.get("filename", ""),
                                file_path=track_dict.get("file_path", ""),
                                duration_ms=track_dict.get("duration_ms"),
                                artist=track_dict.get("artist"),
                                album=track_dict.get("album"),
                                id=track_dict.get("id"),
                            )
                            tracks.append(track)
                    # Create Playlist object
                    playlist_obj = Playlist(
                        name=playlist_data.get("title", playlist_data.get("name", "")),
                        tracks=tracks,
                        description=playlist_data.get("description"),
                        id=playlist_data.get("id"),
                        nfc_tag_id=playlist_data.get("nfc_tag_id"),
                    )
                    # Update AudioController internal state tracking (replaces deprecated load_playlist)
                    self.audio_controller._current_playlist_id = playlist_id
                    self.audio_controller._current_playlist = playlist_obj
                    self.audio_controller._current_track_index = 0
                    # CRITICAL FIX: Set internal playing state for seekbar progression
                    self.audio_controller._internal_playing_state = True
                    self.audio_controller._last_action = "playing"
                    # CRITICAL FIX: Start playback tracking for position calculation
                    self.audio_controller._start_playback_tracking()
                    logger.log(
                        LogLevel.INFO,
                        f"✅ AudioController state tracking updated for playlist: {playlist_id}",
                    )
                    logger.log(
                        LogLevel.INFO,
                        f"🎯 AudioController internal state set: "
                        f"_internal_playing_state=True, "
                        f"is_playing()={self.audio_controller.is_playing()}",
                    )
                    logger.log(
                        LogLevel.INFO,
                        f"🎯 Playback tracking started: "
                        f"_is_playing_tracked={getattr(self.audio_controller, '_is_playing_tracked', False)}",
                    )
                    # Start the TrackProgressService for auto-advance and position updates
                    if hasattr(self, "progress_service") and self.progress_service:
                        await self.progress_service.start()
                        logger.log(
                            LogLevel.INFO,
                            "🎵 TrackProgressService started for position tracking and auto-advance",
                        )
                else:
                    logger.log(
                        LogLevel.WARNING,
                        f"Could not retrieve playlist data for state tracking: {playlist_id}",
                    )

                # CRITICAL FIX: Broadcast player state after successful playlist start
                try:
                    # Debug: Log audio controller state before building player state
                    controller_status = await self.audio_controller.get_playback_status()
                    controller_playlist_info = self.audio_controller.get_current_playlist_info()
                    logger.log(LogLevel.INFO, f"🔍 AudioController status: {controller_status}")
                    logger.log(LogLevel.INFO, f"🔍 AudioController playlist info: {controller_playlist_info}")

                    current_player_state = await self.player_state_service.build_current_player_state()
                    player_data = current_player_state.model_dump()
                    logger.log(LogLevel.INFO, f"🔍 Built player state: {player_data}")

                    await self.state_manager.broadcast_state_change(
                        StateEventType.PLAYER_STATE,
                        player_data
                    )
                    logger.log(LogLevel.INFO, "✅ État du player diffusé après démarrage de playlist")
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"⚠️ Échec diffusion état player: {str(e)}")
                    import traceback
                    logger.log(LogLevel.ERROR, f"Stack trace: {traceback.format_exc()}")

                # Return HTTP response for successful playlist start
                return UnifiedResponseService.success(
                    message=f"Playlist '{playlist_data.get('title') if playlist_data else playlist_id}' started successfully",
                    data=result
                )
            else:
                # Handle failure case
                logger.log(LogLevel.ERROR, f"❌ Failed to start playlist: {result.get('message', 'Unknown error')}")
                return UnifiedResponseService.error(
                    message=result.get("message", "Failed to start playlist"),
                    error_type=result.get("error_type", "playlist_start_failed")
                )

        # NFC association routes (integrate with existing NFC system)
        @self.router.post("/nfc/{nfc_tag_id}/associate/{playlist_id}")
        @handle_http_errors()
        async def associate_nfc_tag(
            nfc_tag_id: str,
            playlist_id: str,
            body: dict = Body(default={}),
            request: Request = None,
        ):
            """Associate NFC tag with playlist."""
            client_op_id = body.get("client_op_id")
            # Execute NFC association
            # This would integrate with existing NFC service
            # For now, just update playlist with NFC tag ID
            result = await self.playlist_controller.update_playlist(
                playlist_id, {"nfc_tag_id": nfc_tag_id}, client_op_id
            )
            return result

        @self.router.delete("/nfc/{playlist_id}")
        @handle_http_errors()
        async def remove_nfc_association(
            playlist_id: str, body: dict = Body(default={}), request: Request = None
        ):
            """Remove NFC association from playlist."""
            client_op_id = body.get("client_op_id")
            result = await self.playlist_controller.update_playlist(
                playlist_id, {"nfc_tag_id": None}, client_op_id
            )
            return result

        @self.router.get("/nfc/{nfc_tag_id}")
        @handle_http_errors()
        async def get_nfc_playlist(nfc_tag_id: str):
            """Get playlist associated with NFC tag."""
            # This would query the database for playlist with matching nfc_tag_id
            # For now, return a placeholder implementation
            playlists = await self.playlist_controller.get_all_playlists()
            for playlist in playlists:
                if playlist.get("nfc_tag_id") == nfc_tag_id:
                    return {"playlist": playlist}
            return UnifiedResponseService.not_found(message="No playlist found for NFC tag")

        # Sync endpoint for manual state synchronization
        @self.router.post("/sync")
        @handle_http_errors()
        async def sync_playlists(request: Request = None):
            """Trigger playlist synchronization and broadcast current state."""
            # This could trigger filesystem sync or other sync operations
            # For now, just broadcast current playlists state
            playlists_data = await self.playlist_controller.get_all_playlists()
            await self.state_manager.broadcast_state_change(
                StateEventType.PLAYLISTS_SNAPSHOT, {"playlists": playlists_data}
            )
            return {
                "status": "success",
                "message": "Playlists synchronized and state broadcasted",
                "server_seq": self.state_manager.get_global_sequence(),
            }

        @self.router.post("/move-track")
        @handle_http_errors()
        async def move_track_between_playlists(body: dict = Body(...), request: Request = None):
            """Move a track from one playlist to another with state broadcasting."""
            source_playlist_id = body.get("source_playlist_id")
            target_playlist_id = body.get("target_playlist_id")
            track_number = body.get("track_number")
            target_position = body.get("target_position")
            client_op_id = body.get("client_op_id")
            if not source_playlist_id or not target_playlist_id or track_number is None:
                return UnifiedResponseService.bad_request(
                    message="source_playlist_id, target_playlist_id, and track_number are required"
                )
            result = await self.playlist_controller.move_track_between_playlists(
                source_playlist_id, target_playlist_id, track_number, target_position, client_op_id
            )
            return result

    async def _setup_controls_integration(self):
        """
        Setup physical controls integration with GPIO hardware.

        This method initializes the PhysicalControlsManager with real GPIO
        integration for buttons and rotary encoder.
        """
        try:
            if not hasattr(self, 'physical_controls_manager'):
                logger.log(LogLevel.WARNING, "No physical controls manager available")
                return

            # Initialize physical controls with GPIO
            success = await self.physical_controls_manager.initialize()
            if success:
                logger.log(
                    LogLevel.INFO,
                    "✅ Physical controls integration setup completed with GPIO"
                )
            else:
                logger.log(
                    LogLevel.WARNING,
                    "⚠️ Physical controls initialization failed - controls not available"
                )

        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"❌ Error setting up physical controls integration: {e}"
            )

    async def setup_controls_integration(self):
        """
        Public method to setup physical controls integration.

        This method provides a public interface for initializing physical controls
        and should be called by external code instead of the protected method.
        """
        await self._setup_controls_integration()

    def _setup_playback_subject_bridge(self):
        """
        PlaybackSubject bridge is no longer needed - state broadcasting is handled directly by:
        1. Player routes broadcasting state changes after control operations
        2. TrackProgressService for continuous progress updates
        3. Direct StateManager.broadcast_state_change() calls in route handlers

        This eliminates duplicate events and race conditions that occurred when both
        the bridge and direct route broadcasting were active simultaneously.
        """
        logger.log(
            LogLevel.INFO,
            "State broadcasting handled directly by routes and TrackProgressService - no bridge needed",
        )

    @handle_http_errors()
    async def cleanup_controls(self):
        """
        Cleanup physical controls integration.

        This method is called during application shutdown to properly
        disconnect physical controls and clean up GPIO resources.
        """
        try:
            if hasattr(self, 'physical_controls_manager') and self.physical_controls_manager:
                await self.physical_controls_manager.cleanup()
                logger.log(LogLevel.INFO, "✅ Physical controls cleanup completed")
            else:
                logger.log(LogLevel.DEBUG, "No physical controls manager to cleanup")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"❌ Error during physical controls cleanup: {e}")

    async def cleanup_background_tasks(self):
        """
        Cleanup background tasks during application shutdown.

        This method stops the TrackProgressService and StateManager cleanup tasks
        to ensure clean shutdown.
        """
        logger.log(LogLevel.INFO, "PlaylistRoutesState: Stopping background tasks...")

        # Stop TrackProgressService
        if hasattr(self, "progress_service") and self.progress_service:
            try:
                await self.progress_service.stop()
                logger.log(LogLevel.INFO, "✅ TrackProgressService stopped")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"❌ Error stopping TrackProgressService: {e}")

        # Stop StateManager cleanup task
        if hasattr(self, "state_manager") and self.state_manager:
            try:
                await self.state_manager.stop_cleanup_task()
                logger.log(LogLevel.INFO, "✅ StateManager cleanup task stopped")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"❌ Error stopping StateManager cleanup task: {e}")

        logger.log(LogLevel.INFO, "✅ PlaylistRoutesState background tasks cleanup completed")


# Global instance for backward compatibility - will be initialized by api_routes_state
playlist_routes_state = None
