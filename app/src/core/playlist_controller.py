import time
import asyncio
import traceback
from typing import Optional, Dict, Any, Union

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.helpers.error_handler import ErrorHandler
from app.src.module.audio_player.audio_player import AudioPlayer
from app.src.services.playlist_service import PlaylistService
from app.src.model.track import Track
from app.src.config.nfc_config import NFCConfig

logger = ImprovedLogger(__name__)

class PlaylistController:
    """
    Controller to manage the interaction between NFC tags and playlist playback.

    This class links NFC tag detection events to the audio system for playing associated playlists.
    It ensures real-time response to tag scans and handles playback control logic.
    """

    def __init__(self, audio_player: AudioPlayer, playlist_service: PlaylistService, config: Optional[NFCConfig] = None):
        """
        Initialize the playlist controller.

        Args:
            audio_player (AudioPlayer): Audio player interface instance.
            playlist_service (PlaylistService): Playlist management service instance.
            config (Optional[NFCConfig]): Configuration for NFC-related settings.
        """
        self._audio = audio_player
        self._playlist_service = playlist_service
        self._current_tag = None
        self._tag_last_seen = 0
        
        # Use provided config or default
        self._config = config or NFCConfig()
        
        # Pause threshold to avoid accidental pauses
        self._pause_threshold = self._config.pause_threshold
        
        # Reference to NFC service for coordination
        self._nfc_service = None
        
        # Variables for manual control management
        self._last_manual_action_time = 0
        self._manual_action_priority_window = self._config.manual_action_priority_window
        
        # Flag to disable automatic pause when tag is removed
        self._auto_pause_enabled = False
        
        # Async monitoring
        self._monitor_task = None
        self._stop_monitor = asyncio.Event()
        
        # Start the async monitor
        asyncio.create_task(self._start_tag_monitor())
        
    def set_nfc_service(self, nfc_service) -> None:
        """
        Configure a reference to the NFC service for coordination.
        
        Args:
            nfc_service: NFC service to use for coordination
        """
        self._nfc_service = nfc_service
        
        # Subscribe to the playback subject if available
        if hasattr(nfc_service, 'playback_subject'):
            nfc_service.playback_subject.subscribe(
                lambda tag_tuple: self.handle_tag_scanned(tag_tuple[0], tag_tuple[1])
            )
            
        logger.log(LogLevel.INFO, "NFC service reference set in PlaylistController")

    def handle_tag_scanned(self, tag_uid: str, tag_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Handle an NFC tag scan event.

        Args:
            tag_uid (str): Unique identifier of the scanned NFC tag.
            tag_data (dict, optional): Additional tag data like timestamp and flags.
        """
        try:
            # Check if a recent manual control has priority
            now = time.time()
            if now - self._last_manual_action_time < self._manual_action_priority_window:
                logger.log(LogLevel.INFO, f"Ignoring NFC tag {tag_uid} - recent manual control action")
                return
                
            # Check if the tag has the new_detection flag
            if tag_data and not tag_data.get('new_detection', True):
                logger.log(LogLevel.DEBUG, f"Ignoring duplicate tag {tag_uid} - not a new detection")
                return
                
            logger.log(LogLevel.INFO, f"[NFC] Tag detected: {tag_uid}")
            
            # Check if we're in NFC association mode
            if self._nfc_service and self._nfc_service.is_in_association_mode():
                logger.log(LogLevel.INFO, f"Ignoring tag {tag_uid} - NFC service is in association mode")
                return
                
            # Update the last seen timestamp for the tag
            self._tag_last_seen = time.time()
            
            # Check if the audio player is available
            if self._audio is None:
                logger.log(LogLevel.WARNING, f"Cannot process tag {tag_uid} - audio player is not initialized")
                return

            # If it's a new tag or if playback is finished
            if tag_uid != self._current_tag or (hasattr(self._audio, 'is_finished') and self._audio.is_finished()):
                # Process the new tag
                self._process_new_tag(tag_uid)
            # Same tag, but playback is paused - resume
            elif hasattr(self._audio, 'is_paused') and self._audio.is_paused:
                self._audio.resume()
                logger.log(LogLevel.INFO, f"Resumed playback for tag: {tag_uid}")
                
            # Enable auto-pause for tag removal
            self._auto_pause_enabled = True
                
        except Exception as e:
            ErrorHandler.log_error(e, "Error handling tag scan")
            logger.log(LogLevel.DEBUG, f"Tag scan error details: {traceback.format_exc()}")

    def _process_new_tag(self, tag_uid: str) -> None:
        """
        Process a newly detected NFC tag.

        Args:
            tag_uid (str): Unique identifier of the NFC tag.
        """
        try:
            # Find the playlist associated with this tag
            playlist_data = self._playlist_service.get_playlist_by_nfc_tag(tag_uid)
            
            if playlist_data:
                # Update current tag
                self._current_tag = tag_uid
                # Play the playlist
                self._play_playlist(playlist_data)
                logger.log(LogLevel.INFO, f"Started playlist for tag: {tag_uid}")
            else:
                logger.log(LogLevel.WARNING, f"No playlist found for tag: {tag_uid}")
                
        except Exception as e:
            ErrorHandler.log_error(e, "Error processing new tag")

    def _play_playlist(self, playlist_data: Dict[str, Any]) -> None:
        """
        Play a playlist using the audio player, with robust validation and metadata update.
        
        Args:
            playlist_data (Dict[str, Any]): Dictionary containing playlist data to play.
        """
        success = self._playlist_service.play_playlist_with_validation(playlist_data, self._audio)
        if not success:
            logger.log(LogLevel.WARNING, f"Failed to start playlist: {playlist_data.get('title', playlist_data.get('id'))}")


    async def _start_tag_monitor(self) -> None:
        """
        Start an async task to monitor NFC tag presence and automatically pause playback if the tag is removed.
        """
        self._stop_monitor.clear()
        
        async def monitor_tags():
            while not self._stop_monitor.is_set():
                try:
                    # Only pause if auto-pause is enabled
                    if self._current_tag and self._audio and hasattr(self._audio, 'is_playing') and self._audio.is_playing and self._auto_pause_enabled:
                        if time.time() - self._tag_last_seen > self._pause_threshold:
                            # Disable auto-pause before pausing
                            self._auto_pause_enabled = False
                            self._audio.pause()
                            logger.log(LogLevel.INFO, f"Paused playback for tag: {self._current_tag} (removed)")
                except Exception as e:
                    ErrorHandler.log_error(e, "Error in tag monitoring")

                await asyncio.sleep(0.2)

        self._monitor_task = asyncio.create_task(monitor_tags())
        logger.log(LogLevel.INFO, "Tag monitor task started")

    def update_playback_status_callback(self, track: Optional[Track] = None, status: str = 'unknown') -> None:
        """
        Callback for playback status updates. Should be called by the audio system when track playback status changes.

        Args:
            track (Optional[Track]): The track currently playing.
            status (str): Playback status. Expected values: 'playing', 'paused', 'stopped', etc.
        """
        # Record this action as a manual action (playback controls)
        self._last_manual_action_time = time.time()
        
        if track and track.id and status == 'playing':
            playlist_id = None
            if self._current_tag:
                playlist_data = self._playlist_service.get_playlist_by_nfc_tag(self._current_tag)
                if playlist_data:
                    playlist_id = playlist_data['id']

            if playlist_id:
                self._playlist_service.repository.update_track_counter(playlist_id, track.number)
                logger.log(LogLevel.DEBUG, f"Updated play counter for track {track.number} in playlist {playlist_id}")
                
    def on_manual_control(self, action: str) -> None:
        """
        Handle manual playback control actions from UI buttons.
        
        Args:
            action (str): Control action ('play', 'pause', 'next', 'prev', etc.)
        """
        # Record the timestamp of the manual action
        self._last_manual_action_time = time.time()
        # Disable automatic pause when user controls manually
        self._auto_pause_enabled = False
        
        logger.log(LogLevel.INFO, f"Manual control action: {action}")
        
        # Execute the requested action
        try:
            if action == 'play' or action == 'resume':
                if self._audio:
                    self._audio.resume()
            elif action == 'pause':
                if self._audio:
                    self._audio.pause()
            elif action == 'next':
                if self._audio:
                    self._audio.next_track()
            elif action == 'prev':
                if self._audio:
                    self._audio.prev_track()
            elif action == 'stop':
                if self._audio:
                    self._audio.stop()
            else:
                logger.log(LogLevel.WARNING, f"Unknown control action: {action}")
        except Exception as e:
            ErrorHandler.log_error(e, "Error executing manual control")
            logger.log(LogLevel.DEBUG, f"Control error details: {traceback.format_exc()}")
            
    async def cleanup(self) -> None:
        """
        Clean up resources used by the controller.
        """
        # Signal the monitor to stop
        if hasattr(self, '_stop_monitor'):
            self._stop_monitor.set()
        
        # Cancel the monitor task if it exists
        if hasattr(self, '_monitor_task') and self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            
        logger.log(LogLevel.INFO, "PlaylistController cleanup completed")