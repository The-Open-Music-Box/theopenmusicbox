# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Custom Exception Classes for Audio System.

This module defines custom exception classes used throughout the audio system
for better error handling and debugging.
"""


class AudioError(Exception):
    """Base exception for audio-related errors."""

    pass


class AudioResourceError(AudioError):
    """Exception raised when audio resource operations fail."""

    pass


class AudioResourceBusyError(AudioResourceError):
    """Exception raised when trying to access a resource that's already in use."""

    pass


class AudioDeviceError(AudioError):
    """Exception raised when audio device operations fail."""

    pass


class AudioFormatError(AudioError):
    """Exception raised when audio format is not supported or invalid."""

    pass


class AudioBufferError(AudioError):
    """Exception raised when audio buffer operations fail."""

    pass


class PlaylistError(Exception):
    """Base exception for playlist-related errors."""

    pass


class PlaylistNotFoundError(PlaylistError):
    """Exception raised when a playlist is not found."""

    pass


class TrackNotFoundError(PlaylistError):
    """Exception raised when a track is not found."""

    pass
