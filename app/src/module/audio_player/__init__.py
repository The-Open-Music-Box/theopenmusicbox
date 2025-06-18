"""Audio Player module for playback with hardware support.

This module provides a platform-independent interface for audio
playback, with implementations for both Raspberry Pi hardware (WM8960)
and mock testing.
"""

from .audio_factory import get_audio_player

__all__ = ["get_audio_player"]
