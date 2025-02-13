# app/src/module/audio_player/audio_wm8960.py

import os
import pygame
from pathlib import Path
from typing import Optional, List
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.helpers.exceptions import AppError
from .audio_interface import AudioPlayerInterface

logger = ImprovedLogger(__name__)

class AudioPlayerWM8960(AudioPlayerInterface):
    def __init__(self):
        try:
            pygame.mixer.init(frequency=44100, channels=2)
            self._current_playlist: Optional[List[str]] = None
            self._current_index = 0
            self._is_playing = False
            logger.log(LogLevel.INFO, "Audio system initialized")
        except Exception as e:
            raise AppError.hardware_error(
                message="Failed to initialize audio system",
                component="audio",
                operation="init",
                details={"error": str(e)}
            )

    def play(self, file_path: str) -> None:
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self._is_playing = True
            logger.log(LogLevel.INFO, f"Playing: {file_path}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Play error: {str(e)}")
            raise

    def pause(self) -> None:
        pygame.mixer.music.pause()
        self._is_playing = False

    def resume(self) -> None:
        pygame.mixer.music.unpause()
        self._is_playing = True

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self._is_playing = False

    def next_track(self) -> None:
        if not self._current_playlist:
            return
        self._current_index = (self._current_index + 1) % len(self._current_playlist)
        self.play(self._current_playlist[self._current_index])

    def previous_track(self) -> None:
        if not self._current_playlist:
            return
        self._current_index = (self._current_index - 1) % len(self._current_playlist)
        self.play(self._current_playlist[self._current_index])

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def cleanup(self) -> None:
        self.stop()
        pygame.mixer.quit()