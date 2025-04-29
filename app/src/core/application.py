# app/src/core/application.py

import time
import threading
from pathlib import Path
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.playlist_service import PlaylistService
from app.src.core.playlist_controller import PlaylistController
from app.src.config import Config

logger = ImprovedLogger(__name__)

class Application:
    """
    Main application class that manages initialization and lifecycle
    of various components.
    """

    def __init__(self, config):
        """
        Initialize the application with async config only (legacy DI container removed).

        Args:
            config: Configuration object
        """
        self._config = config

        # Initialize playlist service with configuration
        self._playlists = PlaylistService(self._config)

        # Synchronize playlists at startup with protection against blocking
        self._sync_playlists()

        # Initialize playlist controller (async version)
        self._playlist_controller = PlaylistController(
            None,  # audio system handled elsewhere async
            self._playlists,
            self._config
        )

        # Set up peripherals (async-compatible)
        self._setup_led()
        self._setup_nfc()
        self._setup_audio()

        logger.log(LogLevel.INFO, "Application initialized successfully")

    def _sync_playlists(self):
        """
        Synchronize playlists in database with files from upload folder.
        With robust error handling and timeouts.
        """
        try:
            logger.log(LogLevel.INFO, "Starting playlist synchronization")

            # Check that required paths exist
            # Support both Config and ContainerAsync (which exposes .config)
            if hasattr(self._config, 'upload_folder'):
                upload_folder = Path(self._config.upload_folder)
            elif hasattr(self._config, 'config') and hasattr(self._config.config, 'upload_folder'):
                upload_folder = Path(self._config.config.upload_folder)
            else:
                raise AttributeError("Config object must have an 'upload_folder' attribute or a 'config' property with 'upload_folder'.")
            if not upload_folder.exists():
                logger.log(LogLevel.WARNING, f"Upload folder doesn't exist: {upload_folder}")
                upload_folder.mkdir(parents=True, exist_ok=True)
                logger.log(LogLevel.INFO, f"Created upload folder: {upload_folder}")

            # Synchronization with timeout protection
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

            # Wait max 15 seconds for synchronization
            timeout = 15
            start_time = time.time()
            while not sync_completed and time.time() - start_time < timeout:
                time.sleep(0.2)

            if not sync_completed:
                logger.log(LogLevel.ERROR, f"Playlist synchronization timed out after {timeout}s")
                return

            if sync_results["error"]:
                logger.log(LogLevel.ERROR, f"Playlist synchronization failed: {sync_results['error']}")
                return

            # Log results
            stats = sync_results["stats"]
            logger.log(LogLevel.INFO, "Playlist synchronization completed", extra={
                "playlists_added": stats.get('playlists_added', 0),
                "playlists_updated": stats.get('playlists_updated', 0),
                "tracks_added": stats.get('tracks_added', 0),
                "tracks_removed": stats.get('tracks_removed', 0)
            })

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Playlist synchronization setup failed: {str(e)}")
            import traceback
            logger.log(LogLevel.DEBUG, f"Sync error details: {traceback.format_exc()}")

    def _setup_led(self):
        """Set up and initialize LED display."""
        logger.log(LogLevel.INFO, "Skipping LED setup: no DI container in async mode.")

    def _setup_nfc(self):
        """Set up and initialize NFC reader."""
        logger.log(LogLevel.INFO, "Skipping NFC setup: no DI container in async mode.")

    def _handle_tag_scanned(self, tag):
        """
        Handle NFC tag scan event.

        Args:
            tag: Scanned NFC tag data
        """
        tag_uid = tag['uid'].replace(':', '').upper()
        self._playlist_controller.handle_tag_scanned(tag_uid)

    def _handle_nfc_error(self, error):
        """
        Handle NFC reader errors.

        Args:
            error: Error information
        """
        logger.log(LogLevel.ERROR, f"NFC error: {error}")

    def _setup_audio(self):
        """Set up and initialize audio system (async version, no DI container)."""
        try:
            # TODO: Inject or initialize audio system in async context if needed
            logger.log(LogLevel.INFO, "Audio system setup skipped (async mode, no DI container)")
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Audio setup failed: {str(e)}")

    def _handle_playback_status(self, event):
        """
        Handle playback status updates.

        Args:
            event: Playback status event
        """
        try:
            if event.event_type == 'status':
                logger.log(LogLevel.INFO, "Playback status update", extra=event.data)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling playback status: {str(e)}")

    def _handle_track_progress(self, event):
        """
        Handle track progress updates.

        Args:
            event: Track progress event
        """
        try:
            if event.event_type == 'progress':
                # Only log progress at a reasonable interval to avoid log flooding
                if event.data.get('progress_percent', 0) % 10 == 0:  # Log every 10%
                    logger.log(LogLevel.DEBUG, "Track progress update", extra=event.data)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling track progress: {str(e)}")

    def _handle_audio_error(self, error):
        """
        Handle audio system errors.

        Args:
            error: Error information
        """
        logger.log(LogLevel.ERROR, f"Audio error: {error}")

    def cleanup(self):
        """
        Clean up all resources before application shutdown.
        """
        logger.log(LogLevel.INFO, "Starting application cleanup")
        try:
            # First stop active playback (no DI container, so skip)
            logger.log(LogLevel.INFO, "No DI container: skipping audio and peripheral cleanup")

            # Additional cleanup specific to Application
            if hasattr(self, '_playlist_controller') and hasattr(self._playlist_controller, 'cleanup'):
                self._playlist_controller.cleanup()

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during application cleanup: {e}")
            import traceback
            logger.log(LogLevel.DEBUG, f"Cleanup error details: {traceback.format_exc()}")