# app/src/services/youtube/service.py

from uuid import uuid4
from typing import Dict
from pathlib import Path

from app.src.services.notification_service import DownloadNotifier
from app.src.services.playlist_service import PlaylistService
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .downloader import YouTubeDownloader

logger = ImprovedLogger(__name__)

class YouTubeService:

    def __init__(self, socketio=None, config=None):
        self.socketio = socketio
        self.config = config
        self.playlist_service = PlaylistService(config.playlists_file)

    def process_download(self, url: str) -> Dict:
        download_id = str(uuid4())
        notifier = DownloadNotifier(self.socketio, download_id)

        try:
            downloader = YouTubeDownloader(
                upload_folder=self.config.upload_folder,
                progress_callback=lambda p: notifier.notify(status='downloading', progress=p)
            )

            result = downloader.download(url)

            base_folder = Path(self.config.upload_folder).name
            relative_path = Path(base_folder) / result['folder']

            playlist_data = {
                'title': result['title'],
                'youtube_id': result['id'],
                'folder': str(relative_path),
                'tracks': result.get('chapters', [])
            }

            playlist_id = self.playlist_service.add_playlist(playlist_data)

            notifier.notify(status='complete', playlist_id=playlist_id)

            return {
                'status': 'success',
                'playlist_id': playlist_id,
                'data': result
            }

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Download failed: {str(e)}")
            notifier.notify(status='error', error=str(e))
            raise