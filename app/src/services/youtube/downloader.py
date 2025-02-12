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

    def _handle_progress(self, progress: dict):
        if self.progress_callback and progress.get('status'):
            if progress['status'] == 'downloading':
                total = progress.get('total_bytes', 0) or progress.get('total_bytes_estimate', 0)
                if total > 0:
                    percentage = (progress['downloaded_bytes'] / total) * 100
                    logger.log(LogLevel.INFO, f"Download progress: {percentage:.1f}%")
            elif progress['status'] == 'finished':
                logger.log(LogLevel.INFO, "Download finished, starting post-processing")

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
            'force_overwrites': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Log les chapitres spécifiquement
                chapters = info.get('chapters', [])
                logger.log(LogLevel.INFO, f"Chapters structure: {chapters}")

                result = {
                    'title': info.get('title', 'Unknown'),
                    'id': info.get('id', 'Unknown'),
                    'folder': str(self.upload_folder),
                    'chapters': chapters
                }

                # Log le résultat final
                logger.log(LogLevel.INFO, f"Final result structure: {result}")

                return result

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Download failed with error: {str(e)}", exc_info=True)
            raise