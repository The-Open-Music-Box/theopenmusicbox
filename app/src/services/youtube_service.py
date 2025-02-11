# app/src/services/youtube_service.py

import yt_dlp
from pathlib import Path
from urllib.parse import urlparse
import re
import eventlet

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .nfc_service import NFCMappingService

logger = ImprovedLogger(__name__)

class YouTubeDownloader:
    def __init__(self, socketio, download_id):
        self.socketio = socketio
        self.download_id = download_id
        self.current_file = None

    def emit_status(self, status, **data):
        self.socketio.emit('download_progress', {
            'download_id': self.download_id,
            'status': status,
            **data
        })
        eventlet.sleep(0)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0)
            filename = Path(d['filename']).name

            if self.current_file != filename:
                self.current_file = filename
                self.emit_status('downloading', filename=filename, phase='start')

            if total > 0:
                self.emit_status('downloading',
                    filename=filename,
                    phase='progress',
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    progress=round((downloaded / total) * 100, 2),
                    speed=d.get('speed', 0),
                    eta=d.get('eta', 0)
                )

        elif d['status'] == 'finished':
            self.emit_status('processing',
                phase='converting',
                filename=Path(d.get('filename', '')).name
            )

        elif d['status'] == 'error':
            self.emit_status('error', error=str(d.get('error', 'Unknown error')))

    def download(self, url: str, upload_folder: str, nfc_mapping_file: str) -> dict:
        try:
            # Extraction des infos
            with yt_dlp.YoutubeDL({'extract_flat': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = self._sanitize_title(info['title'])

            # Préparation du dossier
            target_dir = Path(upload_folder) / title
            target_dir.mkdir(parents=True, exist_ok=True)

            # Configuration du téléchargement
            options = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'extract_flat': True,
                'split_chapters': True,
                'outtmpl': str(target_dir / '%(title)s - %(section_number)s - %(section_title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook]
            }

            # Téléchargement
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

            self.emit_status('completed',
                folder=title,
                message='Download completed!'
            )

            from uuid import uuid4
            nfc_service = NFCMappingService(nfc_mapping_file)
            new_mapping = {
                "id": str(uuid4()),
                "type": "playlist",
                "idtagnfc": "",
                "path": title
            }
            mapping = nfc_service.read_mapping()
            mapping.append(new_mapping)
            nfc_service.save_mapping(mapping)

            return {
                'folder': title,
                'youtube_id': info['id'],
                'mapping': new_mapping
            }

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Download error: {str(e)}")
            self.emit_status('error', error=str(e))
            raise

    @staticmethod
    def _sanitize_title(title: str) -> str:
        return re.sub(r'[^\w\s-]', '', title).strip()

def validate_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be']