from app.src.config import Config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.notification_service import PlaybackSubject
from app.src.services.playlist_service import PlaylistService
from app.src.module.audio_player.audio_factory import get_audio_player

logger = ImprovedLogger(__name__)

class ContainerAsync:
    """
    Asynchronous dependency injection container for backend services.

    Provides access to configuration, NFC, LED, playback subject, playlist service, and audio player.
    Handles initialization and cleanup of async resources required by the application.
    """
    def __init__(self, config: Config):
        self._config = config
        self._nfc = None
        self._led_hat = None
        self._playback_subject = PlaybackSubject()
        self._playlist_service = PlaylistService(config)
        self._audio = get_audio_player(self._playback_subject)

        # --- NFC handler initialization ---
        try:
            from app.src.module.nfc.nfc_factory import get_nfc_handler
            from gevent.lock import Semaphore
            bus_lock = Semaphore()
            self._nfc = get_nfc_handler(bus_lock)
            logger.log(LogLevel.INFO, f"NFC handler initialized: {type(self._nfc).__name__}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Could not initialize NFC handler: {e}")
            self._nfc = None

    @property
    def config(self):
        return self._config

    @property
    def playback_subject(self):
        return self._playback_subject

    @property
    def nfc(self):
        return self._nfc

    @property
    def audio(self):
        """
        Returns a working AudioPlayer instance for playback.
        - On macOS/dev: returns a MockAudioPlayer (simulated playback)
        - On Raspberry Pi: returns the real hardware player
        """
        return self._audio

    async def cleanup_async(self):
        """
        Clean up all async resources before application shutdown.
        Extend this method to close DB connections, stop background tasks, etc.
        """
        logger.log(LogLevel.INFO, "Starting async resource cleanup...")
        logger.log(LogLevel.INFO, "Async resource cleanup complete.")
