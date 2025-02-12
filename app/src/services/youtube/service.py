# app/src/services/youtube/service.py

from urllib.parse import urlparse
from uuid import uuid4
from typing import Dict, Any

from src.services.notification_service import DownloadNotifier
from src.services.nfc_service import NFCMappingService
from .downloader import YouTubeDownloader

def validate_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be']

class YouTubeService:
    def __init__(self, socketio, config):
        self.socketio = socketio
        self.config = config

    def process_download(self, url: str) -> Dict[str, Any]:
        download_id = str(uuid4())
        notifier = DownloadNotifier(self.socketio, download_id)

        downloader = YouTubeDownloader(
            self.config.upload_folder,
            progress_callback=notifier.notify
        )

        result = downloader.download(url)

        nfc_service = NFCMappingService(self.config.nfc_mapping_file)
        new_mapping = {
            "id": str(uuid4()),
            "type": "playlist",
            "idtagnfc": "",
            "path": result['folder']
        }
        mapping = nfc_service.read_mapping()
        mapping.append(new_mapping)
        nfc_service.save_mapping(mapping)

        notifier.notify('completed',
            folder=result['folder'],
            message='Download completed!'
        )

        return {
            "status": "success",
            "download_id": download_id,
            "folder": result['folder'],
            "mapping": new_mapping
        }