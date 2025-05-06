import time
import threading
import traceback

from typing import Optional, Dict, Any

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.audio_player.audio_player import AudioPlayer
from app.src.services.playlist_service import PlaylistService
from app.src.model.track import Track

logger = ImprovedLogger(__name__)

class PlaylistController:
    """
    Controller to manage the interaction between NFC tags and playlist playback.

    This class links NFC tag detection events to the audio system for playing associated playlists.
    It ensures real-time response to tag scans and handles playback control logic.
    """

    def __init__(self, audio_player: AudioPlayer, playlist_service: PlaylistService):
        """
        Initialize the playlist controller.

        Args:
            audio_player (AudioPlayer): Audio player interface instance.
            playlist_service (PlaylistService): Playlist management service instance.
        """
        self._audio = audio_player
        self._playlist_service = playlist_service
        self._current_tag = None
        self._tag_last_seen = 0
        self._pause_threshold = 1.0  # seconds before pausing after tag removal
        self._monitor_thread = None
        self._start_tag_monitor()

    def handle_tag_scanned(self, tag_uid: str) -> None:
        """
        Handle an NFC tag scan event.

        Args:
            tag_uid (str): Unique identifier of the scanned NFC tag.
        """
        try:
            logger.log(LogLevel.INFO, f"[NFC] Tag detected: {tag_uid}")
            # Update the last seen timestamp for the tag
            self._tag_last_seen = time.time()

            if tag_uid != self._current_tag or (hasattr(self._audio, 'is_finished') and self._audio.is_finished()):
                # New tag detected or previous playlist finished
                self._current_tag = tag_uid
                logger.log(LogLevel.INFO, f"Processing tag: {tag_uid}")
                self._process_new_tag(tag_uid)
            elif not self._audio.is_playing and (not hasattr(self._audio, 'is_finished') or not self._audio.is_finished()):
                # Same tag, but playback is paused - resume playback
                self._audio.resume()
                logger.log(LogLevel.INFO, f"Resumed playback for tag: {tag_uid}")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling tag: {str(e)}")
            logger.log(LogLevel.DEBUG, f"Tag handling error details: {traceback.format_exc()}")

    def _process_new_tag(self, tag_uid: str) -> None:
        """
        Process a newly detected NFC tag.

        Args:
            tag_uid (str): Unique identifier of the NFC tag.
        """
        try:
            # Retrieve the playlist associated with the tag
            playlist_data = self._playlist_service.get_playlist_by_nfc_tag(tag_uid)

            if playlist_data:
                # Play the playlist
                self._play_playlist(playlist_data)
                logger.log(LogLevel.INFO, f"Playing playlist for tag: {tag_uid}")
            else:
                logger.log(LogLevel.WARNING, f"No playlist found for tag: {tag_uid}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error processing tag: {str(e)}")

    def _play_playlist(self, playlist_data: Dict[str, Any]) -> None:
        """
        Play a playlist using the audio player, with robust validation and metadata update.
        Args:
            playlist_data (Dict[str, Any]): Dictionary containing playlist data to play.
        """
        success = self._playlist_service.play_playlist_with_validation(playlist_data, self._audio)
        if not success:
            logger.log(LogLevel.WARNING, f"Failed to start playlist: {playlist_data.get('title', playlist_data.get('id'))}")


    def _start_tag_monitor(self) -> None:
        """
        Start a background thread to monitor NFC tag presence and automatically pause playback if the tag is removed.
        """
        def monitor_tags():
            while True:
                try:
                    if self._current_tag and self._audio and self._audio.is_playing:
                        if time.time() - self._tag_last_seen > self._pause_threshold:
                            self._audio.pause()
                            logger.log(LogLevel.INFO, f"Paused playback for tag: {self._current_tag} (removed)")
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"Error in tag monitoring: {str(e)}")

                time.sleep(0.2)

        self._monitor_thread = threading.Thread(target=monitor_tags)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        logger.log(LogLevel.INFO, "Tag monitor thread started")

    def update_playback_status_callback(self, track: Optional[Track] = None, status: str = 'unknown') -> None:
        """
        Callback for playback status updates. Should be called by the audio system when track playback status changes.

        Args:
            track (Optional[Track]): The track currently playing.
            status (str): Playback status. Expected values: 'playing', 'paused', 'stopped', etc.
        """
        if track and track.id and status == 'playing':
            playlist_id = None
            if self._current_tag:
                playlist_data = self._playlist_service.get_playlist_by_nfc_tag(self._current_tag)
                if playlist_data:
                    playlist_id = playlist_data['id']

            if playlist_id:
                self._playlist_service.repository.update_track_counter(playlist_id, track.number)
                logger.log(LogLevel.DEBUG, f"Updated play counter for track {track.number} in playlist {playlist_id}")