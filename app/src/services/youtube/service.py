# app/src/services/youtube/service.py

from uuid import uuid4
from typing import Dict
from pathlib import Path

from src.services.notification_service import DownloadNotifier
from src.services.nfc_mapping_service import NFCMappingService
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .downloader import YouTubeDownloader

logger = ImprovedLogger(__name__)

class YouTubeService:

    def __init__(self, socketio=None, config=None):
        self.socketio = socketio
        self.config = config
        self.nfc_service = NFCMappingService(config.nfc_mapping_file)

    def process_download(self, url: str) -> Dict:
        download_id = str(uuid4())
        notifier = DownloadNotifier(self.socketio, download_id)

        try:
            downloader = YouTubeDownloader(
                upload_folder=self.config.upload_folder,
                progress_callback=lambda p: notifier.notify(status='downloading', progress=p)
            )

            result = downloader.download(url)
            playlist_data = {
                'title': result['title'],
                'youtube_id': result['id'],
                'path': result['folder'],
                'tracks': result.get('chapters', [])
            }

            playlist_id = self.nfc_service.add_playlist(playlist_data)
            return {
                'status': 'success',
                'playlist_id': playlist_id,
                'data': result
            }

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Download failed: {str(e)}")
            notifier.notify(status='error', error=str(e))
            raise