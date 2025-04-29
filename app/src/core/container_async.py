# app/src/core/container_async.py

from typing import Optional
from app.src.config import Config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.nfc.nfc_handler import NFCHandler
from app.src.services.notification_service import PlaybackSubject
from app.src.services.playlist_service import PlaylistService

logger = ImprovedLogger(__name__)

class ContainerAsync:
    def __init__(self, config: Config):
        self._config = config
        self._nfc = None
        self._led_hat = None
        self._playback_subject = PlaybackSubject()
        self._playlist_service = PlaylistService(config)
        # AUDIO: always provide a working audio player for dev (macOS)
        from app.src.module.audio_player.audio_factory import get_audio_player
        self._audio = get_audio_player(self._playback_subject)
        # TODO: Initialiser les autres modules nécessaires en mode async-friendly

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

    # Ajoute ici les méthodes/props nécessaires pour la stack async

    async def cleanup_async(self):
        """
        Clean up all async resources before application shutdown.
        Extend this method to close DB connections, stop background tasks, etc.
        """
        import logging
        logger = logging.getLogger("ContainerAsync")
        logger.info("Starting async resource cleanup...")

        # Example: if you have async DB connections, close them here
        # if self._db:
        #     await self._db.close()

        # Example: if you have background tasks, signal them to stop and await completion
        # if self._monitor_task:
        #     self._monitor_task.cancel()
        #     try:
        #         await self._monitor_task
        #     except asyncio.CancelledError:
        #         pass

        logger.info("Async resource cleanup complete.")
