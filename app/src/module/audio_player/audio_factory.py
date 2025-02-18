# app/src/module/audio_player/audio_factory.py

import sys
from .audio_interface import AudioPlayerInterface

def get_audio_player() -> AudioPlayerInterface:
    if sys.platform == 'darwin':
        from .audio_mock import AudioPlayerMock
        return AudioPlayerMock()
    else:
        from .audio_wm8960 import AudioPlayerWM8960
        return AudioPlayerWM8960()