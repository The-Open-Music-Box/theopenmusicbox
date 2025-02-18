# app/src/core/application.py

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.services.nfc_mapping_service import NFCMappingService
from .nfc_playlist_controller import NFCPlaylistController
from .container import Container

logger = ImprovedLogger(__name__)

class Application:
    def __init__(self, container: Container):
        self._container = container
        self._nfc_mapping = NFCMappingService(container.config.nfc_mapping_file)
        self._playlist_controller = NFCPlaylistController(
            container.audio,
            self._nfc_mapping,
            container.config.upload_folder
        )
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
                logger.log(LogLevel.INFO, "NFC reader started")
        except Exception as e:
            logger.log(LogLevel.WARNING, f"NFC setup failed: {str(e)}")

    def _handle_tag_scanned(self, tag):
        tag_uid = tag['uid'].replace(':', '').upper()
        self._playlist_controller.handle_tag_scanned(tag_uid)

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
            logger.log(LogLevel.ERROR, f"Error during cleanup: {e}")