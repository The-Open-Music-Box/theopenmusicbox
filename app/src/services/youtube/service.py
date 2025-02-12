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
    def __init__(self, socketio, config):
        self.socketio = socketio
        self.config = config
        self.nfc_service = NFCMappingService(config.nfc_mapping_file)

    def process_download(self, url: str) -> Dict:
        download_id = str(uuid4())
        notifier = DownloadNotifier(self.socketio, download_id)

        try:
            downloader = YouTubeDownloader(
                upload_folder=self.config.upload_folder,
                progress_callback=lambda p: notifier.notify(**p)
            )

            result = downloader.download(url)
            logger.log(LogLevel.INFO, f"Download result received: {result}")

            playlist_data = {
                'title': result['title'],
                'youtube_id': result['id'],
                'path': result['folder'],
                'tracks': result.get('chapters', [])
            }
            logger.log(LogLevel.INFO, f"Playlist data prepared: {playlist_data}")

            playlist_id = self.nfc_service.add_playlist(playlist_data)
            logger.log(LogLevel.INFO, f"Playlist created with ID: {playlist_id}")

            return {
                'status': 'success',
                'playlist_id': playlist_id,
                'data': result
            }

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Process failed with error: {str(e)}", exc_info=True)
            notifier.notify(status='error', error=str(e))
            raise