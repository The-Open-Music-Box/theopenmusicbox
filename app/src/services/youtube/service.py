# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

from pathlib import Path
from typing import Dict
from uuid import uuid4

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.notification_service import DownloadNotifier
from app.src.services.playlist_service import PlaylistService

from .downloader import YouTubeDownloader

logger = ImprovedLogger(__name__)


class YouTubeService:
    """Service for handling YouTube download requests and playlist creation."""

    def __init__(self, socketio=None, config=None):
        self.socketio = socketio
        self.config = config
        self.playlist_service = PlaylistService(config)

    async def process_download(self, url: str) -> Dict:
        """Process a YouTube download request asynchronously.

        This method handles the entire download workflow:
        1. Download the video/audio
        2. Process chapters if available
        3. Create a playlist in the database
        4. Send notifications about the progress
        """
        download_id = str(uuid4())
        notifier = DownloadNotifier(self.socketio, download_id)

        try:
            # Initial notification
            await notifier.notify(
                status="pending", message="Download request received, preparing..."
            )

            # Create downloader with async progress callback
            # The callback will pass through all status updates from the downloader
            downloader = YouTubeDownloader(
                upload_folder=self.config.upload_folder,
                progress_callback=lambda p_data: notifier.notify(**p_data),
            )

            # Download the video
            # This will send progress notifications via the callback
            result = await downloader.download(url)

            # Notify that we're saving to the database
            await notifier.notify(
                status="saving_playlist",
                message="Download complete, saving playlist to database...",
            )

            # Process the result
            base_folder = Path(self.config.upload_folder).name
            relative_path = Path(base_folder) / result["folder"]

            playlist_data = {
                "title": result["title"],
                "youtube_id": result["id"],
                "folder": str(relative_path),
                "tracks": result.get("chapters", []),
            }

            # Add to database
            playlist_id = self.playlist_service.add_playlist(playlist_data)

            # Send completion notification
            await notifier.notify(
                status="complete",
                playlist_id=playlist_id,
                message=f'Playlist "{result["title"]}" created successfully with {len(result.get("chapters", []))} tracks!',
            )

            # Emit a dedicated event for playlist updates to help frontend refresh its
            # data
            if self.socketio:
                await self.socketio.emit(
                    "playlists_updated",
                    {
                        "action": "created",
                        "playlist_id": playlist_id,
                        "playlist_title": result["title"],
                        "tracks_count": len(result.get("chapters", [])),
                    },
                )

            return {"status": "success", "playlist_id": playlist_id, "data": result}

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Download failed: {str(e)}")
            await notifier.notify(
                status="error",
                error=str(e),
                message=f"An error occurred during download: {str(e)}",
            )
            raise
