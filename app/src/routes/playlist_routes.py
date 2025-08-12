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
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse
from socketio import AsyncServer

from app.src.dependencies import get_audio, get_config
from app.src.helpers.exceptions import InvalidFileError, ProcessingError
from app.src.module.controles import get_controles_manager
from app.src.module.controles.events.controles_events import ControlesEventType
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.chunked_upload_service import ChunkedUploadService
from app.src.services.playlist_service import PlaylistService
from app.src.services.upload_service import UploadService

logger = ImprovedLogger(__name__)


class PlaylistRoutes:
    """
    Registers the playlist-related API routes with the FastAPI app.
    """

    def __init__(self, app: FastAPI, socketio: AsyncServer):
        self.app = app
        self.router = APIRouter(prefix="/api/playlists", tags=["playlists"])
        # Store Socket.IO server for event emission
        self.socketio = socketio
        # Cache the audio instance to avoid repeated dependency resolution
        self._audio_instance = None
        # Initialize controls-related attributes
        self.controls_manager = None
        self.controls_subscription = None
        # Keep track of the current volume for rotary encoder adjustments
        self._current_volume = 50  # Default volume 50%
        # Initialize the chunked upload service
        self._chunked_upload_service = None
        self._register_routes()

    def register(self):
        """
        Register playlist-related API routes with the FastAPI app.
        """
        self.app.include_router(self.router)
        setattr(self.app, "playlist_routes", self)

    def _get_cached_audio(self, request):
        """
        Get cached audio instance or resolve it once and cache it.
        """
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
        """
        Set up integration with physical control devices if enabled.
        """
        try:

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
        """
        Clean up resources associated with physical controls.

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
        """
        Handle control events from physical inputs.

        Args:     event: The ControlesEvent to handle
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
        async def list_playlists(page: int = 1, page_size: int = 50):
            """
            Get all playlists with pagination support.
            """
            logger.log(
                LogLevel.INFO,
                "API /api/playlists/: Route called",
            )

            try:
                playlist_service = PlaylistService()
                playlists_data = playlist_service.get_all_playlists(
                    page=page, page_size=page_size
                )

                if playlists_data is None:
                    playlists_data = []

                logger.log(
                    LogLevel.INFO,
                    f"API /api/playlists/: Fetched {len(playlists_data)} playlists from service",
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
                    "API /api/playlists/: Returning JSONResponse with playlists",
                )
                return response

            except Exception as e:
                logger.log(
                    LogLevel.ERROR,
                    f"API /api/playlists/: Error creating response: {str(e)}",
                )
                error_data = {"playlists": [], "error": str(e)}
                return JSONResponse(content=error_data, status_code=500)

        @self.router.post("/", response_model=Dict[str, Any])
        async def create_playlist(body: dict = Body(...)):
            """
            Create a new playlist.
            """
            playlist_service = PlaylistService()
            title = body.get("title")
            if not isinstance(title, str) or not title.strip():
                raise HTTPException(
                    status_code=422, detail="Missing or invalid 'title' field"
                )
            created = playlist_service.create_playlist(title)
            return created

        @self.router.get("/{playlist_id}", response_model=Dict[str, Any])
        async def get_playlist(playlist_id: str):
            """
            Get a playlist by ID.
            """
            playlist_service = PlaylistService()
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return playlist

        @self.router.delete("/{playlist_id}", response_model=Dict[str, Any])
        async def delete_playlist(playlist_id: str):
            """
            Delete a playlist and its files.
            """
            playlist_service = PlaylistService()
            try:
                deleted = playlist_service.delete_playlist(playlist_id)
                return deleted
            except ValueError as exc:
                raise HTTPException(
                    status_code=404, detail=f"Playlist {playlist_id} not found"
                ) from exc

        @self.router.post("/{playlist_id}/upload", response_model=Dict[str, Any])
        # Socket.IO upload events: emit progress and completion
        async def upload_files(
            playlist_id: str,
            files: List[UploadFile] = File(...),
            config=Depends(get_config),
        ):
            """
            Upload files to a specific playlist.

            Handles file uploads for a playlist, with progress reporting (no websocket
            emit here).

            Returns:     Dict[str, Any]: Upload status and file metadata.
            """
            playlist_service = PlaylistService()
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:

                raise HTTPException(status_code=404, detail="Playlist not found")

            upload_service = UploadService(config)
            uploaded_files = []
            failed_files = []
            for idx, file in enumerate(files):
                try:
                    if not file.filename:
                        continue
                    filename, metadata = await upload_service.process_upload(
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
                    # Emit upload progress event
                    try:
                        progress = int((idx + 1) / len(files) * 100)
                        await self.socketio.emit(
                            "upload_progress",
                            {
                                "playlist_id": playlist_id,
                                "filename": filename,
                                "progress": progress,
                                "current": idx + 1,
                                "total": len(files),
                            },
                        )
                    except Exception as emit_progress_error:
                        logger.log(
                            LogLevel.ERROR,
                            f"Failed to emit upload_progress event: {str(emit_progress_error)}",
                        )
                    # Emit upload complete event
                    try:
                        await self.socketio.emit(
                            "upload_complete",
                            {
                                "playlist_id": playlist_id,
                                "filename": filename,
                                "metadata": metadata,
                            },
                        )
                    except Exception as emit_complete_error:
                        logger.log(
                            LogLevel.ERROR,
                            f"Failed to emit upload_complete event: {str(emit_complete_error)}",
                        )

                except (InvalidFileError, ProcessingError) as e:
                    error_msg = str(e)
                    failed_files.append({"filename": file.filename, "error": error_msg})
                    # Emit upload error event
                    try:
                        await self.socketio.emit(
                            "upload_error",
                            {
                                "playlist_id": playlist_id,
                                "filename": file.filename,
                                "error": error_msg,
                            },
                        )
                    except Exception as emit_error_error:
                        logger.log(
                            LogLevel.ERROR,
                            f"Failed to emit upload_error event: {str(emit_error_error)}",
                        )
                    continue
            if uploaded_files:
                playlist_service.save_playlist_file(playlist_id, playlist)
            response = {
                "status": "success" if uploaded_files else "error",
                "uploaded_files": uploaded_files,
            }
            if failed_files:
                response["failed_files"] = failed_files
                if not uploaded_files:
                    status_code = (
                        413
                        if any("too large" in f.get("error", "") for f in failed_files)
                        else 400
                    )
                    raise HTTPException(status_code=status_code, detail=response)
            return response

        # New routes for chunked uploads
        @self.router.post("/{playlist_id}/upload/init")
        async def create_upload_session(
            playlist_id: str,
            body: dict = Body(...),
            config=Depends(get_config),
        ):
            """
            Create a new chunked upload session for a specific playlist.

            Args:     playlist_id: ID of the playlist to upload files to.     body:
            Dictionary containing filename, total_chunks, and total_size.

            Returns:     Dict with session_id and status.
            """
            filename = body.get("filename")
            total_chunks = body.get("total_chunks")
            total_size = body.get("total_size")

            if not filename or total_chunks is None or total_size is None:
                raise HTTPException(
                    status_code=400,
                    detail="Missing required parameters: filename, total_chunks, total_size",
                )

            try:
                # Initialize chunked upload service if not already done
                if self._chunked_upload_service is None:
                    upload_service = UploadService(config)
                    self._chunked_upload_service = ChunkedUploadService(
                        config, upload_service
                    )

                session_id = self._chunked_upload_service.create_session(
                    filename, total_chunks, total_size
                )

                return {"status": "success", "session_id": session_id}

            except InvalidFileError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error creating upload session: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post("/{playlist_id}/upload/chunk")
        async def upload_chunk(
            playlist_id: str,
            session_id: str = Form(...),
            chunk_index: int = Form(...),
            file: UploadFile = File(...),
            config=Depends(get_config),
        ):
            """
            Upload a chunk of a file to a specific playlist.

            Args:     playlist_id: ID of the playlist.     session_id: Upload session
            identifier.     chunk_index: Index of the current chunk (0-based).
            file:
            The chunk data.

            Returns:
            Dict with status and progress information.
            """
            try:
                # Check if playlist exists
                playlist_service = PlaylistService()
                playlist = playlist_service.get_playlist_by_id(playlist_id)
                if not playlist:
                    raise HTTPException(status_code=404, detail="Playlist not found")

                # Initialize chunked upload service if not already done
                if self._chunked_upload_service is None:
                    upload_service = UploadService(config)
                    self._chunked_upload_service = ChunkedUploadService(
                        config, upload_service
                    )

                # Read chunk data
                chunk_data = await file.read()
                chunk_size = len(chunk_data)

                # Process the chunk
                result = await self._chunked_upload_service.process_chunk(
                    session_id, chunk_index, chunk_data, chunk_size
                )

                # Emit progress event via Socket.IO
                try:
                    await self.socketio.emit(
                        "upload_progress",
                        {
                            "playlist_id": playlist_id,
                            "session_id": session_id,
                            "filename": file.filename,
                            "chunk_index": chunk_index,
                            "progress": result["progress"],
                            "complete": result["complete"],
                        },
                    )
                except Exception as e:
                    logger.log(
                        LogLevel.ERROR,
                        f"Failed to emit upload_progress event: {str(e)}",
                    )

                return result

            except InvalidFileError as e:
                # Emit error event
                try:
                    await self.socketio.emit(
                        "upload_error",
                        {
                            "playlist_id": playlist_id,
                            "session_id": session_id,
                            "filename": file.filename if file else "unknown",
                            "error": str(e),
                        },
                    )
                except Exception as emit_error:
                    logger.log(
                        LogLevel.ERROR,
                        f"Failed to emit upload_error event: {str(emit_error)}",
                    )

                raise HTTPException(status_code=400, detail=str(e)) from e
            except ProcessingError as e:
                raise HTTPException(status_code=500, detail=str(e)) from e
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error processing chunk: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post("/{playlist_id}/upload/finalize")
        async def finalize_upload(
            playlist_id: str,
            body: dict = Body(...),
            config=Depends(get_config),
        ):
            """
            Finalize a chunked upload by assembling all chunks.

            Args:     playlist_id: ID of the playlist.     body: Dictionary containing
            session_id.

            Returns:     Dict with status and file metadata.
            """
            session_id = body.get("session_id")
            if not session_id:
                raise HTTPException(
                    status_code=400, detail="Missing session_id parameter"
                )

            try:
                # Check if playlist exists
                playlist_service = PlaylistService()
                playlist = playlist_service.get_playlist_by_id(playlist_id)
                if not playlist:
                    raise HTTPException(status_code=404, detail="Playlist not found")

                # Initialize chunked upload service if not already done
                if self._chunked_upload_service is None:
                    upload_service = UploadService(config)
                    self._chunked_upload_service = ChunkedUploadService(
                        config, upload_service
                    )

                # Finalize the upload
                filename, metadata = await self._chunked_upload_service.finalize_upload(
                    session_id, playlist["path"]
                )

                # Add the track to the playlist
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
                playlist_service.save_playlist_file(playlist_id, playlist)

                # Emit upload complete event
                try:
                    await self.socketio.emit(
                        "upload_complete",
                        {
                            "playlist_id": playlist_id,
                            "session_id": session_id,
                            "filename": filename,
                            "metadata": metadata,
                        },
                    )
                except Exception as e:
                    logger.log(
                        LogLevel.ERROR,
                        f"Failed to emit upload_complete event: {str(e)}",
                    )

                return {"status": "success", "filename": filename, "metadata": metadata}

            except InvalidFileError as e:
                # Emit error event
                try:
                    await self.socketio.emit(
                        "upload_error",
                        {
                            "playlist_id": playlist_id,
                            "session_id": session_id,
                            "error": str(e),
                        },
                    )
                except Exception as emit_error:
                    logger.log(
                        LogLevel.ERROR,
                        f"Failed to emit upload_error event: {str(emit_error)}",
                    )

                raise HTTPException(status_code=400, detail=str(e)) from e
            except ProcessingError as e:
                raise HTTPException(status_code=500, detail=str(e)) from e
            except (IOError, OSError) as e:
                # File system related errors
                logger.log(
                    LogLevel.ERROR,
                    f"File system error while finalizing upload: {str(e)}",
                )
                raise HTTPException(
                    status_code=500, detail=f"File system error: {str(e)}"
                ) from e
            except ValueError as e:
                # Data validation errors
                logger.log(
                    LogLevel.ERROR,
                    f"Validation error while finalizing upload: {str(e)}",
                )
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                # Fallback for truly unexpected errors
                logger.log(
                    LogLevel.ERROR, f"Unexpected error finalizing upload: {str(e)}"
                )
                raise HTTPException(
                    status_code=500, detail="An unexpected error occurred"
                ) from e

        @self.router.get("/uploads/session/{session_id}")
        async def get_upload_session_status(
            session_id: str,
            config=Depends(get_config),
        ):
            """
            Get the status of an upload session.

            Args:     session_id: Upload session identifier.

            Returns:     Dict with session status information.
            """
            try:
                # Initialize chunked upload service if not already done
                if self._chunked_upload_service is None:
                    upload_service = UploadService(config)
                    self._chunked_upload_service = ChunkedUploadService(
                        config, upload_service
                    )

                # Get session status
                status = self._chunked_upload_service.get_session_status(session_id)
                return {"status": "success", **status}

            except InvalidFileError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error getting session status: {str(e)}")
                raise HTTPException(status_code=500, detail="Server error") from e

        @self.router.post("/{playlist_id}/reorder", response_model=Dict[str, Any])
        async def reorder_tracks(playlist_id: str, body: dict = Body(...)):
            """
            Reorder tracks in a playlist.

            Args:     playlist_id (str): ID of the playlist to reorder.     body (dict):
            Dictionary containing the new track order.

            Returns:     Dict[str, Any]: Status of the reorder operation.
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
        async def delete_tracks(playlist_id: str, body: dict = Body(...)):
            """
            Delete multiple tracks from a playlist.
            """
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
        async def start_playlist(playlist_id: str, audio=Depends(get_audio)):
            """
            Start playing a specific playlist.
            """
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
            playlist_id: str, track_number: int, audio=Depends(get_audio)
        ):
            """
            Play a specific track from a playlist.
            """
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
            """
            Control the currently playing playlist with immediate response.

            Allows play, pause, next, previous, and stop actions for the current
            playlist.

            Returns:     Dict[str, Any]: Status and action performed.
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
