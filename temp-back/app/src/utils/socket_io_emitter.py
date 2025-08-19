# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Centralized Socket.IO event emission utility.

This module provides a unified interface for emitting Socket.IO events
across the application, eliminating code duplication and ensuring
consistent event handling patterns.
"""

from typing import Dict, Any, Optional
from socketio import AsyncServer
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class SocketIOEmitter:
    """Centralized utility for Socket.IO event emissions."""
    
    def __init__(self, socketio: Optional[AsyncServer] = None):
        """
        Initialize the Socket.IO emitter.
        
        Args:
            socketio: AsyncServer instance for Socket.IO communications
        """
        self.socketio = socketio
    
    async def emit_upload_progress(self, playlist_id: str, current: int, total: int, 
                                 filename: str, status: str = 'processing') -> None:
        """
        Emit upload progress event.
        
        Args:
            playlist_id: ID of the playlist being uploaded to
            current: Current file number being processed
            total: Total number of files
            filename: Name of the current file
            status: Status of the upload ('processing', 'completed', 'error')
        """
        if not self.socketio:
            return
            
        try:
            await self.socketio.emit('upload_progress', {
                'playlist_id': playlist_id,
                'current': current,
                'total': total,
                'filename': filename,
                'status': status
            })
            
            logger.log(LogLevel.DEBUG, f"Emitted upload_progress: {filename} ({current}/{total})")
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to emit upload_progress event: {str(e)}")
    
    async def emit_upload_complete(self, playlist_id: str, total_files: int, 
                                 results: list) -> None:
        """
        Emit upload completion event.
        
        Args:
            playlist_id: ID of the playlist
            total_files: Total number of files processed
            results: List of upload results
        """
        if not self.socketio:
            return
            
        try:
            await self.socketio.emit('upload_complete', {
                'playlist_id': playlist_id,
                'total_files': total_files,
                'results': results
            })
            
            logger.log(LogLevel.INFO, f"Emitted upload_complete for playlist {playlist_id}")
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to emit upload_complete event: {str(e)}")
    
    async def emit_upload_error(self, playlist_id: str, filename: Optional[str] = None, 
                              error: str = None, session_id: Optional[str] = None) -> None:
        """
        Emit upload error event.
        
        Args:
            playlist_id: ID of the playlist
            filename: Name of the file that caused the error (optional)
            error: Error message
            session_id: Upload session ID (for chunked uploads)
        """
        if not self.socketio:
            return
            
        try:
            event_data = {
                'playlist_id': playlist_id,
                'error': error
            }
            
            if filename:
                event_data['filename'] = filename
            if session_id:
                event_data['session_id'] = session_id
                
            await self.socketio.emit('upload_error', event_data)
            
            logger.log(LogLevel.WARNING, f"Emitted upload_error for playlist {playlist_id}: {error}")
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to emit upload_error event: {str(e)}")
    
    async def emit_chunk_progress(self, playlist_id: str, session_id: str, 
                                chunk_index: int, progress: Dict[str, Any]) -> None:
        """
        Emit chunk upload progress event.
        
        Args:
            playlist_id: ID of the playlist
            session_id: Upload session ID
            chunk_index: Index of the chunk
            progress: Progress information
        """
        if not self.socketio:
            return
            
        try:
            await self.socketio.emit('chunk_progress', {
                'playlist_id': playlist_id,
                'session_id': session_id,
                'chunk_index': chunk_index,
                'progress': progress
            })
            
            logger.log(LogLevel.DEBUG, f"Emitted chunk_progress: session {session_id}, chunk {chunk_index}")
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to emit chunk_progress event: {str(e)}")
    
    async def emit_chunk_error(self, playlist_id: str, session_id: str, 
                             chunk_index: int, error: str) -> None:
        """
        Emit chunk upload error event.
        
        Args:
            playlist_id: ID of the playlist
            session_id: Upload session ID
            chunk_index: Index of the chunk that failed
            error: Error message
        """
        if not self.socketio:
            return
            
        try:
            await self.socketio.emit('chunk_error', {
                'playlist_id': playlist_id,
                'session_id': session_id,
                'chunk_index': chunk_index,
                'error': error
            })
            
            logger.log(LogLevel.WARNING, f"Emitted chunk_error: session {session_id}, chunk {chunk_index}")
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to emit chunk_error event: {str(e)}")
    
    async def emit_upload_finalized(self, playlist_id: str, session_id: str, 
                                  result: Dict[str, Any]) -> None:
        """
        Emit upload finalization event.
        
        Args:
            playlist_id: ID of the playlist
            session_id: Upload session ID
            result: Finalization result
        """
        if not self.socketio:
            return
            
        try:
            await self.socketio.emit('upload_finalized', {
                'playlist_id': playlist_id,
                'session_id': session_id,
                'result': result
            })
            
            logger.log(LogLevel.INFO, f"Emitted upload_finalized for session {session_id}")
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to emit upload_finalized event: {str(e)}")
    
    async def emit_playback_status(self, status: str, track_info: Optional[Dict[str, Any]] = None,
                                 playlist_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Emit playback status event.
        
        Args:
            status: Playback status ('playing', 'paused', 'stopped', etc.)
            track_info: Current track information (optional)
            playlist_info: Current playlist information (optional)
        """
        if not self.socketio:
            return
            
        try:
            event_data = {'status': status}
            
            if track_info:
                event_data['track'] = track_info
            if playlist_info:
                event_data['playlist'] = playlist_info
                
            await self.socketio.emit('playback_status', event_data)
            
            logger.log(LogLevel.DEBUG, f"Emitted playback_status: {status}")
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to emit playback_status event: {str(e)}")
    
    async def emit_custom_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """
        Emit a custom Socket.IO event.
        
        Args:
            event_name: Name of the event to emit
            data: Event data
        """
        if not self.socketio:
            return
            
        try:
            await self.socketio.emit(event_name, data)
            
            logger.log(LogLevel.DEBUG, f"Emitted custom event: {event_name}")
            
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to emit {event_name} event: {str(e)}")
    
    def set_socketio(self, socketio: AsyncServer) -> None:
        """
        Set or update the Socket.IO server instance.
        
        Args:
            socketio: AsyncServer instance
        """
        self.socketio = socketio
        logger.log(LogLevel.INFO, "Socket.IO server instance updated")


# Global instance for easy access
_socket_emitter: Optional[SocketIOEmitter] = None


def get_socket_emitter() -> SocketIOEmitter:
    """
    Get the global Socket.IO emitter instance.
    
    Returns:
        SocketIOEmitter instance
    """
    global _socket_emitter
    if _socket_emitter is None:
        _socket_emitter = SocketIOEmitter()
    return _socket_emitter


def initialize_socket_emitter(socketio: AsyncServer) -> SocketIOEmitter:
    """
    Initialize the global Socket.IO emitter with a server instance.
    
    Args:
        socketio: AsyncServer instance
        
    Returns:
        Initialized SocketIOEmitter instance
    """
    global _socket_emitter
    _socket_emitter = SocketIOEmitter(socketio)
    return _socket_emitter
