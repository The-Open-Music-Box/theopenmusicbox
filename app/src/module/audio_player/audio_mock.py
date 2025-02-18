# app/src/module/audio_player/audio_mock.py

from typing import List
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .audio_interface import AudioPlayerInterface

logger = ImprovedLogger(__name__)

class AudioPlayerMock(AudioPlayerInterface):
    def __init__(self):
        self._current_playlist: List[str] = []
        self._current_index = 0
        self._is_playing = False
        logger.log(LogLevel.INFO, "Mock Audio Player initialized")

    def set_playlist(self, file_paths: List[str]) -> None:
        self._current_playlist = file_paths
        self._current_index = 0
        if self._current_playlist:
            self.play(self._current_playlist[0])
        logger.log(LogLevel.INFO, f"Mock: Setting playlist with {len(file_paths)} tracks")

    def play(self, file_path: str) -> None:
        self._is_playing = True
        logger.log(LogLevel.INFO, f"Mock: Playing {file_path}")

    def pause(self) -> None:
        self._is_playing = False
        logger.log(LogLevel.INFO, "Mock: Playback paused")

    def resume(self) -> None:
        self._is_playing = True
        logger.log(LogLevel.INFO, "Mock: Playback resumed")

    def stop(self) -> None:
        self._is_playing = False
        self._current_playlist = []
        self._current_index = 0
        logger.log(LogLevel.INFO, "Mock: Playback stopped")

    def next_track(self) -> None:
        if not self._current_playlist:
            return
        self._current_index = (self._current_index + 1) % len(self._current_playlist)
        self.play(self._current_playlist[self._current_index])
        logger.log(LogLevel.INFO, "Mock: Skipped to next track")

    def previous_track(self) -> None:
        if not self._current_playlist:
            return
        self._current_index = (self._current_index - 1) % len(self._current_playlist)
        self.play(self._current_playlist[self._current_index])
        logger.log(LogLevel.INFO, "Mock: Skipped to previous track")

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def cleanup(self) -> None:
        self.stop()
        logger.log(LogLevel.INFO, "Mock: Audio player cleaned up")