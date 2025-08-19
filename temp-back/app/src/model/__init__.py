# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Model package for database entities and ORM mappings.

This package defines ORM mappings and core data structures for playlists
and tracks in TheOpenMusicBox backend.
"""

from .playlist import Playlist
from .track import Track

__all__ = ["Track", "Playlist"]
