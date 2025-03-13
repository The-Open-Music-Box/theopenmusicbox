# app/src/core/container.py

from typing import Optional
from abc import ABC, abstractmethod
from eventlet.semaphore import Semaphore

from src.config import Config
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.module.gpio.gpio_interface import GPIOInterface
from src.module.gpio.gpio_factory import get_gpio_controller
from src.module.nfc.nfc_interface import NFCInterface
from src.module.nfc.nfc_factory import get_nfc_handler
from src.helpers.exceptions import AppError
from src.module.audio_player.audio_interface import AudioPlayerInterface
from src.module.audio_player.audio_factory import get_audio_player
from src.services.notification_service import PlaybackSubject

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
    def gpio(self) -> GPIOInterface:
        if not self._gpio:
            try:
                self._gpio = get_gpio_controller()
                logger.log(LogLevel.INFO, "GPIO initialized")
            except AppError as e:
                logger.log(LogLevel.ERROR, f"GPIO init failed: {e}")
                raise
        return self._gpio

    @property
    def nfc(self) -> Optional[NFCInterface]:
        if not self._nfc:
            try:
                self._nfc = get_nfc_handler(self.bus_lock)
                logger.log(LogLevel.INFO, "NFC initialized")
            except AppError as e:
                logger.log(LogLevel.WARNING, f"NFC hardware not available: {str(e)}")
                self._nfc = None
        return self._nfc

    @property
    def audio(self) -> Optional[AudioPlayerInterface]:
        if not self._audio:
            try:
                self._audio = get_audio_player(self._playback_subject)
                logger.log(LogLevel.INFO, "Audio initialized")
            except AppError as e:
                logger.log(LogLevel.WARNING, f"Audio hardware not available: {str(e)}")
                self._audio = None
        return self._audio

    def cleanup(self):
        logger.log(LogLevel.INFO, "Starting container cleanup")

        # Clean up NFC
        if self._nfc:
            try:
                self._nfc.cleanup()
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error cleaning up NFC: {e}")
            self._nfc = None

        # Clean up GPIO
        if self._gpio:
            try:
                self._gpio.cleanup_all()
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error cleaning up GPIO: {e}")
            self._gpio = None

        # Clean up audio
        if self._audio:
            try:
                self._audio.cleanup()
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error cleaning up audio: {e}")
            self._audio = None

        # Release bus lock if held
        try:
            if self.bus_lock and self.bus_lock.locked():
                self.bus_lock.release()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error releasing bus lock: {e}")
