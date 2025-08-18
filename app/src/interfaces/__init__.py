# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Interface definitions for service abstractions.

This package contains abstract base classes and interfaces that define
contracts for services, promoting loose coupling and testability.
"""

from .audio_service_interface import AudioServiceInterface
from .playlist_service_interface import PlaylistServiceInterface
from .upload_service_interface import UploadServiceInterface

__all__ = [
    "AudioServiceInterface",
    "PlaylistServiceInterface", 
    "UploadServiceInterface",
]
