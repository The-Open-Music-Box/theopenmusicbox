# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

# MARK: - Imports
import asyncio
import os
import threading
import time
import traceback
from pathlib import Path

from app.src.config.nfc_config import NFCConfig
from app.src.core.playlist_controller import PlaylistController
from app.src.module.nfc.nfc_factory import get_nfc_handler

# Application imports
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.nfc_service import NFCService
from app.src.services.playlist_service import PlaylistService

# MARK: - Constants
PROGRESS_LOG_INTERVAL = 10  # Log track progress every 10%
SYNC_TIMEOUT_SECONDS = 15  # Maximum wait time for playlist synchronization

# MARK: - Logger
logger = ImprovedLogger(__name__)

# MARK: - Application Class


class Application:
    """Main application class for TheOpenMusicBox backend.

    Manages initialization and lifecycle of various components.
    """

    # MARK: - Initialization
    def __init__(self, config):
        """Initialize the Application instance.

        Args:
            config: Configuration object
        """
        self._config = config
        self._nfc_lock = None

        # Initialize playlist service with configuration
        self._playlists = PlaylistService(self._config)

        # Synchronize playlists at startup with protection against blocking
        self._sync_playlists()

        # Create NFC config with auto-pause setting from app config
        nfc_config = NFCConfig()

        # Apply auto-pause setting directly from app config (already converted to
        # proper type)
        nfc_config.auto_pause_enabled = self._config.get("auto_pause_enabled")

        # Initialize playlist controller (async version) with config
        self._playlist_controller = PlaylistController(
            None, self._playlists, nfc_config
        )

        # Initialize NFC components in constructor (basic setup)
        # These will be properly initialized in initialize_async
        self._nfc_handler = None
        self._nfc_service = None

        logger.log(LogLevel.INFO, "Application initialized successfully")

    async def initialize_async(self):
        """Initialize application resources asynchronously.

        Asynchronous initialization - to be called from lifespan context.
        """
        # Initialize NFC components using the dedicated method
        await self._setup_nfc()

        # Initialize audio components
        self._setup_audio()

        return self

    # MARK: - NFC Event Handling
    async def handle_nfc_event(self, tag_data):
        """Handle an NFC event triggered by tag detection.

        Handles NFC tag events (scan or absence) by routing them to the
        PlaylistController. This method provides a public API, encapsulating
        the interaction with _playlist_controller.

        Args:
            tag_data: The data associated with the NFC tag event.
        """
        try:
            if isinstance(tag_data, dict) and tag_data.get("absence"):
                logger.log(LogLevel.DEBUG, "Handling NFC tag absence event.")
                self._playlist_controller.handle_tag_absence()
            else:
                uid = None
                full_data = None
                if isinstance(tag_data, dict):
                    uid = tag_data.get("uid")
                    full_data = tag_data  # Pass full dict if available
                    logger.log(
                        LogLevel.DEBUG,
                        f"Handling NFC tag scanned event (dict): UID={uid}",
                    )
                else:
                    uid = tag_data  # Assume it's the UID string
                    logger.log(
                        LogLevel.DEBUG,
                        f"Handling NFC tag scanned event (string): UID={uid}",
                    )

                if uid:
                    self._playlist_controller.handle_tag_scanned(uid, full_data)
                else:
                    logger.log(
                        LogLevel.WARNING,
                        f"Received NFC tag event with no usable UID: {tag_data}",
                    )

        except Exception as e:  # Catch broader exceptions for robustness
            # Log the error using the improved logger
            logger.log(
                LogLevel.ERROR,
                f"Error processing NFC event in Application: {e}",
                exc_info=True,
            )
            # Avoid raising exceptions from here unless absolutely necessary,
            # as this is typically called from an event handler.

    # MARK: - Playlist Synchronization
    def _sync_playlists(self):
        """Synchronize playlists in database with files from upload folder.

        With robust error handling and timeouts.
        """
        try:
            logger.log(LogLevel.INFO, "Starting playlist synchronization")
            if hasattr(self._config, "upload_folder"):
                upload_folder = Path(self._config.upload_folder)
            elif hasattr(self._config, "config") and hasattr(
                self._config.config, "upload_folder"
            ):
                upload_folder = Path(self._config.config.upload_folder)
            else:
                raise AttributeError(
                    "Config object must have an 'upload_folder' attribute or a 'config' property with 'upload_folder'."
                )

            # Get the app directory path (parent of src)
            app_dir = Path(__file__).parent.parent.parent

            # Make relative paths absolute from the app directory
            if not upload_folder.is_absolute():
                upload_folder = app_dir / upload_folder
            if not upload_folder.exists():
                logger.log(
                    LogLevel.WARNING, f"Upload folder doesn't exist: {upload_folder}"
                )
                upload_folder.mkdir(parents=True, exist_ok=True)
                logger.log(LogLevel.INFO, f"Created upload folder: {upload_folder}")

            sync_completed = False
            sync_results = {"error": None, "stats": {}}

            def sync_worker():
                try:
                    sync_results["stats"] = self._playlists.sync_with_filesystem()
                    sync_results["error"] = None
                    nonlocal sync_completed
                    sync_completed = True
                except Exception as e:
                    sync_results["error"] = str(e)
                    sync_completed = True

            # Run synchronization in a separate thread
            sync_thread = threading.Thread(target=sync_worker)
            sync_thread.daemon = True
            sync_thread.start()

            # Wait for synchronization with timeout
            start_time = time.time()
            while (
                not sync_completed and time.time() - start_time < SYNC_TIMEOUT_SECONDS
            ):
                time.sleep(0.2)

            if not sync_completed:
                logger.log(
                    LogLevel.ERROR,
                    f"Playlist synchronization timed out after {SYNC_TIMEOUT_SECONDS}s",
                )
                return

            if sync_results["error"]:
                logger.log(
                    LogLevel.ERROR,
                    f"Playlist synchronization failed: {sync_results['error']}",
                )
                return

            # Log results
            stats = sync_results["stats"]
            logger.log(
                LogLevel.INFO,
                "Playlist synchronization completed",
                extra={
                    "playlists_added": stats.get("playlists_added", 0),
                    "playlists_updated": stats.get("playlists_updated", 0),
                    "tracks_added": stats.get("tracks_added", 0),
                    "tracks_removed": stats.get("tracks_removed", 0),
                },
            )

        except Exception as e:
            logger.log(
                LogLevel.ERROR, f"Playlist synchronization setup failed: {str(e)}"
            )
            logger.log(LogLevel.DEBUG, f"Sync error details: {traceback.format_exc()}")

    # MARK: - NFC Setup
    async def _setup_nfc(self):
        """Set up and initialize NFC reader using asyncio."""
        try:
            # In our application architecture, the NFC handler and service should
            # already be initialized by the ContainerAsync class.
            # We'll just ensure our playlist controller is linked to the NFC service.

            # Try to get the NFC service from fastapi app's container
            container = None
            nfc_service_from_container = None

            try:
                # Try to import and access FastAPI app to get its container
                from app.main import app

                if hasattr(app, "container") and app.container:
                    container = app.container
                    if hasattr(container, "nfc") and container.nfc:
                        nfc_service_from_container = container.nfc
                        logger.log(
                            LogLevel.INFO, "Found existing NFC service from container"
                        )
            except (ImportError, AttributeError):
                logger.log(
                    LogLevel.WARNING,
                    "Couldn't access container NFC service from FastAPI app",
                )

            if nfc_service_from_container and self._nfc_service is None:
                # Use the existing NFC service from container
                self._nfc_service = nfc_service_from_container
                # Get NFC handler through proper access methods
                if hasattr(self._nfc_service, "get_nfc_handler"):
                    self._nfc_handler = self._nfc_service.get_nfc_handler()
                else:
                    # Fallback for backward compatibility
                    self._nfc_handler = getattr(self._nfc_service, "_nfc_handler", None)
                logger.log(LogLevel.INFO, "Using NFC service from container")
            elif self._nfc_service is None:
                # Create a new NFC service if we couldn't get one from container
                # Create a lock for I2C bus (if needed)
                if self._nfc_lock is None:
                    self._nfc_lock = asyncio.Lock()

                # Initialize the NFC handler via the async factory
                self._nfc_handler = await get_nfc_handler(self._nfc_lock)
                logger.log(
                    LogLevel.INFO,
                    f"NFC handler initialized: {type(self._nfc_handler).__name__}",
                )

                # Initialize the NFC service with handler and playlist controller
                self._nfc_service = NFCService(
                    socketio=None, nfc_handler=self._nfc_handler
                )

                # If we have access to the container, update its NFC service
                if container:
                    # Use setter methods if available
                    if hasattr(container, "set_nfc_service"):
                        container.set_nfc_service(self._nfc_service)
                    elif hasattr(container, "_nfc_service"):
                        container._nfc_service = self._nfc_service

                    if hasattr(container, "set_nfc_handler"):
                        container.set_nfc_handler(self._nfc_handler)
                    elif hasattr(container, "_nfc_handler"):
                        container._nfc_handler = self._nfc_handler

                    logger.log(LogLevel.INFO, "Updated container's NFC service")

            # Always ensure bi-directional link between playlist controller and NFC
            # service
            if hasattr(self._playlist_controller, "set_nfc_service"):
                self._playlist_controller.set_nfc_service(self._nfc_service)
                logger.log(LogLevel.INFO, "PlaylistController linked with NFC service")
            else:
                logger.log(
                    LogLevel.WARNING,
                    "PlaylistController doesn't have set_nfc_service method - coordination with NFC service not possible",
                )

            # Make sure the playlist controller is set on the NFC service
            if hasattr(self._nfc_service, "set_playlist_controller"):
                self._nfc_service.set_playlist_controller(self._playlist_controller)
                logger.log(LogLevel.INFO, "Set playlist controller on NFC service")

            # Load playlist mapping if needed
            # Check if playlists are loaded through a proper method or attribute
            playlists_loaded = False
            if hasattr(self._nfc_service, "has_playlists_loaded"):
                playlists_loaded = self._nfc_service.has_playlists_loaded()
            elif hasattr(self._nfc_service, "_playlists"):
                playlists_loaded = bool(getattr(self._nfc_service, "_playlists", None))

            if not playlists_loaded:
                playlists = self._playlists.get_all_playlists(page=1, page_size=1000)
                self._nfc_service.load_mapping(playlists)
                logger.log(LogLevel.INFO, "Playlist mapping loaded into NFC service")

            # Ensure the NFC reader is started
            if self._nfc_handler and hasattr(self._nfc_handler, "start_nfc_reader"):
                # Check if already started to avoid duplicate starts
                try:
                    await self._nfc_handler.start_nfc_reader()
                    logger.log(
                        LogLevel.INFO, "NFC reader hardware started successfully"
                    )
                except Exception as reader_error:
                    # This might fail if already started, which is fine
                    logger.log(
                        LogLevel.WARNING,
                        f"NFC reader may already be started: {reader_error}",
                    )

            logger.log(LogLevel.INFO, "NFC system fully initialized and ready")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize NFC: {e}")
            logger.log(
                LogLevel.DEBUG, f"NFC setup error details: {traceback.format_exc()}"
            )

    # MARK: - Internal Event Handlers
    def _handle_nfc_error(self, error):
        """Handle NFC reader errors.

        Args:
            error: Error information
        """
        logger.log(LogLevel.ERROR, f"NFC error: {error}")

    # MARK: - Audio Setup
    def _setup_audio(self):
        """Set up and initialize audio system for playlist playback.

        This method ensures that the audio system is properly
        initialized and connected to the playlist controller. It sets
        environment variables for audio playback, creates an audio
        player instance, and handles any errors that may occur.
        """
        # Set environment variables at the application level
        os.environ["SDL_AUDIODRIVER"] = "alsa"  # Explicitly use ALSA
        os.environ["SDL_AUDIODEV"] = "hw:1"  # Target WM8960 (card 1)
        os.environ["SDL_VIDEODRIVER"] = "dummy"  # Disable video mode

        container_audio = None

        # First try to get the audio player from the container if available
        try:
            # Attempt to access the FastAPI app container
            from app.main import app

            if hasattr(app, "container") and app.container:
                if hasattr(app.container, "audio"):
                    container_audio = app.container.audio
                    logger.log(
                        LogLevel.INFO,
                        f"Using audio player from container: {type(container_audio).__name__}",
                    )
        except (ImportError, AttributeError) as e:
            logger.log(
                LogLevel.WARNING,
                f"Could not access container audio from FastAPI app: {e}",
            )

        # If we got the audio player from the container, connect it to the
        # playlist controller
        if container_audio:
            if self._playlist_controller:
                # Set audio player on playlist controller
                if hasattr(self._playlist_controller, "set_audio_player"):
                    self._playlist_controller.set_audio_player(container_audio)
                else:
                    # Fallback for backward compatibility
                    self._playlist_controller._audio = container_audio
                logger.log(
                    LogLevel.INFO, "Audio player connected to playlist controller"
                )
                return
            else:
                logger.log(
                    LogLevel.WARNING,
                    "Playlist controller not available to connect audio player",
                )
                return

        # If we couldn't get the audio player from the container, create one
        try:
            from app.src.module.audio_player.audio_factory import get_audio_player
            from app.src.services.notification_service import PlaybackSubject

            # Get a PlaybackSubject instance
            playback_subject = PlaybackSubject.get_instance()

            # Create an audio player
            try:
                audio_player = get_audio_player(playback_subject)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Failed to create audio player: {str(e)}")
                raise RuntimeError(f"Failed to initialize audio system: {str(e)}")

            # Set it on the playlist controller
            if self._playlist_controller:
                # Set audio player on playlist controller
                if hasattr(self._playlist_controller, "set_audio_player"):
                    self._playlist_controller.set_audio_player(audio_player)
                else:
                    # Fallback for backward compatibility
                    self._playlist_controller._audio = audio_player
                logger.log(
                    LogLevel.INFO,
                    f"Created and connected new {type(audio_player).__name__} to playlist controller",
                )
            else:
                logger.log(
                    LogLevel.ERROR,
                    "Playlist controller not available to connect new audio player",
                )
                raise RuntimeError(
                    "Audio initialization failed: playlist controller not available"
                )
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error creating audio player: {str(e)}")
            # Traceback already imported at the top of the file
            logger.log(
                LogLevel.DEBUG,
                f"Audio creation error details: {traceback.format_exc()}",
            )
            raise RuntimeError(f"Failed to initialize audio system: {str(e)}")

    def _handle_playback_status(self, event):
        """Handle playback status updates.

        Args:
            event: Playback status event
        """
        try:
            if event.event_type == "status":
                logger.log(LogLevel.INFO, "Playback status update", extra=event.data)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling playback status: {str(e)}")

    def _handle_track_progress(self, event):
        """Handle track progress updates.

        Args:
            event: Track progress event
        """
        try:
            if event.event_type == "progress":
                # Only log progress at a reasonable interval to avoid log flooding
                if event.data.get("progress_percent", 0) % PROGRESS_LOG_INTERVAL == 0:
                    logger.log(
                        LogLevel.DEBUG, "Track progress update", extra=event.data
                    )
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling track progress: {str(e)}")

    def _handle_audio_error(self, error):
        """Handle audio system errors.

        Args:
            error: Error information
        """
        logger.log(LogLevel.ERROR, f"Audio error: {error}")

    # MARK: - Application Lifecycle
    async def run(self):
        """Start and run the application asynchronously."""
        try:
            logger.log(LogLevel.INFO, "Starting application")
            # Start the playlist controller
            if hasattr(self._playlist_controller, "start"):
                await self._playlist_controller.start()
            # Keep the application running
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error running application: {e}")
            logger.log(
                LogLevel.DEBUG, f"Runtime error details: {traceback.format_exc()}"
            )
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up all resources before application shutdown."""
        logger.log(LogLevel.INFO, "Starting application cleanup")
        try:
            # Additional cleanup specific to Application
            if hasattr(self, "_playlist_controller") and hasattr(
                self._playlist_controller, "cleanup"
            ):
                await self._playlist_controller.cleanup()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during application cleanup: {e}")
            logger.log(
                LogLevel.DEBUG, f"Cleanup error details: {traceback.format_exc()}"
            )
