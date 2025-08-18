"""
Audio models for TheOpenMusicBox.

This module defines data models for audio playback state and events.
"""

from enum import Enum, auto
from typing import Dict, Optional


class AudioState(Enum):
    """Enum representing the possible states of audio playback."""


    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    LOADING = auto()
    ERROR = auto()


class PlaybackEvent(Enum):
    """Enum representing playback events that can be emitted."""


    TRACK_STARTED = auto()
    TRACK_ENDED = auto()
    TRACK_PAUSED = auto()
    TRACK_RESUMED = auto()
    PLAYLIST_STARTED = auto()
    PLAYLIST_ENDED = auto()
    PLAYBACK_ERROR = auto()
    PROGRESS_UPDATE = auto()
