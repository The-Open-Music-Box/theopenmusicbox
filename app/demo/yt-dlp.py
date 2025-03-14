# app/demo/yt-dlp.py

import yt_dlp
import logging
from pathlib import Path

# Log configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('youtube-downloader')

def download_and_split():
    url = "https://www.youtube.com/watch?v=QR_HmidODnM"
    logger.info(f"Starting download: {url}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'outtmpl': '%(title)s.%(ext)s',
        'download_archive': 'downloaded.txt',
        'split_chapters': True,
        'paths': {'home': str(Path.cwd())},
        'progress_hooks': [log_progress],
        'logger': logger
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Extracting video information...")
            info = ydl.extract_info(url, download=True)
            logger.info(f"Download completed: {info.get('title', 'Unknown title')}")

            chapters = info.get('chapters', [])
            if chapters:
                logger.info(f"Number of chapters found: {len(chapters)}")
                for chapter in chapters:
                    logger.info(f"Chapter extracted: {chapter.get('title', 'Unknown chapter')}")
            else:
                logger.warning("No chapters found in the video")

    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        raise

def log_progress(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
        if total > 0:
            percentage = (d['downloaded_bytes'] / total) * 100
            logger.info(f"Downloading: {percentage:.1f}%")
    elif d['status'] == 'finished':
        logger.info("Audio download completed, starting post-processing...")

if __name__ == "__main__":
    try:
        download_and_split()
    except KeyboardInterrupt:
        logger.info("Script manually stopped")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")