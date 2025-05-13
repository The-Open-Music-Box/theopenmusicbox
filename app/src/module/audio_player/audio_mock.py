"""
Mock Audio Player Implementation

This module provides the mock implementation of the AudioPlayerHardware Protocol for use in development and testing environments.
It simulates playback, playlist management, and observer notification without requiring real audio hardware, enabling robust local testing and CI workflows.

Business Logic and Architectural Notes:
- Used automatically when the application is running in a development or test environment (e.g., on macOS).
- Ensures that all backend code can be tested without actual hardware.
- Notifies observers via the PlaybackSubject for integration with real-time status updates and frontend Socket.IO.
- All methods match the AudioPlayerHardware Protocol and are invoked via the AudioPlayer wrapper.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import threading
import time
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .base_audio_player import BaseAudioPlayer # Import BaseAudioPlayer
from app.src.module.audio_player.audio_hardware import AudioPlayerHardware
from app.src.services.notification_service import PlaybackSubject
from app.src.model.track import Track
from app.src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class MockAudioPlayer(BaseAudioPlayer, AudioPlayerHardware): # Inherit from BaseAudioPlayer
    """
    MockAudioPlayer simulates audio playback for testing purposes. Playback state is exposed through public properties `is_playing` and `is_paused` for consistency with hardware implementations.
    """

    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        """
        Initialize the mock audio player.
        Args:
            playback_subject: Optional observer for playback events (used for real-time status updates)
        """
        super().__init__(playback_subject)
        self._track_duration = 180.0  # Simulated track duration in seconds
        self._track_position = 0.0
        logger.log(LogLevel.INFO, "Mock Audio Player initialized")

        # Start the progress tracking thread if a playback_subject is provided
        if playback_subject:
            self._start_progress_thread()

    def play(self, track: str) -> None:
        """
        Play a specific track by filename or path.
        Args:
            track: The filename or path of the audio track to play.
        """
        with self._state_lock:
            logger.log(LogLevel.INFO, f"Mock: Playing track {track}")

            # Simulate loading a single track
            path = Path(track)
            mock_track = Track(
                number=1,
                filename=path.name,
                path=path,
                title=path.stem
            )

            # Create a single-track playlist if we don't have one
            if not self._playlist:
                self._playlist = Playlist(name="Single Track", tracks=[mock_track])
            elif not any(t.path == path for t in self._playlist.tracks):
                # Add to existing playlist if not already there
                mock_track.number = len(self._playlist.tracks) + 1
                self._playlist.tracks.append(mock_track)

            self._current_track = mock_track
            self._is_playing = True
            self._track_start_time = time.time()
            self._notify_playback_status('playing')

    def play_track(self, track_number: int) -> bool:
        """Play a specific track from the playlist"""
        with self._state_lock:
            # Stop current playback without clearing the playlist
            self.stop(clear_playlist=False) # Use self.stop() to call MockAudioPlayer's stop

            if not self._playlist or not self._playlist.tracks:
                logger.log(LogLevel.WARNING, "Mock: No playlist or empty playlist")
                return False

            # Find the track in the playlist
            track = next((t for t in self._playlist.tracks if t.number == track_number), None)

            # If the track is not found, create a simulated track
            if not track:
                if track_number <= len(self._playlist.tracks):
                    track = self._playlist.tracks[track_number-1]
                else:
                    logger.log(LogLevel.WARNING, f"Mock: Track number {track_number} not found in playlist")
                    # Create a mock track for tests
                    track = Track(
                        number=track_number,
                        title=f"Mock Track {track_number}",
                        filename=f"mock_{track_number}.mp3",
                        path=Path(f"/tmp/mock_{track_number}.mp3")
                    )

            self._current_track = track
            self._is_playing = True
            self._track_position = 0.0
            self._track_start_time = time.time()

            # Notify playback state change
            self._notify_playback_status('playing')
            logger.log(LogLevel.INFO, f"Mock: Playing track: {track.title}")

            return True

    def pause(self) -> None:
        """Pause playback"""
        with self._state_lock:
            if self._is_playing:
                self._is_playing = False
                # Store the current position for later resume
                self._track_position = time.time() - self._track_start_time

                # Notify pause
                self._notify_playback_status('paused')
                logger.log(LogLevel.INFO, "Mock: Playback paused")

    def resume(self) -> None:
        """Resume playback"""
        with self._state_lock:
            if not self._is_playing and self._current_track:
                self._is_playing = True
                # Adjust start time to account for current position
                self._track_start_time = time.time() - self._track_position

                # Notify resume
                self._notify_playback_status('playing')
                logger.log(LogLevel.INFO, "Mock: Playback resumed")

    def stop(self, clear_playlist: bool = True) -> None:
        """Stop playback"""
        with self._state_lock:
            was_playing = self._is_playing
            self._is_playing = False
            self._current_track = None
            self._track_position = 0.0

            if clear_playlist:
                self._playlist = None

            if was_playing:
                self._notify_playback_status('stopped')
            logger.log(LogLevel.INFO, "Mock: Playback stopped")

    def _check_playback_active(self) -> bool:
        """Check if playback is currently active (mock implementation)."""
        with self._state_lock:
            return self._is_playing

    def _update_progress(self) -> None:
        """Update and send current progress (mock implementation)."""
        with self._state_lock:
            if not self._is_playing or not self._playback_subject or not self._current_track:
                return

            current_time = time.time()
            elapsed = current_time - self._track_start_time

            if elapsed >= self._track_duration:
                self._handle_track_end() # Call the base class _handle_track_end
            else:
                track_info = {
                    'number': self._current_track.number,
                    'title': getattr(self._current_track, 'title', f'Track {self._current_track.number}'),
                    'filename': getattr(self._current_track, 'filename', None),
                    'duration': self._track_duration
                }
                playlist_info = None
                if self._playlist:
                    playlist_info = {
                        'name': getattr(self._playlist, 'name', None),
                        'track_count': len(self._playlist.tracks) if self._playlist.tracks else 0
                    }
                self._playback_subject.notify_track_progress(
                    elapsed=elapsed,
                    total=self._track_duration,
                    track_number=self._current_track.number,
                    track_info=track_info,
                    playlist_info=playlist_info,
                    is_playing=self._is_playing
                )

    def _get_track_duration(self, file_path: Path) -> float:
        """Get track duration in seconds (mock implementation)."""
        return self._track_duration
