# app/src/module/audio_player/audio_factory.py

import os
import sys
from typing import Optional
from app.src.services.notification_service import PlaybackSubject
from .audio_player import AudioPlayer
from .audio_hardware import AudioPlayerHardware

def get_audio_player(playback_subject: Optional[PlaybackSubject] = None) -> AudioPlayer[AudioPlayerHardware]:
    if os.environ.get('USE_MOCK_HARDWARE', '').lower() == 'true' or sys.platform == 'darwin':
        from .audio_mock import MockAudioPlayer
        return AudioPlayer(MockAudioPlayer())
    else:
        from .audio_wm8960 import AudioPlayerWM8960
        return AudioPlayer(AudioPlayerWM8960(playback_subject))