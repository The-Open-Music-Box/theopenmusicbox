# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Simplified Unified Audio Player for Domain Purity.

This is a simplified version that removes Application layer dependencies
while maintaining the core audio functionality.
"""

from typing import Optional, Any
from pathlib import Path

from app.src.domain.data.models.playlist import Playlist
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.domain.protocols.notification_protocol import PlaybackNotifierProtocol as PlaybackSubject
from app.src.domain.protocols.audio_backend_protocol import AudioBackendProtocol
# PlaylistManagerProtocol removed - use data domain services
from app.src.domain.decorators.error_handler import handle_domain_errors as handle_errors

logger = get_logger(__name__)


class UnifiedAudioPlayer:
    """Simplified unified audio player with optional playlist management.

    This version maintains Domain purity by using dependency injection
    for playlist management rather than direct Application layer imports.
    """

    def __init__(
        self,
        audio_backend: AudioBackendProtocol,
        playlist_controller: Optional[Any] = None,  # PlaylistManagerProtocol removed
        playback_subject: Optional[PlaybackSubject] = None,
    ):
        """Initialize the unified audio player.

        Args:
            audio_backend: The platform-specific audio backend to use
            playlist_controller: Optional playlist controller (injected dependency)
            playback_subject: Optional notification service for events
        """
        self._backend = audio_backend
        self._playback_subject = playback_subject
        self._playlist_controller = playlist_controller  # Injected dependency

        logger.log(
            LogLevel.INFO,
            f"✅ UnifiedAudioPlayer initialized with {type(audio_backend).__name__} backend",
        )

    def _has_playlist_controller(self) -> bool:
        """Check if playlist controller is available."""
        return self._playlist_controller is not None

    # === Core Audio Operations (Domain Pure) ===

    def play_file(self, file_path: str) -> bool:
        """Play a single audio file directly.

        Args:
            file_path: Path to the audio file

        Returns:
            bool: True if playback started successfully
        """
        return self._backend.play_file(file_path)

    def pause(self) -> bool:
        """Pause current playback."""
        return self._backend.pause()

    def resume(self) -> bool:
        """Resume paused playback."""
        return self._backend.resume()

    def stop(self) -> bool:
        """Stop current playback."""
        return self._backend.stop()

    def set_volume(self, volume: int) -> bool:
        """Set playback volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if volume was set successfully
        """
        return self._backend.set_volume(volume)

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        return self._backend.get_position()

    def set_position(self, position_seconds: float) -> bool:
        """Set playback position.

        Args:
            position_seconds: Position in seconds

        Returns:
            bool: True if position was set successfully
        """
        return self._backend.set_position(position_seconds)

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._backend.is_playing()

    def get_duration(self) -> float:
        """Get duration of current track in seconds."""
        return self._backend.get_duration()

    # === Playlist Operations (Optional - requires controller injection) ===

    def set_playlist(self, playlist: Playlist) -> bool:
        """Load and set a playlist (requires playlist controller).

        Args:
            playlist: The playlist to load

        Returns:
            bool: True if playlist was set successfully
        """
        if not self._has_playlist_controller():
            logger.log(LogLevel.WARNING, "⚠️ Playlist operations require playlist controller injection")
            return False

        self._playlist_controller.set_current_playlist(playlist)
        logger.log(LogLevel.INFO, f"✅ Playlist set: {playlist.name}")
        return True

    def next_track(self) -> bool:
        """Advance to next track (requires playlist controller)."""
        if not self._has_playlist_controller():
            logger.log(LogLevel.WARNING, "⚠️ Track navigation requires playlist controller injection")
            return False

        # For now, just log - full implementation would coordinate with controller
        logger.log(LogLevel.INFO, "🎵 Next track requested")
        return True

    def previous_track(self) -> bool:
        """Go to previous track (requires playlist controller)."""
        if not self._has_playlist_controller():
            logger.log(LogLevel.WARNING, "⚠️ Track navigation requires playlist controller injection")
            return False

        # For now, just log - full implementation would coordinate with controller
        logger.log(LogLevel.INFO, "🎵 Previous track requested")
        return True

    def get_current_track_info(self) -> Optional[dict]:
        """Get current track information."""
        if not self._has_playlist_controller():
            return None

        # Basic track info from backend
        return {
            "position": self.get_position(),
            "duration": self.get_duration(),
            "is_playing": self.is_playing(),
        }

    # === Cleanup ===

    def cleanup(self) -> None:
        """Clean up resources."""
        logger.log(LogLevel.INFO, "🧹 Cleaning up UnifiedAudioPlayer...")

        if self._backend:
            self._backend.cleanup()

        logger.log(LogLevel.INFO, "✅ UnifiedAudioPlayer cleanup completed")