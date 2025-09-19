# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unified Audio Player Implementation.

This module provides a unified audio player that combines platform-specific
audio backends with centralized playlist management. It provides a clean,
consistent API for all audio operations while delegating playlist logic
to the PlaylistController.
"""

from typing import Dict, Any, Optional

from app.src.domain.models.playlist import Playlist
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.notification_service import PlaybackSubject

from ...protocols.audio_backend_protocol import AudioBackendProtocol
from ....controllers.unified_controller import UnifiedPlaylistController
from app.src.services.error.unified_error_decorator import handle_errors

logger = get_logger(__name__)


class UnifiedAudioPlayer:
    """Unified audio player with centralized playlist management.

    This class provides a clean, consistent API for audio playback operations
    while delegating platform-specific audio operations to backend implementations
    and playlist management to the centralized PlaylistController.

    Key features:
    - Platform-agnostic audio operations
    - Centralized playlist management and auto-advance
    - Consistent behavior across all platforms
    - Clean separation of concerns
    """

    def __init__(
        self,
        audio_backend: AudioBackendProtocol,
        playback_subject: Optional[PlaybackSubject] = None,
    ):
        """Initialize the unified audio player.

        Args:
            audio_backend: The platform-specific audio backend to use
            playback_subject: Optional notification service for events
        """
        self._backend = audio_backend
        self._playback_subject = playback_subject
        self._playlist_controller = UnifiedPlaylistController()

        logger.log(
            LogLevel.INFO,
            f"✅ UnifiedAudioPlayer initialized with {type(audio_backend).__name__} backend",
        )

    # === Playlist Operations ===

    def set_playlist(self, playlist: Playlist) -> bool:
        """Load and start playing a playlist.

        Args:
            playlist: The playlist to load and play

        Returns:
            bool: True if playlist was loaded successfully, False otherwise
        """
        return self._playlist_controller.set_playlist(playlist)

    def next_track(self) -> bool:
        """Manually advance to the next track in the playlist.

        Returns:
            bool: True if advanced successfully, False if at end of playlist
        """
        return self._playlist_controller.next_track()

    def previous_track(self) -> bool:
        """Go back to the previous track in the playlist.

        Returns:
            bool: True if went back successfully, False if at beginning
        """
        return self._playlist_controller.previous_track()

    @handle_errors("auto_advance_to_next")
    def auto_advance_to_next(self) -> bool:
        """Auto-advance to the next track (called by TrackProgressService).

        Returns:
            bool: True if advanced successfully, False if at end of playlist
        """
        # Use the internal auto-advance method to distinguish from manual next
        self._playlist_controller._auto_advance_to_next()
        # Check if advance was successful by checking if we're still playing
        return self._playlist_controller.is_playing

    def play_track(self, track_number: int) -> bool:
        """Play a specific track by its track number.

        Args:
            track_number: Track number (1-based)

        Returns:
            bool: True if track started playing, False otherwise
        """
        return self._playlist_controller.play_track_by_number(track_number)

    # === Playback Control ===

    def pause(self) -> bool:
        """Pause current playback.

        Returns:
            bool: True if paused successfully, False otherwise
        """
        return self._playlist_controller.pause()

    def resume(self) -> bool:
        """Resume paused playback.

        Returns:
            bool: True if resumed successfully, False otherwise
        """
        return self._playlist_controller.resume()

    def stop(self, clear_playlist: bool = True) -> bool:
        """Stop playback.

        Args:
            clear_playlist: Whether to clear the current playlist (legacy parameter)

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        return self._playlist_controller.stop()

    def set_volume(self, volume: int) -> bool:
        """Set playback volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if volume was set successfully, False otherwise
        """
        return self._playlist_controller.set_volume(volume)

    def set_position(self, position_seconds: float) -> bool:
        """Set playback position (seeking).

        Note: This is a simplified implementation. Full seeking support
        would require backend-specific implementation.

        Args:
            position_seconds: Position to seek to in seconds

        Returns:
            bool: True if seeking was successful, False otherwise
        """
        # Delegate seeking to the playlist controller for consistent state management
        return self._playlist_controller.set_position(position_seconds)

    # === State Access ===

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing.

        Returns:
            bool: True if playing, False otherwise
        """
        return self._playlist_controller.is_playing

    def get_position(self) -> float:
        """Get current playback position in seconds.

        Returns:
            float: Current position in seconds, 0.0 if not available
        """
        return self._playlist_controller.get_position()

    def get_current_track_info(self) -> Dict[str, Any]:
        """Get information about the currently playing track.

        Returns:
            Dict[str, Any]: Current track information including:
                - track_number: Track number (1-based)
                - track_id: Track ID if available
                - title: Track title
                - filename: Track filename
                - duration_sec: Track duration in seconds
        """
        return self._playlist_controller.get_current_track_info()

    def get_playlist_info(self) -> Dict[str, Any]:
        """Get information about the current playlist.

        Returns:
            Dict[str, Any]: Playlist information including:
                - playlist_id: Playlist ID if available
                - playlist_title: Playlist name
                - current_track_index: Current track index (0-based)
                - track_count: Total number of tracks
                - can_next: Whether next track is available
                - can_prev: Whether previous track is available
        """
        return self._playlist_controller.get_playlist_info()

    # === Legacy Compatibility ===

    def play(self, track: str) -> None:
        """Play a single track by filename or path (legacy method).

        This method is provided for backward compatibility with existing code
        that expects to play individual tracks.

        Args:
            track: Path to the track to play
        """
        success = self._backend.play_file(track)
        if success:
            logger.log(LogLevel.INFO, f"🎵 Playing single track: {track}")
        else:
            logger.log(LogLevel.ERROR, f"❌ Failed to play track: {track}")

    def is_finished(self) -> bool:
        """Check if the current playlist has finished playing.

        Returns:
            bool: True if playlist has finished, False otherwise
        """
        # A playlist is finished if we're not playing and not paused
        return not self.is_playing and not self._playlist_controller.is_paused

    # === Cleanup ===

    def cleanup(self) -> None:
        """Clean up all resources."""
        logger.log(LogLevel.INFO, "🧹 UnifiedAudioPlayer cleanup started")
        self._playlist_controller.cleanup()
        logger.log(LogLevel.INFO, "✅ UnifiedAudioPlayer cleanup completed")
