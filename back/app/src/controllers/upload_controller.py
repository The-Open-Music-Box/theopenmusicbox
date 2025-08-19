# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Upload controller for handling file upload business logic.

This controller extracts upload-related business logic from route handlers
and provides a clean interface for upload operations.
"""

from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from socketio import AsyncServer

from app.src.core.service_container import ServiceContainer
from app.src.helpers.error_handling import ErrorHandler
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.upload_service import UploadService
from app.src.services.chunked_upload_service import ChunkedUploadService

logger = ImprovedLogger(__name__)


class UploadController:
    """
    Controller for upload business logic.
    
    Handles file upload operations by coordinating between upload services
    and providing progress tracking via Socket.IO.
    """

    def __init__(self, service_container: Optional[ServiceContainer] = None, socketio: Optional[AsyncServer] = None):
        """
        Initialize the UploadController.
        
        Args:
            service_container: Optional service container for dependency injection.
            socketio: Optional Socket.IO server for progress events.
        """
        self.service_container = service_container or ServiceContainer()
        self.socketio = socketio
        self.config = self.service_container.config
        self.upload_service = UploadService(self.config)
        self.chunked_upload_service = ChunkedUploadService(self.config, self.upload_service)
        self.error_handler = ErrorHandler()

    async def upload_files(self, playlist_id: str, files: List[UploadFile], config) -> Dict[str, Any]:
        """
        Upload multiple files to a playlist.
        
        Args:
            playlist_id: The playlist ID.
            files: List of uploaded files.
            config: Configuration object.
            
        Returns:
            Upload results.
        """
        try:
            results = []
            total_files = len(files)
            
            for i, file in enumerate(files):
                try:
                    # Emit progress via Socket.IO
                    if self.socketio:
                        await self.socketio.emit('upload_progress', {
                            'playlist_id': playlist_id,
                            'current': i + 1,
                            'total': total_files,
                            'filename': file.filename,
                            'status': 'processing'
                        })
                    
                    # Process the file
                    result = await self.upload_service.process_uploaded_file(
                        file, playlist_id, config
                    )
                    results.append(result)
                    
                    # Emit success for this file
                    if self.socketio:
                        await self.socketio.emit('upload_progress', {
                            'playlist_id': playlist_id,
                            'current': i + 1,
                            'total': total_files,
                            'filename': file.filename,
                            'status': 'completed'
                        })
                        
                except Exception as file_error:
                    logger.log(LogLevel.ERROR, f"Error processing file {file.filename}: {str(file_error)}")
                    
                    # Emit error for this file
                    if self.socketio:
                        await self.socketio.emit('upload_error', {
                            'playlist_id': playlist_id,
                            'filename': file.filename,
                            'error': str(file_error)
                        })
                    
                    results.append({
                        'filename': file.filename,
                        'status': 'error',
                        'error': str(file_error)
                    })
            
            # Emit completion
            if self.socketio:
                await self.socketio.emit('upload_complete', {
                    'playlist_id': playlist_id,
                    'total_files': total_files,
                    'results': results
                })
            
            logger.log(LogLevel.INFO, f"Uploaded {len(files)} files to playlist {playlist_id}")
            return {"results": results}
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error uploading files to playlist {playlist_id}: {str(e)}")
            
            if self.socketio:
                await self.socketio.emit('upload_error', {
                    'playlist_id': playlist_id,
                    'error': str(e)
                })
            raise

    async def create_upload_session(self, playlist_id: str, filename: str, file_size: int, config) -> Dict[str, Any]:
        """
        Create a chunked upload session.
        
        Args:
            playlist_id: The playlist ID.
            filename: Name of the file to upload.
            file_size: Size of the file in bytes.
            config: Configuration object.
            
        Returns:
            Session information.
        """
        try:
            session = await self.chunked_upload_service.create_session(
                playlist_id, filename, file_size, config
            )
            
            logger.log(LogLevel.INFO, f"Created upload session {session['session_id']} for {filename}")
            return session
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error creating upload session for {filename}: {str(e)}")
            raise

    async def upload_chunk(self, playlist_id: str, session_id: str, chunk_index: int, 
                          chunk_data: bytes, config) -> Dict[str, Any]:
        """
        Upload a file chunk.
        
        Args:
            playlist_id: The playlist ID.
            session_id: Upload session ID.
            chunk_index: Index of the chunk.
            chunk_data: Binary chunk data.
            config: Configuration object.
            
        Returns:
            Upload status.
        """
        try:
            result = await self.chunked_upload_service.upload_chunk(
                session_id, chunk_index, chunk_data, config
            )
            
            # Emit progress via Socket.IO
            if self.socketio and result.get('progress'):
                await self.socketio.emit('chunk_progress', {
                    'playlist_id': playlist_id,
                    'session_id': session_id,
                    'chunk_index': chunk_index,
                    'progress': result['progress']
                })
            
            return result
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error uploading chunk {chunk_index} for session {session_id}: {str(e)}")
            
            if self.socketio:
                await self.socketio.emit('chunk_error', {
                    'playlist_id': playlist_id,
                    'session_id': session_id,
                    'chunk_index': chunk_index,
                    'error': str(e)
                })
            raise

    async def finalize_upload(self, playlist_id: str, session_id: str, config) -> Dict[str, Any]:
        """
        Finalize a chunked upload.
        
        Args:
            playlist_id: The playlist ID.
            session_id: Upload session ID.
            config: Configuration object.
            
        Returns:
            Finalization result.
        """
        try:
            result = await self.chunked_upload_service.finalize_upload(
                session_id, playlist_id, config
            )
            
            # Emit completion via Socket.IO
            if self.socketio:
                await self.socketio.emit('upload_finalized', {
                    'playlist_id': playlist_id,
                    'session_id': session_id,
                    'result': result
                })
            
            logger.log(LogLevel.INFO, f"Finalized upload session {session_id} for playlist {playlist_id}")
            return result
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error finalizing upload session {session_id}: {str(e)}")
            
            if self.socketio:
                await self.socketio.emit('upload_error', {
                    'playlist_id': playlist_id,
                    'session_id': session_id,
                    'error': str(e)
                })
            raise

    async def get_upload_session_status(self, session_id: str, config) -> Dict[str, Any]:
        """
        Get the status of an upload session.
        
        Args:
            session_id: Upload session ID.
            config: Configuration object.
            
        Returns:
            Session status.
        """
        try:
            status = await self.chunked_upload_service.get_session_status(session_id, config)
            return status
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error getting status for upload session {session_id}: {str(e)}")
            raise

    def cleanup_expired_sessions(self, config) -> Dict[str, Any]:
        """
        Clean up expired upload sessions.
        
        Args:
            config: Configuration object.
            
        Returns:
            Cleanup statistics.
        """
        try:
            stats = self.chunked_upload_service.cleanup_expired_sessions(config)
            logger.log(LogLevel.INFO, f"Cleaned up expired upload sessions", extra=stats)
            return {"status": "success", "stats": stats}
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error cleaning up expired sessions: {str(e)}")
            raise
