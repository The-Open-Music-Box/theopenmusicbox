# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Domain models package for TheOpenMusicBox.

This package contains all domain entities and value objects following
Domain-Driven Design principles.
"""

from .track import Track
from .playlist import Playlist

__all__ = ["Track", "Playlist"]
