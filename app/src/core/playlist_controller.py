import time
import asyncio
import threading
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

    Playback state is determined strictly through the public properties `is_playing` and `is_paused` on the audio player.
    """

    def __init__(self, audio_player: Optional[AudioPlayer] = None, playlist_service: Optional[PlaylistService] = None, config: Optional[NFCConfig] = None):
        """
        Initialize the playlist controller.

        Args:
            audio_player: Optional audio player instance
            playlist_service: Optional playlist service instance
            config: Optional configuration for NFC-related settings
        """
        self._audio = audio_player
        self._playlist_service = playlist_service
        self._nfc_service = None
        self._current_tag = None
        self._auto_pause_enabled = False
        self._tag_last_seen = 0
        self._tag_presence_time = 0
        self._tag_absence_time = 0
        self._last_manual_action_time = 0
        self._manual_action_priority_window = 5
        self._pause_lock = threading.Lock()

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

        # Async monitor is NOT started automatically to allow robust testing.
        # Call self.start_monitoring() explicitly from an async context to start monitoring.

    async def start_monitoring(self):
        """
        Start the async tag monitor. Must be called from an async context.
        """
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._start_tag_monitor())

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
        Handle a tag scan event strictly according to architecture use cases (A-E).
        See README_ARCHITECTURE.md for detailed expected behaviors.
        """
        try:
            current_time = time.time()
            self._tag_presence_time = current_time
            self._tag_last_seen = current_time
            
            # Store previous tag to detect changes
            previous_tag = self._current_tag
            self._current_tag = tag_uid  # Set current tag immediately to ensure it's set even if an exception occurs
            
            # Ignore scan if in association mode, manual override, duplicate scan, or audio unavailable
            if self._should_ignore_tag_scan(tag_uid, tag_data):
                return
            
            playlist_data = self._playlist_service.get_playlist_by_nfc_tag(tag_uid)
            has_playlist = playlist_data is not None
            playlist_name = playlist_data.get('title', 'Unknown') if has_playlist else 'None'
            logger.log(LogLevel.INFO, f"[NFC] Tag detected: {tag_uid} (Playlist: {playlist_name})")
            
            # Robust audio state detection
            is_playing = False
            is_paused = False
            is_finished = False
            if self._audio:
                is_playing = getattr(self._audio, 'is_playing', False)
                is_paused = getattr(self._audio, 'is_paused', False)
                is_finished = getattr(self._audio, 'is_finished', lambda: False)()
            
            # CASE A/E: New tag with playlist (always load and start from beginning)
            if has_playlist and (previous_tag is None or tag_uid != previous_tag):
                logger.log(LogLevel.INFO, "CASE A/E: New or different tag with playlist - loading and starting playlist from beginning")
                self._playlist_service.play_playlist_with_validation(playlist_data, self._audio)
                self._auto_pause_enabled = True
                return
            
            # CASE F: Same tag with finished playlist (restart from beginning)
            if has_playlist and tag_uid == previous_tag and is_finished:
                logger.log(LogLevel.INFO, "CASE F: Same tag with finished playlist - restarting playlist from beginning")
                self._playlist_service.play_playlist_with_validation(playlist_data, self._audio)
                self._auto_pause_enabled = True
                return
            
            # CASE B: Same tag, playback paused (resume at paused position)
            if has_playlist and tag_uid == previous_tag and not is_playing:
                logger.log(LogLevel.INFO, "CASE B: Same tag with playlist detected while paused - resuming playback at paused position")
                if self._audio:
                    self._audio.resume()
                self._auto_pause_enabled = True
                return
            
            # CASE C: Tag not associated with any playlist
            if not has_playlist:
                logger.log(LogLevel.INFO, "CASE C: Tag without playlist - no action taken")
                return
            
            # Safety: Same tag, already playing (continue, no state change)
            if has_playlist and tag_uid == previous_tag and is_playing:
                logger.log(LogLevel.DEBUG, "Same tag detected during playback - continuing (no action)")
                self._auto_pause_enabled = True
                return
            
            # Fallback: Log as unhandled
            logger.log(LogLevel.WARNING, f"[NFC] Unhandled case: tag={tag_uid}, current_tag={previous_tag}, has_playlist={has_playlist}, is_playing={is_playing}, is_paused={is_paused}")
            logger.log(LogLevel.INFO, "No specific action taken for this tag scan event")
        except Exception as e:
            ErrorHandler.log_error(e, f"Error handling tag scan: {str(e)}")
            logger.log(LogLevel.ERROR, f"Exception in handle_tag_scanned: {str(e)}")
            # Ensure tag is still set even if an error occurs
            self._current_tag = tag_uid

    def _should_ignore_tag_scan(self, tag_uid: str, tag_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if a tag scan should be ignored based on:
        - NFC association mode active
        - Recent manual action (manual_action_priority_window)
        - Duplicate detection (not a new_detection)
        - Audio player not ready
        """
        if self._nfc_service and self._nfc_service.is_in_association_mode():
            logger.log(LogLevel.INFO, f"Ignoring tag {tag_uid} - NFC service is in association mode")
            return True
        now = time.time()
        if now - self._last_manual_action_time < self._manual_action_priority_window:
            logger.log(LogLevel.INFO, f"Ignoring NFC tag {tag_uid} - recent manual control action")
            return True
        if tag_data and not tag_data.get('new_detection', True):
            logger.log(LogLevel.DEBUG, f"Ignoring duplicate tag {tag_uid} - not a new detection")
            return True
        if not self._audio or not hasattr(self._audio, 'is_playing'):
            logger.log(LogLevel.WARNING, "Audio player not initialized or missing required methods")
            return True
        return False

    def _extract_tag_info(self, tag_uid: str, tag_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Extract and format tag information for logging purposes.

        Args:
            tag_uid: The UID of the scanned tag
            tag_data: Optional additional data about the tag

        Returns:
            str: Formatted tag information string
        """
        if not tag_data:
            return ""

        playlist_id = tag_data.get('playlist_id')
        name = tag_data.get('name', 'Unknown')
        return f" (Playlist: {name}, ID: {playlist_id})"

    def _get_audio_player_state(self) -> str:
        """
        Récupère l'état actuel du lecteur audio sous forme de chaîne pour le débogage.

        Returns:
            str: Une représentation textuelle de l'état du lecteur audio
        """
        if not self._audio:
            return "Audio player not initialized"

        state_parts = []

        # Propriétés de base
        if hasattr(self._audio, 'is_playing'):
            state_parts.append(f"is_playing={self._audio.is_playing}")
        if hasattr(self._audio, 'is_paused'):
            state_parts.append(f"is_paused={self._audio.is_paused}")
        if hasattr(self._audio, 'is_finished') and callable(getattr(self._audio, 'is_finished')):
            state_parts.append(f"is_finished={self._audio.is_finished()}")

        # Position actuelle
        if hasattr(self._audio, '_current_position'):
            state_parts.append(f"current_position={self._audio._current_position:.2f}s")
        if hasattr(self._audio, '_paused_position'):
            state_parts.append(f"paused_position={self._audio._paused_position:.2f}s")

        # Piste actuelle
        if hasattr(self._audio, '_current_track_index'):
            state_parts.append(f"track_index={self._audio._current_track_index}")

        return ", ".join(state_parts)

    def _process_new_tag(self, tag_uid: str, tag_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Process a newly detected NFC tag.

        Args:
            tag_uid (str): Unique identifier of the NFC tag.
            tag_data (Optional[Dict[str, Any]]): Additional data associated with the tag.

        Returns:
            bool: True if a playlist was successfully loaded and started, False otherwise
        """
        try:
            # Always update current tag immediately
            self._current_tag = tag_uid
            # Find the playlist associated with this tag
            playlist_data = self._playlist_service.get_playlist_by_nfc_tag(tag_uid)

            if playlist_data:
                # Play the playlist
                self._play_playlist(playlist_data)
                logger.log(LogLevel.INFO, f"Started playlist for tag: {tag_uid}")
                return True
            else:
                logger.log(LogLevel.WARNING, f"No playlist found for tag: {tag_uid}")
                # Important: Ne pas reprendre la lecture si aucune playlist n'est associée à ce tag
                # Le tag actuel reste celui qu'on vient de scanner, mais on ne fait rien de plus
                return False

        except (ValueError, KeyError, TypeError) as e:
            ErrorHandler.log_error(e, f"Error processing tag {tag_uid}: {str(e)}")
            return False
        except Exception as e:
            ErrorHandler.log_error(e, f"Unexpected error processing tag {tag_uid}: {str(e)}")
            logger.log(LogLevel.ERROR, f"Exception details: {traceback.format_exc()}")
            return False

    def _play_playlist(self, playlist_data: Dict[str, Any]) -> None:
        """
        Play a playlist using the audio player, with robust validation and metadata update.

        Args:
            playlist_data (Dict[str, Any]): Dictionary containing playlist data to play.
        """
        success = self._playlist_service.play_playlist_with_validation(playlist_data, self._audio)
        if not success:
            logger.log(LogLevel.WARNING, f"Failed to start playlist: {playlist_data.get('title', playlist_data.get('id'))}")

    def handle_tag_absence(self) -> None:
        """
        Handle the absence (removal) of an NFC tag. Auto-pause playback if enabled.
        """
        # Utiliser un verrou pour éviter les problèmes de concurrence
        with self._pause_lock:
            # Vérifier si nous avons un lecteur audio, si l'auto-pause est activée
            # et si le lecteur est en train de jouer
            current_time = time.time()
            self._tag_absence_time = current_time

            if self._auto_pause_enabled and self._audio:
                if hasattr(self._audio, 'is_playing') and self._audio.is_playing:
                    # Calculer précisément combien de temps le tag était présent
                    tag_present_duration = current_time - self._tag_presence_time

                    # Mettre en pause la lecture
                    self._audio.pause()
                    logger.log(LogLevel.INFO, f"Auto-paused playback because tag was removed (tag present for {tag_present_duration:.2f}s)")

                    # Désactiver la pause automatique jusqu'à la prochaine détection de tag
                    self._auto_pause_enabled = False
                else:
                    logger.log(LogLevel.DEBUG, "Tag removed but playback already paused or stopped")
            else:
                if not self._auto_pause_enabled:
                    logger.log(LogLevel.DEBUG, "Tag removed but auto-pause is disabled")
                elif not self._audio:
                    logger.log(LogLevel.WARNING, "Tag removed but no audio player available")
                else:
                    logger.log(LogLevel.DEBUG, "Tag removed but no action taken")


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
                except (AttributeError, RuntimeError) as e:
                    ErrorHandler.log_error(e, f"Audio player error in tag monitoring: {str(e)}")
                except Exception as e:
                    ErrorHandler.log_error(e, f"Unexpected error in tag monitoring: {str(e)}")
                    logger.log(LogLevel.ERROR, f"Exception details: {traceback.format_exc()}")

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

    def handle_manual_action(self, action: str) -> None:
        """
        Handle manual control actions (play/pause/next/prev/stop).
        This is called when a user directly interacts with the UI.

        Args:
            action (str): Action to perform (play, pause, next, prev, stop).
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

    def on_manual_control(self, action: str) -> None:
        """
        Handle manual playback control actions from UI buttons.

        Args:
            action (str): Control action ('play', 'pause', 'next', 'prev', etc.)
        """
        # Simple wrapper to the handle_manual_action method with cleaner name for external calls
        self.handle_manual_action(action)
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