from app.src.config import Config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.notification_service import PlaybackSubject
from app.src.services.playlist_service import PlaylistService
from app.src.module.audio_player.audio_factory import get_audio_player
from app.src.services.nfc_service import NFCService

logger = ImprovedLogger(__name__)

class ContainerAsync:
    """
    Asynchronous dependency injection container for backend services.

    Provides access to configuration, NFC, LED, playback subject, playlist service, and audio player.
    Handles initialization and cleanup of async resources required by the application.
    """
    def __init__(self, config: Config):
        self._config = config
        self._nfc_handler = None
        self._nfc_service = None
        self._led_hat = None
        self._playback_subject = PlaybackSubject()
        self._playlist_service = PlaylistService(config)
        self._audio = get_audio_player(self._playback_subject)
        self._init_socketio = None  # Will be set before async initialization
        
        # NFC service will be properly initialized in initialize_async()

    @property
    def config(self):
        return self._config

    @property
    def playback_subject(self):
        return self._playback_subject

    @property
    def nfc(self):
        return self._nfc_service
        
    def set_init_socketio(self, socketio):
        """Store the Socket.IO reference for initialization"""
        self._init_socketio = socketio
        
    def set_socketio(self, socketio):
        """Update the NFCService with the Socket.IO instance"""
        if self._nfc_service:
            self._nfc_service.socketio = socketio

    @property
    def audio(self):
        """
        Returns a working AudioPlayer instance for playback.
        - On macOS/dev: returns a MockAudioPlayer (simulated playback)
        - On Raspberry Pi: returns the real hardware player
        """
        return self._audio

    async def initialize_async(self):
        """
        Initialize async resources that require coroutines.
        This method should be called after the container creation but before using any async resources.
        """
        try:
            # Initialiser le NFC de manière asynchrone
            from app.src.module.nfc.nfc_factory import get_nfc_handler
            import asyncio
            
            # Create a lock asyncio for the I2C bus
            bus_lock = asyncio.Lock()
            
            # Get the NFC handler via the factory
            self._nfc_handler = await get_nfc_handler(bus_lock)
            
            # Create the NFC service with the handler and with playlist controller
            # It will be linked with the playlist controller in Application._setup_nfc
            self._nfc_service = NFCService(
                socketio=None,  # Will be set by main.py's set_socketio call
                nfc_handler=self._nfc_handler
            )
            
            # Start the NFC reader
            await self._nfc_handler.start_nfc_reader()
            
            # Load playlists into the NFC service
            playlists = self._playlist_service.get_all_playlists(page=1, page_size=1000)
            self._nfc_service.load_mapping(playlists)
            
            logger.log(LogLevel.INFO, f"NFC handler and service fully initialized: {type(self._nfc_handler).__name__}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Could not initialize NFC handler: {e}")
            import traceback
            logger.log(LogLevel.DEBUG, f"NFC initialization error details: {traceback.format_exc()}")
    
    async def cleanup_async(self):
        """
        Clean up all async resources before application shutdown.
        Extend this method to close DB connections, stop background tasks, etc.
        """
        logger.log(LogLevel.INFO, "Starting async resource cleanup...")
        
        # Nettoyer les ressources NFC
        if self._nfc_handler:
            try:
                await self._nfc_handler.cleanup()
                logger.log(LogLevel.INFO, "NFC resources cleaned up")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error cleaning up NFC: {e}")
        
        logger.log(LogLevel.INFO, "Async resource cleanup complete.")
