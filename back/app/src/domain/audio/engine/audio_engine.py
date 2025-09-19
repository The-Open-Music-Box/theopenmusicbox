# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Unified audio engine implementation."""

import time
from typing import Dict, Any, Optional

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_errors
from app.src.domain.models.playlist import Playlist

from ..protocols.audio_backend_protocol import AudioBackendProtocol
from ..protocols.audio_engine_protocol import AudioEngineProtocol
from ..protocols.event_bus_protocol import EventBusProtocol
from ..protocols.state_manager_protocol import StateManagerProtocol, PlaybackState
from ..protocols.playlist_manager_protocol import PlaylistManagerProtocol

from ..events.audio_events import (
    TrackStartedEvent,
    PlaylistLoadedEvent,
    PlaybackStateChangedEvent,
    VolumeChangedEvent,
    ErrorEvent,
)

logger = get_logger(__name__)


class AudioEngine(AudioEngineProtocol):
    """Unified audio engine coordinating all audio operations."""

    def __init__(
        self,
        backend: AudioBackendProtocol,
        event_bus: EventBusProtocol,
        state_manager: StateManagerProtocol,
        playlist_manager: PlaylistManagerProtocol,
    ):
        """Initialize the audio engine.

        Args:
            backend: Audio backend implementation
            event_bus: Event bus for notifications
            state_manager: State management
            playlist_manager: Playlist management
        """
        self._backend = backend
        self._event_bus = event_bus
        self._state_manager = state_manager
        self._playlist_manager = playlist_manager
        self._is_running = False
        self._startup_time: Optional[float] = None

        # Validate state manager has required methods
        if not hasattr(state_manager, "set_state"):
            logger.log(
                LogLevel.ERROR,
                f"❌ Invalid StateManager type: {type(state_manager).__name__} lacks set_state method",
            )
            raise ValueError(
                f"StateManager must have set_state method, got {type(state_manager).__name__}"
            )

        # Subscribe to state changes for event generation
        self._setup_event_subscriptions()

        logger.log(
            LogLevel.INFO,
            f"AudioEngine initialized with {type(backend).__name__} and {type(state_manager).__name__}",
        )

    @handle_errors("_safe_set_state")
    def _safe_set_state(self, state: PlaybackState) -> None:
        """Safely set state with validation."""
        if hasattr(self._state_manager, "set_state"):
            self._state_manager.set_state(state)
        else:
            logger.log(
                LogLevel.ERROR,
                f"❌ StateManager {type(self._state_manager).__name__} lacks set_state method",
            )

    @handle_errors("_safe_get_current_state")
    def _safe_get_current_state(self) -> PlaybackState:
        """Safely get current state with fallback."""
        if hasattr(self._state_manager, "get_current_state"):
            return self._safe_get_current_state()
        else:
            logger.log(
                LogLevel.WARNING,
                f"⚠️ StateManager {type(self._state_manager).__name__} lacks get_current_state method",
            )
            return PlaybackState.STOPPED  # Safe fallback

    def _setup_event_subscriptions(self) -> None:
        """Set up internal event subscriptions."""
        # We'll add event handlers here as needed
        pass

    @handle_errors("start")
    async def start(self) -> None:
        """Start the audio engine."""
        if self._is_running:
            return

        self._safe_set_state(PlaybackState.LOADING)
        self._is_running = True
        self._startup_time = time.time()
        self._safe_set_state(PlaybackState.STOPPED)
        logger.log(LogLevel.INFO, "🎛️ AudioEngine started successfully")

    @handle_errors("stop")
    async def stop(self) -> None:
        """Stop the audio engine."""
        if not self._is_running:
            return

        # Stop any current playback
        await self.stop_playback()
        # Cleanup backend
        self._backend.cleanup()
        self._is_running = False
        self._safe_set_state(PlaybackState.STOPPED)
        logger.log(LogLevel.INFO, "🎛️ AudioEngine stopped")

    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._is_running

    @property
    def event_bus(self) -> EventBusProtocol:
        """Get the event bus instance."""
        return self._event_bus

    @property
    def state_manager(self) -> StateManagerProtocol:
        """Get the state manager instance."""
        return self._state_manager

    # === Playlist Operations ===

    async def load_playlist(self, playlist: Playlist) -> bool:
        """Load a playlist for playback."""
        if not self._is_running:
            logger.log(LogLevel.ERROR, "Engine not running")
            return False

        try:
            success = self._playlist_manager.set_playlist(playlist)

            if success:
                # Update state
                self._state_manager.update_playlist_info(
                    {
                        "playlist_id": getattr(playlist, "id", None),
                        "title": playlist.title,
                        "track_count": len(playlist.tracks),
                    }
                )

                # Fire event
                await self._event_bus.publish(
                    PlaylistLoadedEvent(
                        "AudioEngine",
                        playlist_id=getattr(playlist, "id", None),
                        playlist_title=playlist.title,
                        track_count=len(playlist.tracks),
                    )
                )

            return success

        except Exception as e:
            await self._event_bus.publish(
                ErrorEvent("AudioEngine", f"Failed to load playlist: {e}")
            )
            return False

    async def play_playlist(self, playlist: Playlist) -> bool:
        """Load and start playing a playlist."""
        success = await self.load_playlist(playlist)
        if success and playlist.tracks:
            # Playlist manager should have started playing automatically
            return self._playlist_manager.is_playing
        return False

    @handle_errors("set_playlist")
    def set_playlist(self, playlist: Playlist) -> bool:
        """Legacy compatibility method for PlaylistService.

        This method provides backwards compatibility for legacy code that expects
        a synchronous set_playlist method.

        Args:
            playlist: Playlist to load and play

        Returns:
            bool: True if playlist was loaded and started successfully
        """
        import asyncio

        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            task = loop.create_task(self.play_playlist(playlist))
            # For legacy compatibility, we return immediately
            # The actual result will be handled asynchronously
            logger.log(
                LogLevel.INFO, f"✅ AudioEngine.set_playlist called for playlist: {playlist.name}"
            )
            return True
        except RuntimeError:
            # Not in an async context, handle synchronously
            logger.log(LogLevel.WARNING, "AudioEngine.set_playlist called outside async context")
            return False

    async def next_track(self) -> bool:
        """Advance to next track."""
        if not self._is_running:
            return False

        try:
            return self._playlist_manager.next_track()
        except Exception as e:
            await self._event_bus.publish(
                ErrorEvent("AudioEngine", f"Failed to go to next track: {e}")
            )
            return False

    async def previous_track(self) -> bool:
        """Go to previous track."""
        if not self._is_running:
            return False

        try:
            return self._playlist_manager.previous_track()
        except Exception as e:
            await self._event_bus.publish(
                ErrorEvent("AudioEngine", f"Failed to go to previous track: {e}")
            )
            return False

    async def play_track_by_index(self, index: int) -> bool:
        """Play track by index."""
        if not self._is_running:
            return False

        try:
            # Convert to 1-based for playlist manager
            return self._playlist_manager.play_track_by_number(index + 1)
        except Exception as e:
            await self._event_bus.publish(
                ErrorEvent("AudioEngine", f"Failed to play track {index}: {e}")
            )
            return False

    # === Direct Playback Operations ===

    async def play_file(self, file_path: str) -> bool:
        """Play a single audio file."""
        if not self._is_running:
            return False

        try:
            old_state = self._safe_get_current_state()
            success = self._backend.play_file(file_path)

            if success:
                self._safe_set_state(PlaybackState.PLAYING)
                self._state_manager.update_track_info(
                    {
                        "file_path": file_path,
                        "title": file_path.split("/")[-1],  # Basic title from filename
                    }
                )

                # Fire events
                await self._event_bus.publish(
                    PlaybackStateChangedEvent("AudioEngine", old_state, PlaybackState.PLAYING)
                )
                await self._event_bus.publish(TrackStartedEvent("AudioEngine", file_path))

            return success

        except Exception as e:
            await self._event_bus.publish(ErrorEvent("AudioEngine", f"Failed to play file: {e}"))
            return False

    async def pause_playback(self) -> bool:
        """Pause current playback."""
        if not self._is_running:
            return False

        try:
            old_state = self._safe_get_current_state()

            # Try playlist manager first, then direct backend
            success = (
                self._playlist_manager.pause()
                if self._playlist_manager.current_playlist
                else self._backend.pause()
            )

            if success:
                self._safe_set_state(PlaybackState.PAUSED)
                await self._event_bus.publish(
                    PlaybackStateChangedEvent("AudioEngine", old_state, PlaybackState.PAUSED)
                )

            return success

        except Exception as e:
            await self._event_bus.publish(ErrorEvent("AudioEngine", f"Failed to pause: {e}"))
            return False

    async def resume_playback(self) -> bool:
        """Resume paused playback."""
        if not self._is_running:
            return False

        try:
            old_state = self._safe_get_current_state()

            # Try playlist manager first, then direct backend
            success = (
                self._playlist_manager.resume()
                if self._playlist_manager.current_playlist
                else self._backend.resume()
            )

            if success:
                self._safe_set_state(PlaybackState.PLAYING)
                await self._event_bus.publish(
                    PlaybackStateChangedEvent("AudioEngine", old_state, PlaybackState.PLAYING)
                )

            return success

        except Exception as e:
            await self._event_bus.publish(ErrorEvent("AudioEngine", f"Failed to resume: {e}"))
            return False

    @handle_errors("stop_playback")
    async def stop_playback(self) -> bool:
        """Stop current playback."""
        if not self._is_running:
            return False

        old_state = self._safe_get_current_state()
        # Try playlist manager first, then direct backend
        success = (
            self._playlist_manager.stop()
            if self._playlist_manager.current_playlist
            else self._backend.stop()
        )
        if success:
            self._safe_set_state(PlaybackState.STOPPED)
            if hasattr(self._state_manager, "update_position"):
                self._state_manager.update_position(0.0)
            await self._event_bus.publish(
                PlaybackStateChangedEvent("AudioEngine", old_state, PlaybackState.STOPPED)
            )
        return success

    async def set_volume(self, volume: int) -> bool:
        """Set playback volume."""
        if not self._is_running:
            return False

        try:
            old_volume = self._backend.get_volume()
            success = self._backend.set_volume(volume)

            if success:
                self._state_manager.update_volume(volume)
                await self._event_bus.publish(VolumeChangedEvent("AudioEngine", old_volume, volume))

            return success

        except Exception as e:
            await self._event_bus.publish(ErrorEvent("AudioEngine", f"Failed to set volume: {e}"))
            return False

    # === State Access ===

    def get_state_dict(self) -> Dict[str, Any]:
        """Get current state as dictionary."""
        base_state = self._state_manager.get_state_dict()

        # Add playlist information if available
        if self._playlist_manager.current_playlist:
            playlist_info = self._playlist_manager.get_playlist_info()
            track_info = self._playlist_manager.get_track_info()
            base_state.update(
                {
                    "playlist_info": playlist_info,
                    "track_info": track_info,
                    "position_seconds": self._playlist_manager.get_position(),
                }
            )

        # Add engine metadata
        base_state.update(
            {
                "engine_running": self._is_running,
                "uptime_seconds": time.time() - self._startup_time if self._startup_time else 0,
                "backend_type": type(self._backend).__name__,
            }
        )

        return base_state

    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics."""
        return {
            "engine": {
                "is_running": self._is_running,
                "uptime_seconds": time.time() - self._startup_time if self._startup_time else 0,
                "backend_type": type(self._backend).__name__,
            },
            "event_bus": getattr(self._event_bus, "get_statistics", lambda: {})(),
            "current_state": self.get_state_dict(),
        }
