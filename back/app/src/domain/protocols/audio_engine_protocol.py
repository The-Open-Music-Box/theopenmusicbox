# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Audio engine protocol for dependency injection."""

from typing import Protocol, Dict, Any
from app.src.domain.models.playlist import Playlist


class AudioEngineProtocol(Protocol):
    """Protocol defining the interface for the audio engine."""

    async def start(self) -> None:
        """Start the audio engine."""
        ...

    async def stop(self) -> None:
        """Stop the audio engine."""
        ...

    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        ...

    # Playlist operations
    async def load_playlist(self, playlist: Playlist) -> bool:
        """Load a playlist for playback."""
        ...

    async def play_playlist(self, playlist: Playlist) -> bool:
        """Load and start playing a playlist."""
        ...

    async def next_track(self) -> bool:
        """Advance to next track."""
        ...

    async def previous_track(self) -> bool:
        """Go to previous track."""
        ...

    async def play_track_by_index(self, index: int) -> bool:
        """Play track by index."""
        ...

    # Playback control
    async def play_file(self, file_path: str) -> bool:
        """Play a single audio file."""
        ...

    async def pause_playback(self) -> bool:
        """Pause current playback."""
        ...

    async def resume_playback(self) -> bool:
        """Resume paused playback."""
        ...

    async def stop_playback(self) -> bool:
        """Stop current playback."""
        ...

    async def set_volume(self, volume: int) -> bool:
        """Set playback volume."""
        ...

    # State access
    def get_state_dict(self) -> Dict[str, Any]:
        """Get current state as dictionary."""
        ...

    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics."""
        ...
