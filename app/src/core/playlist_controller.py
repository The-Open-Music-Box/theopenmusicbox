# app/src/core/playlist_controller.py

import time
from pathlib import Path
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.model.track import Track
from src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class PlaylistController:
    def __init__(self, audio_player, playlists_service, upload_folder):
        self._audio = audio_player
        self._mapping_service = playlists_service
        self._upload_folder = upload_folder
        self._current_tag = None
        self._tag_last_seen = 0
        self._pause_threshold = 1.0
        self._start_tag_monitor()

    def handle_tag_scanned(self, tag_uid: str) -> None:
        try:
            self._tag_last_seen = time.time()

            if tag_uid != self._current_tag or (hasattr(self._audio, 'is_finished') and self._audio.is_finished()):
                self._current_tag = tag_uid
                logger.log(LogLevel.INFO, f"Processing tag: {tag_uid}")
                self._process_new_tag(tag_uid)
            elif not self._audio.is_playing and (not hasattr(self._audio, 'is_finished') or not self._audio.is_finished()):
                self._audio.resume()

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling tag: {str(e)}")

    def _process_new_tag(self, tag_uid: str) -> None:
        try:
            mapping = self._mapping_service.read_mapping()
            playlist = next((item for item in mapping
                            if item.get('idtagnfc') == tag_uid
                            and item.get('type') == 'playlist'), None)
            if playlist:
                self._play_playlist(playlist)
                logger.log(LogLevel.INFO, f"Playing playlist for tag: {tag_uid}")
            else:
                logger.log(LogLevel.WARNING, f"No playlist found for tag: {tag_uid}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error processing tag: {str(e)}")

    def _play_playlist(self, playlist_data: dict) -> None:
        try:
            base_path = Path(self._upload_folder) / playlist_data['path']

            tracks = []
            track_number = 1

            for track_info in playlist_data.get('tracks', []):
                file_path = base_path / track_info.get('filename', '')
                if file_path.exists():
                    track = Track(
                        number=track_number,
                        title=track_info.get('title', f'Track {track_number}'),
                        filename=track_info.get('filename', ''),
                        path=file_path
                    )
                    tracks.append(track)
                    track_number += 1

            if tracks:
                playlist_obj = Playlist(
                    name=playlist_data.get('title', 'Unknown Playlist'),
                    tracks=tracks
                )

                # Passer l'objet Playlist à la méthode set_playlist
                result = self._audio.set_playlist(playlist_obj)
                if result:
                    logger.log(LogLevel.INFO, f"Started playlist: {playlist_data['title']} with {len(tracks)} tracks")
                else:
                    logger.log(LogLevel.WARNING, f"Failed to start playlist: {playlist_data['title']}")
            else:
                logger.log(LogLevel.WARNING, f"No valid tracks found for playlist: {playlist_data['title']}")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error playing playlist: {str(e)}", extra={"error": str(e)})
            import traceback
            logger.log(LogLevel.DEBUG, f"Traceback: {traceback.format_exc()}")

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