# app/src/module/audio_player/audio_interface.py

from abc import ABC, abstractmethod
from typing import List

class AudioPlayerInterface(ABC):
    @abstractmethod
    def set_playlist(self, file_paths: List[str]) -> None:
        """Set and start playing a list of audio files"""

    @abstractmethod
    def play(self, file_path: str) -> None:
        """Play an audio file"""

    @abstractmethod
    def pause(self) -> None:
        """Pause current playback"""

    @abstractmethod
    def resume(self) -> None:
        """Resume playback"""

    @abstractmethod
    def stop(self) -> None:
        """Stop playback"""

    @abstractmethod
    def next_track(self) -> None:
        """Play next track"""

    @abstractmethod
    def previous_track(self) -> None:
        """Play previous track"""

    @property
    @abstractmethod
    def is_playing(self) -> bool:
        """Return True if currently playing"""

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources"""