# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""YouTube services module initialization.

Provides YouTube-related functionality including video downloading with yt-dlp
and high-level service orchestration. Exposes both the low-level downloader
and the high-level service interface for YouTube integration.
"""

from .downloader import YouTubeDownloader
from .service import YouTubeService

__all__ = ["YouTubeService", "YouTubeDownloader"]
