# app/src/core/application.py

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.services.nfc_mapping_service import NFCMappingService
from pathlib import Path
from .container import Container

logger = ImprovedLogger(__name__)

class Application:
    def __init__(self, container: Container):
        self._container = container
        self._nfc_mapping = NFCMappingService(container.config.nfc_mapping_file)
        self._setup_nfc()
        self._setup_audio()

    def _setup_nfc(self):
        try:
            if self._container.nfc:
                self._container.nfc.start_nfc_reader()
                self._container.nfc.tag_subject.subscribe(
                    on_next=self._handle_tag_scanned,
                    on_error=self._handle_nfc_error
                )
        except Exception as e:
            logger.log(LogLevel.WARNING, f"NFC setup failed: {str(e)}")

    def _handle_tag_scanned(self, tag):
        try:
            tag_uid = tag['uid'].replace(':', '').upper()
            logger.log(LogLevel.INFO, f"Tag scanned: {tag_uid}")

            mapping = self._nfc_mapping.read_mapping()
            playlist = next((item for item in mapping if item['idtagnfc'] == tag_uid and item['type'] == 'playlist'), None)

            if playlist:
                self._play_playlist(playlist)
            else:
                logger.log(LogLevel.INFO, f"No playlist mapping found for tag: {tag_uid}")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling tag: {str(e)}")

    def _play_playlist(self, playlist):
        try:
            base_path = Path(self._container.config.upload_folder) / playlist['path']
            track_paths = [
                str(base_path / track['filename'])
                for track in playlist['tracks']
                if Path(base_path / track['filename']).exists()
            ]

            if track_paths:
                self._container.audio.set_playlist(track_paths)
                logger.log(LogLevel.INFO, f"Started playlist: {playlist['title']}")
            else:
                logger.log(LogLevel.WARNING, f"No valid tracks found for playlist: {playlist['title']}")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error playing playlist: {str(e)}")

    def _handle_nfc_error(self, error):
        logger.log(LogLevel.ERROR, f"NFC error: {error}")

    def _setup_audio(self):
        try:
            if self._container.audio:
                logger.log(LogLevel.INFO, "Audio system ready")
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Audio setup failed: {str(e)}")

    def cleanup(self):
        logger.log(LogLevel.INFO, "Starting application cleanup")
        try:
            if self._container:
                if self._container.nfc:
                    self._container.nfc.cleanup()
                if self._container.audio:
                    self._container.audio.cleanup()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during application cleanup: {e}")