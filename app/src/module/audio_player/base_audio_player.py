# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Base Audio Player Implementation.

This module provides a base class for audio player implementations to
reduce code duplication and standardize common functionality across
different hardware implementations.
"""

import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional

from app.src.model.playlist import Playlist

# Import models directly to avoid circular imports
from enum import Enum, auto

# Local version of models to avoid circular imports


class AudioState(Enum):
    """Enum representing the possible states of audio playback."""
    
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()
    LOADING = auto()
    ERROR = auto()


class PlaybackEvent(Enum):
    """Enum representing playback events that can be emitted."""
    
    TRACK_STARTED = auto()
    TRACK_ENDED = auto()
    TRACK_PAUSED = auto()
    TRACK_RESUMED = auto()
    PLAYLIST_STARTED = auto()
    PLAYLIST_ENDED = auto()
    PLAYBACK_ERROR = auto()
    PROGRESS_UPDATE = auto()


from app.src.config import config
from app.src.services.notification_service import PlaybackSubject
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

# MARK: - Base Audio Player Class


class BaseAudioPlayer(ABC):
    """Base class for audio player implementations.

    Provides common functionality for state management, notification,
    and threading that can be shared across different hardware
    implementations.
    """

    # MARK: - Initialization
    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        """Initialize the base audio player.

        Args:
            playback_subject: Optional observer for playback events
        """
        self._playback_subject = playback_subject
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        self._volume = config.audio.default_volume  # Use centralized config
        self._progress_thread = None
        self._stop_progress = False
        self._track_start_time = 0
        self._paused_position = 0
        self._pause_time = 0
        self._state_lock = threading.RLock()  # Lock for thread safety

    # MARK: - State Properties
    @property
    def is_playing(self) -> bool:
        """Check if the player is currently playing audio.

        Returns:
            bool: True if audio is playing, False otherwise.
        """
        with self._state_lock:
            return self._is_playing

    @property
    def is_paused(self) -> bool:
        """Check if the player is paused.

        Returns:
            bool: True if the player is paused (not playing, but a track is loaded), False otherwise.
        """
        with self._state_lock:
            return not self._is_playing and self._current_track is not None

    def is_finished(self) -> bool:
        """Check if the current playlist has finished playing.

        Returns:
            bool: True if the playlist has finished, False otherwise.
        """
        return False

    # MARK: - Playback Control
    def play(self, track: str) -> None:
        """Play a specific track by filename or path.

        Args:
            track: The filename or path of the audio track to play.
        """
        raise NotImplementedError("Subclasses must implement play()")

    def pause(self) -> None:
        """Pause playback."""
        raise NotImplementedError("Subclasses must implement pause()")

    def resume(self) -> None:
        """Resume playback from a paused state."""
        raise NotImplementedError("Subclasses must implement resume()")

    def stop(self, clear_playlist: bool = True) -> None:
        """Stop playback.

        Args:
            clear_playlist: Whether to clear the playlist when stopping
        """
        raise NotImplementedError("Subclasses must implement stop()")

    def set_volume(self, volume: int) -> bool:
        """Set the playback volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            bool: True if setting volume was successful
        """
        with self._state_lock:
            self._volume = max(0, min(100, volume))
        return True

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
        with self._state_lock:
            if self._progress_thread:
                self._stop_progress = True
                try:
                    self._progress_thread.join(timeout=2.0)
                except Exception as e:
                    logger.log(
                        LogLevel.WARNING, f"Error stopping progress thread: {str(e)}"
                    )
                self._progress_thread = None

    # MARK: - Playlist Management
    def set_playlist(self, playlist: Playlist) -> bool:
        """Set the current playlist and start playback.

        Args:
            playlist: The playlist to set

        Returns:
            bool: True if the playlist was set and playback started
        """
        with self._state_lock:
            self.stop()
            self._playlist = playlist

            if self._playlist and self._playlist.tracks:
                logger.log(
                    LogLevel.INFO,
                    f"Set playlist with {len(self._playlist.tracks)} tracks",
                )
                return self.play_track(1)

            logger.log(LogLevel.WARNING, "Empty playlist or no tracks")
            return False

    def play_track(self, track_number: int) -> bool:
        """Play a specific track from the playlist.

        Args:
            track_number: The track number to play

        Returns:
            bool: True if the track was played successfully
        """
        raise NotImplementedError("Subclasses must implement play_track()")

    def next_track(self) -> None:
        """Advance to the next track in the playlist."""
        with self._state_lock:
            if not self._current_track or not self._playlist:
                logger.log(LogLevel.WARNING, "No current track or playlist")
                return

            next_number = self._current_track.number + 1
            if next_number <= len(self._playlist.tracks):
                logger.log(LogLevel.INFO, f"Moving to next track: {next_number}")
                self.play_track(next_number)
            else:
                logger.log(LogLevel.INFO, "Reached end of playlist")
                self.stop()

    def previous_track(self) -> None:
        """Return to the previous track in the playlist."""
        with self._state_lock:
            if not self._current_track or not self._playlist:
                logger.log(LogLevel.WARNING, "No current track or playlist")
                return

            prev_number = self._current_track.number - 1
            if prev_number > 0:
                logger.log(LogLevel.INFO, f"Moving to previous track: {prev_number}")
                self.play_track(prev_number)
            else:
                logger.log(LogLevel.INFO, "Already at first track")

    # MARK: - Thread Management
    def _start_progress_thread(self) -> None:
        """Start the progress tracking thread."""
        with self._state_lock:
            if self._progress_thread:
                self._stop_progress = True
                self._progress_thread.join(timeout=1.0)

            self._stop_progress = False
            self._progress_thread = threading.Thread(
                target=self._progress_loop, daemon=True
            )
            self._progress_thread.start()
            logger.log(LogLevel.INFO, "Progress tracking thread started")

    def _progress_loop(self) -> None:
        """Progress tracking loop that runs in a separate thread."""
        last_playing_state = False
        tick = 0

        while not self._stop_progress:
            tick += 1

            # Thread-safe access to state
            with self._state_lock:
                is_playing = self._is_playing
                current_track = self._current_track
                playback_subject = self._playback_subject

            if is_playing and playback_subject and current_track:
                # Update and send progress information
                self._update_progress()

                # Check for track end - this should be implemented by subclasses
                current_playing_state = self._check_playback_active()
                if last_playing_state and not current_playing_state:
                    logger.log(
                        LogLevel.INFO,
                        f"[PROGRESS_LOOP] Detected track end at tick={tick}",
                    )
                    self._handle_track_end()
                last_playing_state = current_playing_state

            time.sleep(0.1)

    def _check_playback_active(self) -> bool:
        """Check if playback is currently active.

        This method should be overridden by subclasses to provide
        hardware-specific implementation.

        Returns:
            bool: True if playback is active, False otherwise
        """
        return self.is_playing

    def _update_progress(self) -> None:
        """Update and send current progress."""

    def _handle_track_end(self) -> None:
        """Handle end of track notification."""
        with self._state_lock:
            if self._is_playing and self._current_track and self._playlist:
                next_number = self._current_track.number + 1
                if next_number <= len(self._playlist.tracks):
                    logger.log(
                        LogLevel.INFO, f"Track ended, playing next: {next_number}"
                    )
                    self.play_track(next_number)
                else:
                    logger.log(LogLevel.INFO, "Playlist ended")
                    self.stop()

    # MARK: - Notification
    def _notify_playback_status(self, status: str) -> None:
        """Notify playback status change in a non-blocking way.

        Args:
            status: The playback status ('playing', 'paused', 'stopped', etc.)
        """
        if not self._playback_subject:
            return

        # Use a separate thread for notification to prevent blocking the control
        # operations
        try:
            import threading

            notification_thread = threading.Thread(
                target=self._send_notification,
                args=(status,),
                daemon=True,  # Use daemon thread to avoid blocking app shutdown
            )
            notification_thread.start()
            # We don't join() the thread - let it run independently
        except Exception as e:
            # Log but continue if threading fails
            logger.log(
                LogLevel.ERROR,
                "Failed to send notification in background",
                extra={"error": str(e)},
            )

    def _send_notification(self, status: str):
        """Send playback status notification to observers.

        Args:
            status: Playback status string (e.g., 'playing', 'paused', 'stopped')
        """
        try:
            # Gather info with minimal lock time
            playlist_info = None
            track_info = None

            if status != "stopped":
                # Use a quick, separate lock acquisition to minimize contention
                with self._state_lock:
                    # Capture just the data we need quickly
                    playlist = self._playlist
                    current_track = self._current_track

                # Process the data outside the lock
                if playlist:
                    playlist_info = {
                        "name": playlist.name,
                        "track_count": len(playlist.tracks) if playlist.tracks else 0,
                    }

                if current_track:
                    # Note: this could call _get_track_duration which might be slow
                    # But we're in a separate thread so it won't block the main
                    # operation
                    track_info = {
                        "number": current_track.number,
                        "title": current_track.title or f"Track {current_track.number}",
                        "filename": current_track.filename,
                        "duration": self._get_track_duration(current_track.path),
                    }

            # Finally send notification (potentially slow operation)
            self._playback_subject.notify_playback_status(
                status, playlist_info, track_info
            )
            logger.log(
                LogLevel.INFO,
                "Playback status update",
                extra={
                    "status": status,
                    "playlist": playlist_info,
                    "current_track": track_info,
                },
            )
        except Exception as e:
            logger.log(
                LogLevel.ERROR, "Error in notification thread", extra={"error": str(e)}
            )

    def _get_track_duration(self, file_path: Path) -> float:
        """Get track duration in seconds.

        Args:
            file_path: Path to the audio file

        Returns:
            float: Duration in seconds
        """
        return 0.0
