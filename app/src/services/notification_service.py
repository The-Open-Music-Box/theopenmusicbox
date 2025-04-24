# app/src/services/notification_service.py

from typing import Dict, Any
import eventlet
from rx.subject import Subject

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
        eventlet.sleep(0)

class PlaybackEvent:
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data

class PlaybackSubject:
    def __init__(self):
        self._status_subject = Subject()
        self._progress_subject = Subject()

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
        self._status_subject.on_next(PlaybackEvent('status', {
            'status': status,
            'playlist': playlist_info,
            'current_track': track_info
        }))

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
        # Compose frontend-compatible payload (snake_case for frontend)
        event_data = {
            'track': track_info,
            'playlist': playlist_info,
            'current_time': elapsed,
            'duration': total,
            'is_playing': is_playing
        }
        self._progress_subject.on_next(PlaybackEvent('progress', event_data))