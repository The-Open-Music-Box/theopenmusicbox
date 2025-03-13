# app/src/module/audio_player/audio_factory.py

import sys
from typing import Optional
from src.services.notification_service import PlaybackSubject
from .audio_interface import AudioPlayerInterface

def get_audio_player(playback_subject: Optional[PlaybackSubject] = None) -> AudioPlayerInterface:
    if sys.platform == 'darwin':
        from .audio_mock import AudioPlayerMock
        return AudioPlayerMock(playback_subject)
    else:
        from .audio_wm8960 import AudioPlayerWM8960
        return AudioPlayerWM8960(playback_subject)