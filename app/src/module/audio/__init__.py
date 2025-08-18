"""
Compatibility module for audio imports.

This module re-exports components from app.src.module.audio_player
to maintain backward compatibility with code that imports from app.src.module.audio.
"""

from app.src.module.audio_player.audio_factory import get_audio_player
from app.src.module.audio_player.audio_hardware import AudioPlayerHardware
from app.src.module.audio_player.audio_mock import MockAudioPlayer
from app.src.module.audio_player.audio_player import AudioPlayer
from app.src.module.audio_player.audio_wm8960 import AudioPlayerWM8960

__all__ = [
    "get_audio_player",
    "AudioPlayerHardware",
    "MockAudioPlayer",
    "AudioPlayer",
    "AudioPlayerWM8960",
]
