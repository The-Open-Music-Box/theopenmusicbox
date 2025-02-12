# app/src/services/youtube/downloader.py

import yt_dlp
from pathlib import Path
from typing import Callable, Dict, Any
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class YouTubeDownloader:
    def __init__(self, upload_folder: str, progress_callback: Callable = None):
        self.upload_folder = Path(upload_folder)
        self.progress_callback = progress_callback
        self._last_percentage = 0

    def _handle_progress(self, progress: dict):
        if progress['status'] != 'downloading':
            return

        total = progress.get('total_bytes', 0) or progress.get('total_bytes_estimate', 0)
        if not total:
            return

        percentage = int((progress['downloaded_bytes'] / total) * 100)

        # Log seulement tous les 10%
        if percentage > self._last_percentage + 9:
            self._last_percentage = percentage
            logger.log(LogLevel.INFO, f"Download progress: {percentage}%")

        # Notification WebSocket sans log
        if self.progress_callback:
            self.progress_callback({
                'status': 'downloading',
                'progress': percentage,
                'downloaded_bytes': progress['downloaded_bytes'],
                'total_bytes': total
            })

    def download(self, url: str) -> Dict[str, Any]:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'outtmpl': str(self.upload_folder / '%(title)s.%(ext)s'),
            'split_chapters': True,
            'paths': {'home': str(self.upload_folder)},
            'progress_hooks': [self._handle_progress],
            'force_overwrites': True,
            'quiet': True,
            'no_warnings': True,
            'logger': None,
            'noprogress': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return {
                    'title': info.get('title', 'Unknown'),
                    'id': info.get('id', 'Unknown'),
                    'folder': str(self.upload_folder),
                    'chapters': info.get('chapters', [])
                }
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Download failed: {str(e)}")
            raise