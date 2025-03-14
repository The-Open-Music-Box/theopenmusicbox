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
        self._setup_led()
        self._setup_nfc()
        self._setup_audio()

    def _setup_led(self):
        # Utiliser le LED hat du container
        try:
            # Le LED hat est déjà initialisé via le container
            led_hat = self._container.led_hat
            if not led_hat:
                logger.log(LogLevel.WARNING, "LED hat not available")
                return

            # Démarrer l'animation de cercle rotatif
            led_hat.start_animation(
                "rotating_circle",
                color=(10, 10, 10),
                background_color=(0, 0, 0),
                segment_length=5,
                rotation_time=4.0,
                continuous=True
            )
            logger.log(LogLevel.INFO, "LED animation started successfully")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error starting LED animation: {str(e)}")
            import traceback
            logger.log(LogLevel.DEBUG, f"Error details: {traceback.format_exc()}")

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
            if self._container.audio and self._container.playback_subject:
                # Subscribe to playback status events for logging
                self._container.playback_subject.status_stream.subscribe(
                    on_next=self._handle_playback_status,
                    on_error=self._handle_audio_error
                )
                # Subscribe to track progress events for logging
                self._container.playback_subject.progress_stream.subscribe(
                    on_next=self._handle_track_progress,
                    on_error=self._handle_audio_error
                )
                logger.log(LogLevel.INFO, "Audio system ready")
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Audio setup failed: {str(e)}")

    def _handle_playback_status(self, event):
        try:
            if event.event_type == 'status':
                logger.log(LogLevel.INFO, "Playback status update", extra=event.data)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling playback status: {str(e)}")

    def _handle_track_progress(self, event):
        try:
            if event.event_type == 'progress':
                logger.log(LogLevel.DEBUG, "Track progress update", extra=event.data)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling track progress: {str(e)}")

    def _handle_audio_error(self, error):
        logger.log(LogLevel.ERROR, f"Audio error: {error}")

    def cleanup(self):
        logger.log(LogLevel.INFO, "Starting application cleanup")
        try:
            if self._container:
                if self._container.nfc:
                    self._container.nfc.cleanup()
                if self._container.audio:
                    self._container.audio.cleanup()
            # Arrêter l'animation LED et nettoyer
            if hasattr(self, '_led_hat'):
                self._led_hat.stop_animation()
                self._led_hat.clear()
                logger.log(LogLevel.INFO, "LED animation stopped")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during cleanup: {e}")