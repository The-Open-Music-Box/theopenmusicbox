# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    Body,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)

from app.src.dependencies import get_audio, get_config
from app.src.helpers.exceptions import InvalidFileError, ProcessingError

# Import the controls event types
from app.src.module.controles.events.controles_events import ControlesEventType
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.playlist_service import PlaylistService
from app.src.services.upload_service import UploadService

logger = ImprovedLogger(__name__)


class PlaylistRoutes:
    """Registers the playlist-related API routes with the FastAPI app."""

    def __init__(self, app: FastAPI):
        self.app = app
        self.router = APIRouter(prefix="/api/playlists", tags=["playlists"])
        # Cache the audio instance to avoid repeated dependency resolution
        self._audio_instance = None
        # Initialize controls-related attributes
        self.controls_manager = None
        self.controls_subscription = None
        # Keep track of the current volume for rotary encoder adjustments
        self._current_volume = 50  # Default volume 50%
        self._register_routes()

    def register(self):
        """Register playlist-related API routes with the FastAPI app."""
        @self.app.get("/api/playlists")
        async def get_playlists_direct(
            page: int = 1, page_size: int = 50, config=Depends(get_config)
        ):
            from fastapi.responses import JSONResponse

            logger.log(LogLevel.INFO, "DIRECT API /api/playlists: Route called")

            try:
                playlist_service = PlaylistService()
                playlists_data = playlist_service.get_all_playlists(
                    page=page, page_size=page_size
                )

                if playlists_data is None:
                    playlists_data = []

                logger.log(
                    LogLevel.INFO,
                    f"DIRECT API /api/playlists: Fetched {len(playlists_data)} playlists from service",
                )

                data = {"playlists": playlists_data}

                response = JSONResponse(
                    content=data,
                    status_code=200,
                )

                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                logger.log(
                    LogLevel.INFO,
                    "DIRECT API /api/playlists: Returning JSONResponse with real playlists",
                )
                return response

            except Exception as e:
                logger.log(
                    LogLevel.ERROR,
                    f"DIRECT API /api/playlists: Error creating response: {str(e)}",
                )
                error_data = {"playlists": [], "error": str(e)}
                return JSONResponse(content=error_data, status_code=500)

        self.app.include_router(self.router)

        setattr(self.app, "playlist_routes", self)

    def _get_cached_audio(self, request):
        """Get cached audio instance or resolve it once and cache it."""
        if self._audio_instance is not None:
            return self._audio_instance

        if request is None:
            if hasattr(self, "app") and hasattr(self.app, "container"):
                container = self.app.container
                if hasattr(container, "audio"):
                    self._audio_instance = container.audio
                    logger.log(
                        LogLevel.DEBUG,
                        "Retrieved audio instance from app.container for control event",
                    )
        else:
            container = getattr(request.app, "container", None)
            if container and hasattr(container, "audio"):
                self._audio_instance = container.audio

        return self._audio_instance

    def _setup_controls_integration(self):
        """Set up integration with physical control devices if enabled."""
        try:
            from app.src.module.controles import get_controles_manager

            self.controls_manager = get_controles_manager()

            if (
                self.controls_manager
                and self.controls_manager.initialize()
                and self.controls_manager.start()
            ):
                logger.log(LogLevel.INFO, "Controls manager started successfully")

                self.controls_subscription = (
                    self.controls_manager.event_observable.subscribe(
                        self._handle_control_event,
                        on_error=lambda e: logger.log(
                            LogLevel.ERROR, f"Error in control event handling: {str(e)}"
                        ),
                    )
                )
                logger.log(LogLevel.INFO, "Subscribed to physical control events")
            else:
                logger.log(
                    LogLevel.WARNING,
                    "Failed to start controls manager or it is not available",
                )
        except Exception as e:
            logger.log(
                LogLevel.ERROR, f"Failed to set up controls integration: {str(e)}"
            )

    def _cleanup_controls(self):
        """Clean up resources associated with physical controls.

        Unsubscribes from control events and releases resources.
        """
        try:
            if self.controls_subscription:
                self.controls_subscription.dispose()
                self.controls_subscription = None
                logger.log(LogLevel.INFO, "Unsubscribed from physical control events")

            if self.controls_manager:
                self.controls_manager.stop()
                self.controls_manager = None
                logger.log(LogLevel.INFO, "Controls manager stopped successfully")
        except Exception as e:
            logger.log(
                LogLevel.ERROR, f"Error while cleaning up controls resources: {str(e)}"
            )

    def _handle_control_event(self, event):
        """Handle control events from physical inputs.

        Args:
            event: The ControlesEvent to handle
        """
        audio_player = self._get_cached_audio(None)
        if not audio_player:
            logger.log(
                LogLevel.WARNING,
                "Cannot handle control event: No audio player available.",
            )
            return

        logger.log(
            LogLevel.INFO,
            f"✓ Received control event: {event.event_type.name} from {event.source}",
        )

        try:
            if event.event_type == ControlesEventType.PLAY_PAUSE:
                if self._audio_instance.is_playing:
                    logger.log(LogLevel.INFO, "✓ Control action: Pausing playback")
                    self._audio_instance.pause()
                else:
                    logger.log(LogLevel.INFO, "✓ Control action: Resuming playback")
                    self._audio_instance.resume()

            elif event.event_type == ControlesEventType.VOLUME_DOWN:
                new_volume = min(self._current_volume + 5, 100)
                logger.log(
                    LogLevel.INFO,
                    f"✓ Control action: Increasing volume from {self._current_volume}% to {new_volume}%",
                )
                self._audio_instance.set_volume(new_volume)
                self._current_volume = new_volume

            elif (
                event.event_type == ControlesEventType.VOLUME_UP
            ):  # Actually counter-clockwise rotation
                new_volume = max(self._current_volume - 5, 0)
                logger.log(
                    LogLevel.INFO,
                    f"✓ Control action: Decreasing volume from {self._current_volume}% to {new_volume}%",
                )
                self._audio_instance.set_volume(new_volume)
                self._current_volume = new_volume

            elif event.event_type == ControlesEventType.NEXT_TRACK:
                logger.log(LogLevel.INFO, "✓ Control action: Skipping to next track")
                self._audio_instance.next_track()

            elif event.event_type == ControlesEventType.PREVIOUS_TRACK:
                logger.log(LogLevel.INFO, "✓ Control action: Going to previous track")
                self._audio_instance.previous_track()

            else:
                logger.log(
                    LogLevel.WARNING,
                    f"Unhandled control event type: {event.event_type.name}",
                )

        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"✗ Error handling control event {event.event_type.name}: {str(e)}",
            )

    def _register_routes(self):

        @self.router.get("/")
        async def list_playlists(
            page: int = 1, page_size: int = 50, config=Depends(get_config)
        ):
            """Get all playlists with pagination support."""
            import json

            from fastapi.responses import JSONResponse

            logger.log(
                LogLevel.INFO,
                "API /api/playlists: Route called with ultra-direct JSON response",
            )

            try:
                data = {"playlists": []}

                json_str = json.dumps(data)
                logger.log(
                    LogLevel.DEBUG, f"API /api/playlists: JSON string: {json_str}"
                )

                response = JSONResponse(
                    content=data,
                    status_code=200,
                )

                response.headers["Cache-Control"] = (
                    "no-cache, no-store, must-revalidate"
                )
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

                logger.log(
                    LogLevel.INFO,
                    "API /api/playlists: Returning JSONResponse with headers",
                )
                return response

            except Exception as e:
                logger.log(
                    LogLevel.ERROR,
                    f"API /api/playlists: Error creating response: {str(e)}",
                )
                error_data = {"playlists": [], "error": str(e)}
                return JSONResponse(content=error_data, status_code=500)

        @self.router.post("/", response_model=Dict[str, Any])
        async def create_playlist(body: dict = Body(...), config=Depends(get_config)):
            """Create a new playlist."""
            playlist_service = PlaylistService()
            title = body.get("title")
            if not isinstance(title, str) or not title.strip():
                raise HTTPException(
                    status_code=422, detail="Missing or invalid 'title' field"
                )
            created = playlist_service.create_playlist(title)
            return created

        @self.router.get("/{playlist_id}", response_model=Dict[str, Any])
        async def get_playlist(playlist_id: str, config=Depends(get_config)):
            """Get a playlist by ID."""
            playlist_service = PlaylistService()
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return playlist

        @self.router.delete("/{playlist_id}", response_model=Dict[str, Any])
        async def delete_playlist(playlist_id: str, config=Depends(get_config)):
            """Delete a playlist and its files."""
            playlist_service = PlaylistService()
            try:
                deleted = playlist_service.delete_playlist(playlist_id)
                return deleted
            except ValueError:
                raise HTTPException(
                    status_code=404, detail=f"Playlist {playlist_id} not found"
                )

        @self.router.post("/{playlist_id}/upload", response_model=Dict[str, Any])
        async def upload_files(
            playlist_id: str,
            files: List[UploadFile] = File(...),
            config=Depends(get_config),
        ):
            """Upload files to a specific playlist.

            Handles file uploads for a playlist, with progress reporting (no websocket emit here).

            Returns:
                Dict[str, Any]: Upload status and file metadata.

            """
            playlist_service = PlaylistService()
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            upload_service = UploadService(config.upload_folder)
            uploaded_files = []
            failed_files = []
            for file in files:
                try:
                    if not file.filename:
                        continue
                    filename, metadata = upload_service.process_upload(
                        file, playlist["path"]
                    )
                    track = {
                        "number": len(playlist["tracks"]) + 1,
                        "title": metadata["title"],
                        "artist": metadata["artist"],
                        "album": metadata["album"],
                        "duration": metadata["duration"],
                        "filename": filename,
                        "play_counter": 0,
                    }
                    playlist["tracks"].append(track)
                    uploaded_files.append({"filename": filename, "metadata": metadata})
                except (InvalidFileError, ProcessingError) as e:
                    failed_files.append({"filename": file.filename, "error": str(e)})
                    continue
            if uploaded_files:
                playlist_service.save_playlist_file()
            response = {
                "status": "success" if uploaded_files else "error",
                "uploaded_files": uploaded_files,
            }
            if failed_files:
                response["failed_files"] = failed_files
                if not uploaded_files:
                    raise HTTPException(status_code=400, detail=response)
            return response

        @self.router.post("/{playlist_id}/reorder", response_model=Dict[str, Any])
        async def reorder_tracks(
            playlist_id: str, body: dict = Body(...), config=Depends(get_config)
        ):
            """Reorder tracks in a playlist.

            Args:
                playlist_id (str): ID of the playlist to reorder.
                body (dict): Dictionary containing the new track order.

            Returns:
                Dict[str, Any]: Status of the reorder operation.

            """
            order = body.get("order", [])
            if not order or not isinstance(order, list):
                raise HTTPException(status_code=400, detail="Invalid order")
            playlist_service = PlaylistService()
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            success = playlist_service.reorder_tracks(playlist_id, order)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to reorder tracks")
            return {"status": "success"}

        @self.router.delete("/{playlist_id}/tracks", response_model=Dict[str, Any])
        async def delete_tracks(
            playlist_id: str, body: dict = Body(...), config=Depends(get_config)
        ):
            """Delete multiple tracks from a playlist."""
            track_numbers = body.get("tracks", [])
            if not track_numbers or not isinstance(track_numbers, list):
                raise HTTPException(status_code=400, detail="Invalid track numbers")
            playlist_service = PlaylistService()
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            success = playlist_service.delete_tracks(playlist_id, track_numbers)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to delete tracks")
            return {"status": "success"}

        @self.router.post("/{playlist_id}/start", response_model=Dict[str, Any])
        async def start_playlist(
            playlist_id: str, config=Depends(get_config), audio=Depends(get_audio)
        ):
            """Start playing a specific playlist."""
            if not audio:
                raise HTTPException(
                    status_code=503, detail="Audio system not available"
                )
            playlist_service = PlaylistService()
            success = playlist_service.start_playlist(playlist_id, audio)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to start playlist")
            return {"status": "success"}

        @self.router.post(
            "/{playlist_id}/play/{track_number}", response_model=Dict[str, Any]
        )
        async def play_track(
            playlist_id: str,
            track_number: int,
            config=Depends(get_config),
            audio=Depends(get_audio),
        ):
            """Play a specific track from a playlist."""
            if not audio:
                raise HTTPException(
                    status_code=503, detail="Audio system not available"
                )
            playlist_service = PlaylistService()
            success = playlist_service.play_track(playlist_id, track_number, audio)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to play track")
            return {"status": "success"}

        @self.router.post("/control", response_model=Dict[str, Any])
        async def control_playlist(
            request: Request, action: str = Body(..., embed=True)
        ):
            """Control the currently playing playlist with immediate response.

            Allows play, pause, next, previous, and stop actions for the current playlist.

            Returns:
                Dict[str, Any]: Status and action performed.

            """
            audio = self._get_cached_audio(request)

            if not audio:
                raise HTTPException(
                    status_code=503, detail="Audio system not available"
                )

            actions = {
                "play": audio.resume,
                "resume": audio.resume,
                "pause": audio.pause,
                "next": audio.next_track,
                "previous": audio.previous_track,
                "stop": audio.stop,
            }

            if action not in actions:
                raise HTTPException(status_code=400, detail="Invalid action")

            action_func = actions[action]
            action_func()

            return {"status": "success", "action": action}

