# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Upload routes for handling file uploads to playlists.

This module contains all upload-related API routes including traditional
file uploads and chunked uploads with progress tracking via Socket.IO.
"""

from typing import List

from fastapi import APIRouter, Body, Depends, FastAPI, File, Form, HTTPException, UploadFile
from socketio import AsyncServer

from app.src.dependencies import get_config
from app.src.helpers.exceptions import InvalidFileError, ProcessingError
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.chunked_upload_service import ChunkedUploadService
from app.src.services.playlist_service import PlaylistService
from app.src.services.upload_service import UploadService

logger = ImprovedLogger(__name__)


class UploadRoutes:
    """Handles all upload-related API routes for playlists.
    
    Manages both traditional file uploads and chunked uploads with
    progress tracking and error handling via Socket.IO events.
    """

    def __init__(self, app: FastAPI, socketio: AsyncServer):
        """Initialize the UploadRoutes.
        
        Args:
            app: FastAPI application instance
            socketio: Socket.IO server for real-time events
        """
        self.app = app
        self.socketio = socketio
        self.router = APIRouter(prefix="/api/playlists", tags=["uploads"])
        self._chunked_upload_service = None
        self._register_routes()

    def register(self):
        """Register upload routes with the FastAPI application."""
        self.app.include_router(self.router)
        logger.log(LogLevel.INFO, "UploadRoutes: Upload routes registered successfully")

    def _get_chunked_upload_service(self, config):
        """Get or create the chunked upload service instance.
        
        Args:
            config: Application configuration
            
        Returns:
            ChunkedUploadService instance
        """
        if self._chunked_upload_service is None:
            upload_service = UploadService(config)
            self._chunked_upload_service = ChunkedUploadService(config, upload_service)
        return self._chunked_upload_service

    async def _emit_upload_progress(self, playlist_id: str, filename: str, 
                                  progress: int, current: int, total: int, 
                                  session_id: str = None):
        """Emit upload progress event via Socket.IO.
        
        Args:
            playlist_id: ID of the playlist
            filename: Name of the file being uploaded
            progress: Progress percentage (0-100)
            current: Current file/chunk number
            total: Total files/chunks
            session_id: Optional session ID for chunked uploads
        """
        try:
            event_data = {
                "playlist_id": playlist_id,
                "filename": filename,
                "progress": progress,
                "current": current,
                "total": total,
            }
            if session_id:
                event_data["session_id"] = session_id
                
            await self.socketio.emit("upload_progress", event_data)
        except (ConnectionError, IOError, RuntimeError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Failed to emit upload_progress event: {str(e)}",
            )

    async def _emit_upload_complete(self, playlist_id: str, filename: str, 
                                  metadata: dict, session_id: str = None):
        """Emit upload complete event via Socket.IO.
        
        Args:
            playlist_id: ID of the playlist
            filename: Name of the uploaded file
            metadata: File metadata
            session_id: Optional session ID for chunked uploads
        """
        try:
            event_data = {
                "playlist_id": playlist_id,
                "filename": filename,
                "metadata": metadata,
            }
            if session_id:
                event_data["session_id"] = session_id
                
            await self.socketio.emit("upload_complete", event_data)
        except (ConnectionError, IOError, RuntimeError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Failed to emit upload_complete event: {str(e)}",
            )

    async def _emit_upload_error(self, playlist_id: str, filename: str, 
                               error: str, session_id: str = None):
        """Emit upload error event via Socket.IO.
        
        Args:
            playlist_id: ID of the playlist
            filename: Name of the file that failed
            error: Error message
            session_id: Optional session ID for chunked uploads
        """
        try:
            event_data = {
                "playlist_id": playlist_id,
                "filename": filename,
                "error": error,
            }
            if session_id:
                event_data["session_id"] = session_id
                
            await self.socketio.emit("upload_error", event_data)
        except (ConnectionError, IOError, RuntimeError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Failed to emit upload_error event: {str(e)}",
            )

    def _register_routes(self):
        """Register all upload-related routes."""
        
        @self.router.post("/{playlist_id}/upload")
        async def upload_files(
            playlist_id: str,
            files: List[UploadFile] = File(...),
            config=Depends(get_config),
        ):
            """Upload files to a specific playlist using traditional upload.

            Handles file uploads for a playlist, with progress reporting via Socket.IO.

            Args:
                playlist_id: ID of the playlist to upload files to
                files: List of files to upload
                config: Application configuration

            Returns:
                Dict containing upload status and file metadata
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
                    progress = int((idx + 1) / len(files) * 100)
                    await self._emit_upload_progress(
                        playlist_id, filename, progress, idx + 1, len(files)
                    )
                    
                    # Emit upload complete event
                    await self._emit_upload_complete(playlist_id, filename, metadata)

                except (InvalidFileError, ProcessingError) as e:
                    error_msg = str(e)
                    failed_files.append({"filename": file.filename, "error": error_msg})
                    await self._emit_upload_error(playlist_id, file.filename, error_msg)
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

        @self.router.post("/{playlist_id}/upload/init")
        async def create_upload_session(
            playlist_id: str,
            body: dict = Body(...),
            config=Depends(get_config),
        ):
            """Create a new chunked upload session for a specific playlist.

            Args:
                playlist_id: ID of the playlist to upload files to
                body: Dictionary containing filename, total_chunks, and total_size

            Returns:
                Dict with session_id and status
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
                chunked_upload_service = self._get_chunked_upload_service(config)
                session_id = chunked_upload_service.create_session(
                    filename, total_chunks, total_size, playlist_id
                )
                return {"status": "success", "session_id": session_id}

            except InvalidFileError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            except (ValueError, TypeError, IOError, FileNotFoundError, PermissionError) as e:
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
            """Upload a chunk of a file to a specific playlist.

            Args:
                playlist_id: ID of the playlist
                session_id: Upload session identifier
                chunk_index: Index of the current chunk (0-based)
                file: The chunk data

            Returns:
                Dict with status and progress information
            """
            try:
                # Check if playlist exists
                playlist_service = PlaylistService()
                playlist = playlist_service.get_playlist_by_id(playlist_id)
                if not playlist:
                    raise HTTPException(status_code=404, detail="Playlist not found")

                chunked_upload_service = self._get_chunked_upload_service(config)

                # Read chunk data
                chunk_data = await file.read()
                chunk_size = len(chunk_data)

                # Process the chunk
                result = await chunked_upload_service.process_chunk(
                    session_id, chunk_index, chunk_data, chunk_size
                )

                # Emit progress event via Socket.IO
                await self._emit_upload_progress(
                    playlist_id, 
                    file.filename, 
                    result["progress"], 
                    chunk_index + 1, 
                    result.get("total_chunks", chunk_index + 1),
                    session_id
                )

                return result

            except InvalidFileError as e:
                await self._emit_upload_error(
                    playlist_id, 
                    file.filename if file else "unknown", 
                    str(e), 
                    session_id
                )
                raise HTTPException(status_code=400, detail=str(e)) from e
            except ProcessingError as e:
                raise HTTPException(status_code=500, detail=str(e)) from e
            except (ValueError, TypeError, IOError, FileNotFoundError, PermissionError, RuntimeError) as e:
                logger.log(LogLevel.ERROR, f"Error processing chunk: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.post("/{playlist_id}/upload/finalize")
        async def finalize_upload(
            playlist_id: str,
            body: dict = Body(...),
            config=Depends(get_config),
        ):
            """Finalize a chunked upload by assembling all chunks.

            Args:
                playlist_id: ID of the playlist
                body: Dictionary containing session_id

            Returns:
                Dict with status and file metadata
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

                chunked_upload_service = self._get_chunked_upload_service(config)

                # Finalize the upload
                filename, metadata = await chunked_upload_service.finalize_upload(
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
                await self._emit_upload_complete(playlist_id, filename, metadata, session_id)

                return {"status": "success", "filename": filename, "metadata": metadata}

            except InvalidFileError as e:
                await self._emit_upload_error(playlist_id, "unknown", str(e), session_id)
                raise HTTPException(status_code=400, detail=str(e)) from e
            except ProcessingError as e:
                raise HTTPException(status_code=500, detail=str(e)) from e
            except (IOError, OSError) as e:
                logger.log(
                    LogLevel.ERROR,
                    f"File system error while finalizing upload: {str(e)}",
                )
                raise HTTPException(
                    status_code=500, detail=f"File system error: {str(e)}"
                ) from e
            except ValueError as e:
                logger.log(
                    LogLevel.ERROR,
                    f"Validation error while finalizing upload: {str(e)}",
                )
                raise HTTPException(status_code=400, detail=str(e)) from e
            except (TypeError, FileNotFoundError, PermissionError, RuntimeError) as e:
                logger.log(LogLevel.ERROR, f"Error finalizing upload: {str(e)}")
                raise HTTPException(status_code=500, detail="Server error") from e

        @self.router.get("/uploads/session/{session_id}")
        async def get_upload_session_status(
            session_id: str,
            config=Depends(get_config),
        ):
            """Get the status of an upload session.

            Args:
                session_id: Upload session identifier

            Returns:
                Dict with session status information
            """
            try:
                chunked_upload_service = self._get_chunked_upload_service(config)
                status = chunked_upload_service.get_session_status(session_id)
                return {"status": "success", **status}

            except InvalidFileError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            except (ValueError, TypeError, IOError, FileNotFoundError, PermissionError) as e:
                logger.log(LogLevel.ERROR, f"Error getting session status: {str(e)}")
                raise HTTPException(status_code=500, detail="Server error") from e
