from typing import Dict, Any
import threading
import asyncio
import time
from rx.subject import Subject
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class DownloadNotifier:
    def __init__(self, socketio, download_id: str):
        self.socketio = socketio
        self.download_id = download_id

    def notify(self, status: str, **data):
        self.socketio.emit('download_progress', {
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
        # RxPy subjects - kept for backward compatibility with legacy components
        # Direct Socket.IO communication is now the primary method
        self._status_subject = Subject()
        self._progress_subject = Subject()
        self._last_status_event = None
        self._last_progress_event = None
        self._last_progress_emit_time = 0  # Used to throttle progress event emission frequency
        # Fix for infinite recursion: only set _instance if it is None and not self
        if PlaybackSubject._instance is not None and PlaybackSubject._instance is not self:
            # Prevent attempting to create a new instance if one already exists
            raise RuntimeError("PlaybackSubject singleton instance already exists. Use get_instance().")
        with PlaybackSubject._lock:
            if PlaybackSubject._instance is None:
                PlaybackSubject._instance = self


    @property
    def status_stream(self) -> Subject:
        """Stream of playback status events (playing, paused, stopped)"""
        return self._status_subject

    @property
    def progress_stream(self) -> Subject:
        """Stream of track progress events"""
        return self._progress_subject

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

            # 1. Maintain RxPy compatibility for legacy components
            self._status_subject.on_next(event)

            # 2. Main method: emit directly via Socket.IO (preferred)
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
            # Compose frontend-compatible payload (snake_case for frontend)
            event_data = {
                'track': track_info,
                'playlist': playlist_info,
                'current_time': elapsed,
                'duration': total,
                'is_playing': is_playing
            }
            event = PlaybackEvent('progress', event_data)
            self._last_progress_event = event

            # 1. Maintain RxPy compatibility for legacy components
            self._progress_subject.on_next(event)

            # 2. Main method: emit directly via Socket.IO (preferred)
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
        Emit a Socket.IO event in an optimized way to avoid thread conflicts.
        This is a simplified and robust version that minimizes new asyncio loop creation.
        """
        if not PlaybackSubject._socketio:
            return

        # Identify the current thread for logging
        thread_name = threading.current_thread().name

        # Check if this event should be sent (to reduce network overhead)
        if event_name == 'track_progress' and 'current_time' in event_data:
            # Only send progress updates at most every 250ms
            current_time = time.time()
            last_progress_time = getattr(self, '_last_progress_emit_time', 0)
            if current_time - last_progress_time < 0.25:  # 250ms throttle
                return  # Ignore overly frequent updates
            self._last_progress_emit_time = current_time

        # Simplified approach to reduce concurrency issues
        try:
            # Try to get the current event loop and use it if available
            try:
                loop = asyncio.get_running_loop()
                # Use create_task, which is safer than directly awaiting
                async def _emit():
                    try:
                        await PlaybackSubject._socketio.emit(event_name, event_data)
                    except Exception as e:
                        logger.log(LogLevel.ERROR, f"[Socket.IO] Emit failed: {e}")
                
                # Store tasks in a class variable to prevent them from being garbage collected
                if not hasattr(PlaybackSubject, '_pending_tasks'):
                    PlaybackSubject._pending_tasks = []
                
                # Create and store the task
                task = loop.create_task(_emit())
                PlaybackSubject._pending_tasks.append(task)
                
                # Add a callback to remove the task when done
                def _cleanup_task(completed_task):
                    if hasattr(PlaybackSubject, '_pending_tasks') and completed_task in PlaybackSubject._pending_tasks:
                        PlaybackSubject._pending_tasks.remove(completed_task)
                
                task.add_done_callback(_cleanup_task)
                return
            except RuntimeError:
                # No active asyncio event loop in this thread (likely a secondary thread)
                pass

            # If here, we are in a secondary thread without an active loop
            # Create a dedicated event loop and cache it globally for reuse
            # This avoids constantly creating new event loops
            if not hasattr(PlaybackSubject, '_thread_local_loops'):
                PlaybackSubject._thread_local_loops = {}

            thread_id = threading.get_ident()
            if thread_id not in PlaybackSubject._thread_local_loops:
                new_loop = asyncio.new_event_loop()
                PlaybackSubject._thread_local_loops[thread_id] = new_loop
                logger.log(LogLevel.DEBUG, f"Created new event loop for thread {thread_id}")

            loop = PlaybackSubject._thread_local_loops[thread_id]

            # Function to synchronously emit the event
            async def _emit_async():
                await PlaybackSubject._socketio.emit(event_name, event_data)

            # Synchronously emit the event using the existing loop
            loop.run_until_complete(_emit_async())

        except Exception as e:
            logger.log(LogLevel.ERROR, f"[Socket.IO] Emit error ({thread_name}): {e}")
            # Do not attempt further retries - this avoids error cascades