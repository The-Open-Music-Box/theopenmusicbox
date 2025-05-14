from typing import Dict, Any, Optional, List
import threading
import asyncio
import time
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class DownloadNotifier:
    def __init__(self, socketio, download_id: str):
        self.socketio = socketio
        self.download_id = download_id

    async def notify(self, status: str, **data):
        await self.socketio.emit('download_progress', {
            'download_id': self.download_id,
            'status': status,
            **data
        })

class PlaybackEvent:
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data

class PlaybackSubject:
    # Global static instance for direct reference
    _instance = None
    _lock = threading.RLock()
    _socketio = None

    @classmethod
    def set_socketio(cls, socketio):
        cls._socketio = socketio

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = PlaybackSubject()
            return cls._instance

    def __init__(self):
        self._last_status_event = None
        self._last_progress_event = None
        self._last_progress_emit_time = 0  # Used to throttle progress event emission frequency
        if PlaybackSubject._instance is not None and PlaybackSubject._instance is not self:
            raise RuntimeError("PlaybackSubject singleton instance already exists. Use get_instance().")
        with PlaybackSubject._lock:
            if PlaybackSubject._instance is None:
                PlaybackSubject._instance = self

    def notify_playback_status(self, status: str, playlist_info: Dict = None, track_info: Dict = None):
        """
        Emit a playback status event
        status: 'playing', 'paused', 'stopped'
        playlist_info: information about current playlist
        track_info: information about current track
        """
        try:
            event_data = {
                'status': status,
                'playlist': playlist_info,
                'current_track': track_info
            }
            event = PlaybackEvent('status', event_data)
            self._last_status_event = event

            # Emit directly via Socket.IO
            if PlaybackSubject._socketio:
                try:
                    # Emit via Socket.IO by creating an asyncio task
                    self._emit_socketio_event('playback_status', event_data)
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"[PlaybackSubject] Error emitting Socket.IO event: {e}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"[PlaybackSubject] Error in notify_playback_status: {e}")

    def notify_track_progress(self, elapsed: float, total: float, track_number: int, track_info: dict = None, playlist_info: dict = None, is_playing: bool = True):
        """
        Emit a track progress event with full info for the frontend
        elapsed: elapsed time in seconds
        total: total duration in seconds
        track_number: track number in playlist
        track_info: dict with track metadata (title, filename, duration, etc.)
        playlist_info: dict with playlist metadata (optional)
        is_playing: bool, if playback is active
        """
        try:
            event_data = {
                'track': track_info,
                'playlist': playlist_info,
                'current_time': elapsed,
                'duration': total,
                'is_playing': is_playing
            }
            event = PlaybackEvent('progress', event_data)
            self._last_progress_event = event

            # Emit directly via Socket.IO
            if PlaybackSubject._socketio:
                try:
                    # Emit via Socket.IO by creating an asyncio task
                    self._emit_socketio_event('track_progress', event_data)
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"[PlaybackSubject] Error emitting Socket.IO event: {e}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"[PlaybackSubject] Error in notify_track_progress: {e}")

    def get_last_status_event(self):
        return self._last_status_event

    def get_last_progress_event(self):
        return self._last_progress_event

    def _emit_socketio_event(self, event_name, event_data):
        """
        Emit a Socket.IO event in a fully non-blocking way.
        This implementation ensures we never block the main thread or event loop.
        """
        if not PlaybackSubject._socketio:
            return

        # Throttle progress events to reduce overhead
        if event_name == 'track_progress' and 'current_time' in event_data:
            current_time = time.time()
            last_progress_time = getattr(self, '_last_progress_emit_time', 0)
            if current_time - last_progress_time < 0.25:  # 250ms throttle
                return  # Ignore overly frequent updates
            self._last_progress_emit_time = current_time

        # Fire-and-forget approach: submit the task to a dedicated background thread
        def _background_emit():
            try:
                # Create a new event loop for this thread if needed
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Create and run the coroutine
                    async def _emit_async():
                        try:
                            await PlaybackSubject._socketio.emit(event_name, event_data)
                        except Exception as e:
                            logger.log(LogLevel.ERROR, f"[Socket.IO] Emit failed: {e}")
                    
                    # Run and close the loop
                    loop.run_until_complete(_emit_async())
                    loop.close()
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"[Socket.IO] Background emit error: {e}")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"[Socket.IO] Fatal background emit error: {e}")
        
        # Use a daemon thread that won't block application shutdown
        emit_thread = threading.Thread(target=_background_emit, daemon=True)
        emit_thread.start()
        # Don't wait for the thread to complete - immediately return
