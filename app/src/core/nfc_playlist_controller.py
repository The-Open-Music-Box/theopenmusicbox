# app/src/core/nfc_playlist_controller.py

import time
from pathlib import Path
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class NFCPlaylistController:
    def __init__(self, audio_player, nfc_mapping_service, upload_folder):
        self._audio = audio_player
        self._mapping_service = nfc_mapping_service
        self._upload_folder = upload_folder
        self._current_tag = None
        self._tag_last_seen = 0
        self._pause_threshold = 1.0
        self._start_tag_monitor()

    def handle_tag_scanned(self, tag_uid: str) -> None:
        try:
            current_time = time.time()
            self._tag_last_seen = current_time

            if tag_uid != self._current_tag or self._audio.is_finished():
                self._current_tag = tag_uid
                logger.log(LogLevel.INFO, f"Processing tag: {tag_uid}")
                self._process_new_tag(tag_uid)
            elif not self._audio.is_playing and not self._audio.is_finished():
                self._audio.resume()

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling tag: {str(e)}")

    def _process_new_tag(self, tag_uid: str) -> None:
        mapping = self._mapping_service.read_mapping()
        playlist = next((item for item in mapping
                        if item['idtagnfc'] == tag_uid
                        and item['type'] == 'playlist'), None)
        if playlist:
            self._play_playlist(playlist)

    def _play_playlist(self, playlist: dict) -> None:
        try:
            base_path = Path(self._upload_folder) / playlist['path']
            track_paths = [
                str(base_path / track['filename'])
                for track in playlist['tracks']
                if Path(base_path / track['filename']).exists()
            ]

            if track_paths:
                self._audio.set_playlist(track_paths)
                logger.log(LogLevel.INFO, f"Started playlist: {playlist['title']}")
            else:
                logger.log(LogLevel.WARNING, f"No valid tracks found for playlist: {playlist['title']}")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error playing playlist: {str(e)}")

    def _start_tag_monitor(self) -> None:
        def monitor_tags():
            while True:
                if self._current_tag and self._audio.is_playing:
                    if time.time() - self._tag_last_seen > self._pause_threshold:
                        self._audio.pause()
                time.sleep(0.2)

        import threading
        self._monitor_thread = threading.Thread(target=monitor_tags)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()