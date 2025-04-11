# app/src/module/audio_player/audio_interface.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from src.model.track import Track
from src.model.playlist import Playlist
from src.services.notification_service import PlaybackSubject

class AudioPlayerInterface(ABC):
    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        """
        Initialize the audio player.
        Args:
            playback_subject: Optional PlaybackSubject for emitting playback events
        """
        self._playback_subject = playback_subject

    @property
    def playback_subject(self) -> Optional[PlaybackSubject]:
        """Get the playback subject for subscribing to events"""
        return self._playback_subject

    @abstractmethod
    def load_playlist(self, playlist_path: str) -> bool:
        """
        Load a playlist from the given path.
        Args:
            playlist_path: Path to the playlist directory
        Returns:
            bool: True if playlist was loaded successfully
        """
        pass

    @abstractmethod
    def set_playlist(self, playlist: Playlist) -> bool:
        """Set and start playing a playlist"""
        pass

    @abstractmethod
    def play_track(self, track_number: int) -> bool:
        """
        Play a specific track from the current playlist.
        Args:
            track_number: Track number to play (1-based index)
        Returns:
            bool: True if track started playing successfully
        """
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause the current track."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume playing the current track."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop playback and clear the current playlist."""
        pass

    @abstractmethod
    def next_track(self) -> None:
        """Play next track"""
        pass

    @abstractmethod
    def previous_track(self) -> None:
        """Play previous track"""
        pass

    @property
    @abstractmethod
    def is_playing(self) -> bool:
        """Return True if currently playing"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass

    @abstractmethod
    def get_current_track(self) -> Optional[Track]:
        """Get the currently playing track"""
        pass

    @abstractmethod
    def get_playlist(self) -> Optional[Playlist]:
        """Get the current playlist"""
        pass

    @abstractmethod
    def set_volume(self, volume: int) -> bool:
        """Set the playback volume (0-100)"""
        pass

    @abstractmethod
    def get_volume(self) -> int:
        """Get the current volume"""
        pass

    # @abstractmethod
    # def is_finished(self) -> bool:
    #     """Return True if playlist has finished playing"""
    #     pass