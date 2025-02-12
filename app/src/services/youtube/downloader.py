# app/src/services/youtube/downloader.py

import yt_dlp
from pathlib import Path
import re
from typing import Callable, Dict, Any
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class YouTubeDownloader:
    def __init__(self, upload_folder: str, progress_callback: Callable = None):
        self.upload_folder = Path(upload_folder)
        self.progress_callback = progress_callback
        self.current_file = None

    def _progress_hook(self, d: Dict[str, Any]):
        if not self.progress_callback:
            return

        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0)
            filename = Path(d['filename']).name

            if self.current_file != filename:
                self.current_file = filename
                self.progress_callback('downloading', filename=filename, phase='start')

            if total > 0:
                self.progress_callback('downloading',
                    filename=filename,
                    phase='progress',
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    progress=round((downloaded / total) * 100, 2),
                    speed=d.get('speed', 0),
                    eta=d.get('eta', 0)
                )

        elif d['status'] == 'finished':
            self.progress_callback('processing',
                phase='converting',
                filename=Path(d.get('filename', '')).name
            )

        elif d['status'] == 'error':
            self.progress_callback('error', error=str(d.get('error', 'Unknown error')))

    def download(self, url: str) -> Dict[str, Any]:
        try:
            options = {
                'format': 'bestaudio/best',
                'extract_flat': False,  # On a besoin des données complètes
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'writethumbnail': False,
                'progress_hooks': [self._progress_hook]
            }

            # Premier passage pour extraire les infos
            with yt_dlp.YoutubeDL({'extract_flat': False}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = self._sanitize_title(info['title'])
                chapters = info.get('chapters', [])

            target_dir = self.upload_folder / title
            target_dir.mkdir(parents=True, exist_ok=True)

            if chapters:
                # Si on a des chapitres, on les télécharge séparément
                for i, chapter in enumerate(chapters, 1):
                    chapter_title = f"{i:02d}. {self._sanitize_title(chapter.get('title', f'Chapter {i}'))}"
                    options['download_ranges'] = lambda info: [[chapter['start_time'], chapter['end_time']]]
                    options['outtmpl'] = str(target_dir / f'{chapter_title}.%(ext)s')

                    with yt_dlp.YoutubeDL(options) as ydl:
                        ydl.download([url])
            else:
                # Si pas de chapitres, on télécharge la vidéo entière
                options['outtmpl'] = str(target_dir / '%(title)s.%(ext)s')
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])

            return {
                'folder': title,
                'youtube_id': info['id'],
                'has_chapters': bool(chapters)
            }

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Download error: {str(e)}")
            if self.progress_callback:
                self.progress_callback('error', error=str(e))
            raise

    @staticmethod
    def _sanitize_title(title: str) -> str:
        # Nettoyage plus agressif pour éviter les problèmes de fichiers
        clean_title = re.sub(r'[^\w\s-]', '', title)
        return clean_title.strip().replace('  ', ' ')