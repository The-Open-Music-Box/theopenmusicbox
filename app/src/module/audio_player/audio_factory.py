import os
import sys
from typing import Optional

from app.src.services.notification_service import PlaybackSubject

from .audio_hardware import AudioPlayerHardware
from .audio_player import AudioPlayer


def get_audio_player(
    playback_subject: Optional[PlaybackSubject] = None,
) -> AudioPlayer[AudioPlayerHardware]:
    """Factory function to create and return the appropriate AudioPlayer
    instance based on the environment.

    If the environment variable 'USE_MOCK_HARDWARE' is set to 'true' or the platform is macOS ('darwin'),
    returns an AudioPlayer with a mock backend for development/testing. Otherwise, returns an AudioPlayer
    with the actual hardware backend (WM8960).

    Args:
        playback_subject (Optional[PlaybackSubject]): Optional notification service for playback events, only used for hardware backend.

    Returns:
        AudioPlayer[AudioPlayerHardware]: An instance of AudioPlayer using either mock or hardware implementation.
    """
    if (
        os.environ.get("USE_MOCK_HARDWARE", "").lower() == "true"
        or sys.platform == "darwin"
    ):
        from .audio_mock import MockAudioPlayer

        return AudioPlayer(MockAudioPlayer())
    else:
        from .audio_wm8960 import AudioPlayerWM8960

        return AudioPlayer(AudioPlayerWM8960(playback_subject))
