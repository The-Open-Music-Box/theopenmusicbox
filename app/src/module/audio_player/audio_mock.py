# app/src/module/audio_player/audio_mock.py

import simpleaudio as sa
from pathlib import Path
from typing import List, Optional
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.module.audio_player.audio_interface import AudioPlayerInterface
from src.services.notification_service import PlaybackSubject
from src.model.track import Track
from src.model.playlist import Playlist
import time

logger = ImprovedLogger(__name__)

class AudioPlayerMock(AudioPlayerInterface):
    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        super().__init__(playback_subject)
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        self._play_obj = None
        self._progress_thread = None
        self._stop_progress = False
        logger.log(LogLevel.INFO, "Mock Audio Player initialized")

    def load_playlist(self, playlist_path: str) -> bool:
        logger.log(LogLevel.INFO, f"Mock: Loading playlist from {playlist_path}")
        return True

    def play_track(self, track_number: int) -> bool:
        self._is_playing = True
        if self._playback_subject:
            self._playback_subject.notify_playback_status(
                'playing',
                {'name': self._playlist.name if self._playlist else None},
                {
                    'number': track_number,
                    'title': f'Mock Track {track_number}',
                    'filename': f'mock_{track_number}.mp3'
                }
            )
        logger.log(LogLevel.INFO, f"Mock: Playing track {track_number}")
        return True

    def pause(self) -> None:
        if self._is_playing:
            if self._play_obj and self._play_obj.is_playing():
                self._play_obj.stop()
            self._is_playing = False
            if self._playback_subject:
                self._playback_subject.notify_playback_status(
                    'paused',
                    {'name': self._playlist.name if self._playlist else None},
                    {
                        'number': self._current_track.number if self._current_track else 1,
                        'title': f'Mock Track {self._current_track.number if self._current_track else 1}',
                        'filename': f'mock_{self._current_track.number if self._current_track else 1}.mp3'
                    }
                )
            logger.log(LogLevel.INFO, "Mock: Playback paused")

    def resume(self) -> None:
        if not self._is_playing:
            self._is_playing = True
            if self._playback_subject:
                self._playback_subject.notify_playback_status(
                    'playing',
                    {'name': self._playlist.name if self._playlist else None},
                    {
                        'number': self._current_track.number if self._current_track else 1,
                        'title': f'Mock Track {self._current_track.number if self._current_track else 1}',
                        'filename': f'mock_{self._current_track.number if self._current_track else 1}.mp3'
                    }
                )
            logger.log(LogLevel.INFO, "Mock: Playback resumed")

    def stop(self) -> None:
        if self._play_obj and self._play_obj.is_playing():
            self._play_obj.stop()
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        if self._playback_subject:
            self._playback_subject.notify_playback_status('stopped')
        logger.log(LogLevel.INFO, "Mock: Playback stopped")

    def next_track(self) -> None:
        if not self._current_track or not self._playlist:
            return
        next_number = self._current_track.number + 1
        if next_number <= len(self._playlist):
            self.play_track(next_number)

    def previous_track(self) -> None:
        if not self._current_track or not self._playlist:
            return
        prev_number = self._current_track.number - 1
        if prev_number > 0:
            self.play_track(prev_number)

    def set_volume(self, volume: int) -> bool:
        try:
            self._volume = max(0, min(100, volume))
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting volume: {e}")
            return False

    def get_volume(self) -> int:
        return self._volume

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def cleanup(self) -> None:
        self.stop()
        logger.log(LogLevel.INFO, "Mock: Resources cleaned up")