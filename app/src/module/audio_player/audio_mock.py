# app/src/module/audio_player/audio_mock.py

from typing import Optional, List
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .audio_interface import AudioPlayerInterface

logger = ImprovedLogger(__name__)

class MockAudioPlayer(AudioPlayerInterface):
    def __init__(self):
        self._current_playlist: Optional[List[str]] = None
        self._current_index = 0
        self._is_playing = False
        logger.log(LogLevel.INFO, "Mock audio player initialized")

    def play(self, file_path: str) -> None:
        self._is_playing = True
        logger.log(LogLevel.INFO, f"Mock playing: {file_path}")

    def pause(self) -> None:
        self._is_playing = False
        logger.log(LogLevel.INFO, "Mock playback paused")

    def resume(self) -> None:
        self._is_playing = True
        logger.log(LogLevel.INFO, "Mock playback resumed")

    def stop(self) -> None:
        self._is_playing = False
        logger.log(LogLevel.INFO, "Mock playback stopped")

    def next_track(self) -> None:
        if not self._current_playlist:
            return
        self._current_index = (self._current_index + 1) % len(self._current_playlist)
        self.play(self._current_playlist[self._current_index])
        logger.log(LogLevel.INFO, "Mock next track")

    def previous_track(self) -> None:
        if not self._current_playlist:
            return
        self._current_index = (self._current_index - 1) % len(self._current_playlist)
        self.play(self._current_playlist[self._current_index])
        logger.log(LogLevel.INFO, "Mock previous track")

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def cleanup(self) -> None:
        self.stop()
        logger.log(LogLevel.INFO, "Mock audio player cleaned up")