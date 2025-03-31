# app/src/services/youtube/downloader.py

import yt_dlp
from pathlib import Path
import os
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
        try:
            # Extraire d'abord les informations sans télécharger
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)

            # Créer un nom de dossier sécurisé à partir du titre
            safe_title = "".join([c if c.isalnum() or c in " -_" else "_" for c in info.get('title', 'Unknown')])
            playlist_folder = self.upload_folder / safe_title

            # Créer le dossier s'il n'existe pas
            playlist_folder.mkdir(exist_ok=True)

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'outtmpl': str(playlist_folder / '%(title)s.%(ext)s'),
                'split_chapters': True,
                'paths': {'home': str(playlist_folder)},
                'progress_hooks': [self._handle_progress],
                'force_overwrites': True,
                'quiet': True,
                'no_warnings': True,
                'logger': None,
                'noprogress': True
            }

            # Télécharger avec les nouvelles options
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Récupérer les chapitres ou construire une liste de pistes
                chapters = info.get('chapters', [])

                # Si pas de chapitres mais des fichiers ont été téléchargés, créer des "chapitres" manuellement
                if not chapters:
                    # Vérifier si c'est une playlist
                    entries = info.get('entries', [])
                    if entries:
                        chapters = []
                        for idx, entry in enumerate(entries, 1):
                            chapters.append({
                                'title': entry.get('title', f'Track {idx}'),
                                'start_time': 0,
                                'end_time': entry.get('duration', 0),
                                'filename': f"{entry.get('title', f'Track {idx}')}.mp3"
                            })
                    else:
                        # Un seul fichier
                        chapters = [{
                            'title': info.get('title', 'Track 1'),
                            'start_time': 0,
                            'end_time': info.get('duration', 0),
                            'filename': f"{info.get('title', 'Track 1')}.mp3"
                        }]

                # Pour les chapitres téléchargés, s'assurer qu'ils ont le bon nom de fichier
                for chapter in chapters:
                    if 'filename' not in chapter:
                        chapter['filename'] = f"{chapter.get('title', 'Unknown')}.mp3"

                return {
                    'title': info.get('title', 'Unknown'),
                    'id': info.get('id', 'Unknown'),
                    'folder': safe_title,  # Retourne le nom du dossier relatif
                    'chapters': chapters
                }
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Download failed: {str(e)}")
            raise