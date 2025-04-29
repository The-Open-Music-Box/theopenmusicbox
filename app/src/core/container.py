# app/src/core/container.py

from typing import Optional
from abc import ABC, abstractmethod
from gevent.lock import Semaphore
from gevent import Timeout

from src.config import Config
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.module.gpio.gpio_controller import GPIOController
from src.module.gpio.gpio_factory import get_gpio_controller
from src.module.nfc.nfc_handler import NFCHandler
from src.module.nfc.nfc_factory import get_nfc_handler
from src.helpers.exceptions import AppError
from src.module.audio_player.audio_factory import get_audio_player
from src.module.audio_player.audio_player import AudioPlayer
from src.module.audio_player.audio_hardware import AudioPlayerHardware
from src.module.ledhat.ledhat_factory import get_led_hat
from src.services.notification_service import PlaybackSubject
from src.services.playlist_service import PlaylistService

logger = ImprovedLogger(__name__)

class EventPublisher(ABC):
    @abstractmethod
    def publish_event(self, event_type: str, data: dict):
        pass

class SocketIOPublisher(EventPublisher):
    def __init__(self, socketio):
        self._socketio = socketio

    def publish_event(self, event_type: str, data: dict):
        self._socketio.emit(event_type, data)

class Container:
    def __init__(self, config: Config, event_publisher: Optional[EventPublisher] = None):
        self._config = config
        self._event_publisher = event_publisher
        self._playback_subject = PlaybackSubject()
        self._gpio = None
        self._nfc = None
        self._audio = None
        self._led_hat = None
        self.bus_lock = Semaphore()

        # Set up event forwarding if event_publisher is provided
        if self._event_publisher:
            self._setup_event_publisher()

    def _setup_event_publisher(self):
        """Set up forwarding of Rx events to WebSocket"""
        self._playback_subject.status_stream.subscribe(
            on_next=lambda event: self._event_publisher.publish_event('playback_status', event.data) if event.event_type == 'status' else None
        )
        self._playback_subject.progress_stream.subscribe(
            on_next=lambda event: self._event_publisher.publish_event('track_progress', event.data) if event.event_type == 'progress' else None
        )

    @property
    def config(self) -> Config:
        return self._config

    @property
    def event_publisher(self) -> EventPublisher:
        return self._event_publisher

    @property
    def playback_subject(self) -> PlaybackSubject:
        return self._playback_subject

    @property
    def gpio(self) -> GPIOController:
        if not self._gpio:
            try:
                self._gpio = get_gpio_controller(self.bus_lock)
                logger.log(LogLevel.INFO, "GPIO initialized")
            except AppError as e:
                logger.log(LogLevel.ERROR, f"GPIO init failed: {e}")
                raise
        return self._gpio

    @property
    def nfc(self) -> Optional[NFCHandler]:
        if not self._nfc:
            try:
                self._nfc = get_nfc_handler(self.bus_lock)
                logger.log(LogLevel.INFO, "NFC initialized")
            except AppError as e:
                logger.log(LogLevel.WARNING, f"NFC hardware not available: {str(e)}")
                self._nfc = None
        return self._nfc

    @property
    def audio(self) -> Optional[AudioPlayer]:
        if not self._audio:
            try:
                self._audio = get_audio_player(self._playback_subject)
                logger.log(LogLevel.INFO, "Audio initialized")
            except AppError as e:
                logger.log(LogLevel.WARNING, f"Audio hardware not available: {str(e)}")
                self._audio = None
        return self._audio

    @property
    def led_hat(self):
        if not self._led_hat:
            try:
                self._led_hat = get_led_hat(12)
                logger.log(LogLevel.INFO, "LED hat initialized")
            except Exception as e:
                # Capture toutes les exceptions possibles pour rendre le composant vraiment optionnel
                logger.log(LogLevel.WARNING, f"LED hat not available: {str(e)}")
                self._led_hat = None
        return self._led_hat

    @property
    def playlist_service(self) -> PlaylistService:
        """
        Obtient ou crée le service de playlists.

        Returns:
            Instance du service de playlists
        """
        if not hasattr(self, '_playlist_service'):
            try:
                from src.services.playlist_service import PlaylistService
                self._playlist_service = PlaylistService(self.config)
                logger.log(LogLevel.INFO, "Playlist service initialized")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Failed to initialize playlist service: {str(e)}")
                raise
        return self._playlist_service

    def cleanup(self):
        logger.log(LogLevel.INFO, "Starting container cleanup")
        cleanup_timeout = 5  # seconds

        def cleanup_with_timeout(resource_name, cleanup_func):
            try:
                with Timeout(cleanup_timeout):
                    cleanup_func()
                logger.log(LogLevel.INFO, f"{resource_name} cleanup completed")
            except Timeout:
                logger.log(LogLevel.ERROR, f"{resource_name} cleanup timed out after {cleanup_timeout} seconds")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error cleaning up {resource_name}: {e}")

        # Clean up NFC
        if self._nfc:
            cleanup_with_timeout("NFC", self._nfc.cleanup)
            self._nfc = None

        # Clean up GPIO
        if self._gpio:
            cleanup_with_timeout("GPIO", self._gpio.cleanup_all)
            self._gpio = None

        # Clean up audio
        if self._audio:
            cleanup_with_timeout("Audio", self._audio.cleanup)
            self._audio = None

        # Clean up LED hat
        if self._led_hat:
            cleanup_with_timeout("LED hat", self._led_hat.cleanup)
            self._led_hat = None

        # Release bus lock if held
        try:
            if self.bus_lock and self.bus_lock.locked():
                with Timeout(1):
                    self.bus_lock.release()
        except (Timeout, Exception) as e:
            logger.log(LogLevel.ERROR, f"Error releasing bus lock: {e}")

        # Force garbage collection to ensure resources are freed
        import gc
        gc.collect()

        logger.log(LogLevel.INFO, "Container cleanup completed")
