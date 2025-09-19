# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Backend adapter to use existing audio backends with new protocols."""

from typing import Optional, Any

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_errors
from ..protocols.audio_backend_protocol import AudioBackendProtocol

logger = get_logger(__name__)


class BackendAdapter(AudioBackendProtocol):
    """Adapter to make existing backends compatible with new protocol."""

    def __init__(self, backend: Any):
        """Initialize adapter with existing backend.

        Args:
            backend: Existing backend implementation
        """
        self._backend = backend
        logger.log(LogLevel.INFO, f"BackendAdapter wrapping {type(backend).__name__}")

    @property
    @handle_errors("is_playing")
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        if hasattr(self._backend, "is_playing"):
            attr = getattr(self._backend, "is_playing")
            return attr() if callable(attr) else bool(attr)
        return False

    @property
    @handle_errors("is_paused")
    def is_paused(self) -> bool:
        """Check if audio is currently paused."""
        if hasattr(self._backend, "is_paused"):
            attr = getattr(self._backend, "is_paused")
            return attr() if callable(attr) else bool(attr)
        return False

    @property
    @handle_errors("is_busy")
    def is_busy(self) -> bool:
        """Check if backend is busy processing."""
        if hasattr(self._backend, "is_busy"):
            attr = getattr(self._backend, "is_busy")
            return attr() if callable(attr) else bool(attr)
        # Fallback: consider busy if playing
        return self.is_playing

    @handle_errors("play_file")
    def play_file(self, file_path: str) -> bool:
        """Play an audio file."""
        if hasattr(self._backend, "play_file"):
            result = self._backend.play_file(file_path)
            return bool(result) if result is not None else True
        elif hasattr(self._backend, "play"):
            self._backend.play(file_path)
            return True
        else:
            logger.log(LogLevel.ERROR, "Backend does not support play_file")
            return False

    @handle_errors("pause")
    def pause(self) -> bool:
        """Pause current playback."""
        if hasattr(self._backend, "pause"):
            result = self._backend.pause()
            return bool(result) if result is not None else True
        else:
            logger.log(LogLevel.WARNING, "Backend does not support pause")
            return False

    @handle_errors("resume")
    def resume(self) -> bool:
        """Resume paused playback."""
        if hasattr(self._backend, "resume"):
            result = self._backend.resume()
            return bool(result) if result is not None else True
        else:
            logger.log(LogLevel.WARNING, "Backend does not support resume")
            return False

    @handle_errors("stop")
    def stop(self) -> bool:
        """Stop current playback."""
        if hasattr(self._backend, "stop"):
            result = self._backend.stop()
            return bool(result) if result is not None else True
        else:
            logger.log(LogLevel.WARNING, "Backend does not support stop")
            return False

    @handle_errors("set_volume")
    def set_volume(self, volume: int) -> bool:
        """Set playback volume."""
        if hasattr(self._backend, "set_volume"):
            result = self._backend.set_volume(volume)
            return bool(result) if result is not None else True
        else:
            logger.log(LogLevel.WARNING, "Backend does not support set_volume")
            return False

    @handle_errors("get_volume")
    def get_volume(self) -> int:
        """Get current volume level."""
        if hasattr(self._backend, "get_volume"):
            volume = self._backend.get_volume()
            return int(volume) if volume is not None else 50
        else:
            return 50  # Default volume

    @handle_errors("get_position")
    def get_position(self) -> float:
        """Get current playback position in seconds."""
        if hasattr(self._backend, "get_position"):
            position = self._backend.get_position()
            return float(position) if position is not None else 0.0
        else:
            return 0.0

    @handle_errors("set_position")
    def set_position(self, position_seconds: float) -> bool:
        """Set playback position (seek)."""
        if hasattr(self._backend, "set_position"):
            result = self._backend.set_position(position_seconds)
            return bool(result) if result is not None else True
        else:
            logger.log(LogLevel.WARNING, "Backend does not support set_position")
            return False

    @handle_errors("get_duration")
    def get_duration(self) -> Optional[float]:
        """Get duration of current track in seconds."""
        if hasattr(self._backend, "get_duration"):
            duration = self._backend.get_duration()
            return float(duration) if duration is not None else None
        else:
            return None

    def cleanup(self) -> None:
        """Clean up backend resources."""
        try:
            if hasattr(self._backend, "cleanup"):
                self._backend.cleanup()
            logger.log(LogLevel.DEBUG, "Backend cleanup completed")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during cleanup: {e}")
