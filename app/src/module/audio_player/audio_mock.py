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
from typing import Optional
import threading
import time
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.audio_player.audio_hardware import AudioPlayerHardware
from app.src.services.notification_service import PlaybackSubject
from app.src.model.track import Track
from app.src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class MockAudioPlayer(AudioPlayerHardware):
    """
    MockAudioPlayer simulates audio playback for testing purposes. Playback state is exposed through public properties `is_playing` and `is_paused` for consistency with hardware implementations.
    """
    @property
    def is_paused(self) -> bool:
        """
        Return True if the player is paused (not playing, but a track is loaded).
        """
        return not self._is_playing and self._current_track is not None
        
    @property
    def is_playing(self) -> bool:
        """
        Check if the player is currently playing audio.
        
        Returns:
            bool: True if audio is playing, False otherwise.
        """
        return self._is_playing

    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        """
        Initialize the mock audio player.
        Args:
            playback_subject: Optional observer for playback events (used for real-time status updates)
        """
        super().__init__(playback_subject)
        self._playback_subject = playback_subject  # Always set for compatibility with AudioPlayer interface
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        self._volume = 50
        self._progress_thread = None
        self._stop_progress = False
        self._track_duration = 180.0  # Simulated track duration in seconds
        self._track_position = 0.0
        self._track_start_time = 0.0
        logger.log(LogLevel.INFO, "Mock Audio Player initialized")

        # Start the progress tracking thread if a playback_subject is provided (for real-time frontend updates)
        if playback_subject:
            self._start_progress_thread()

    def play(self, track: str) -> None:
        """
        Play a specific track by filename or path.
        Args:
            track: The filename or path of the audio track to play.
        """
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

    def _load_playlist(self, playlist_path: str) -> bool:
        """(Private) Load a playlist from a path (not part of Protocol)"""
        logger.log(LogLevel.INFO, f"Mock: Loading playlist from {playlist_path}")
        self._playlist = Playlist(name=Path(playlist_path).stem, tracks=[])
        return True

    def set_playlist(self, playlist: Playlist) -> bool:
        """Set the current playlist and start playback"""
        try:
            self.stop()
            self._playlist = playlist

            if self._playlist and self._playlist.tracks:
                logger.log(LogLevel.INFO, f"Mock: Set playlist with {len(self._playlist.tracks)} tracks")
                # Play the first track in the playlist
                return self.play_track(1)

            logger.log(LogLevel.WARNING, "Mock: Empty playlist or no tracks")
            return False

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Mock: Error setting playlist: {str(e)}")
            return False

    def play_track(self, track_number: int) -> bool:
        """Play a specific track from the playlist"""
        # Stop current playback without clearing the playlist
        self.stop(clear_playlist=False)

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
        if self._is_playing:
            self._is_playing = False
            # Store the current position for later resume
            self._track_position = time.time() - self._track_start_time

            # Notify pause
            self._notify_playback_status('paused')
            logger.log(LogLevel.INFO, "Mock: Playback paused")

    def resume(self) -> None:
        """Resume playback"""
        if not self._is_playing and self._current_track:
            self._is_playing = True
            # Adjust start time to account for current position
            self._track_start_time = time.time() - self._track_position

            # Notify resume
            self._notify_playback_status('playing')
            logger.log(LogLevel.INFO, "Mock: Playback resumed")

    def stop(self, clear_playlist: bool = True) -> None:
        """Stop playback"""
        was_playing = self._is_playing
        self._is_playing = False
        self._current_track = None
        self._track_position = 0.0

        if clear_playlist:
            self._playlist = None

        if was_playing:
            self._notify_playback_status('stopped')
            logger.log(LogLevel.INFO, "Mock: Playback stopped")

    def next_track(self) -> None:
        """Go to the next track"""
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "Mock: No current track or playlist")
            return

        next_number = self._current_track.number + 1
        if next_number <= len(self._playlist.tracks):
            logger.log(LogLevel.INFO, f"Mock: Moving to next track: {next_number}")
            self.play_track(next_number)
        else:
            logger.log(LogLevel.INFO, "Mock: Reached end of playlist")
            # Simulate the end of the playlist
            self.stop()

    def previous_track(self) -> None:
        """Go to the previous track"""
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "Mock: No current track or playlist")
            return

        prev_number = self._current_track.number - 1
        if prev_number > 0:
            logger.log(LogLevel.INFO, f"Mock: Moving to previous track: {prev_number}")
            self.play_track(prev_number)
        else:
            logger.log(LogLevel.INFO, "Mock: Already at first track")

    def set_volume(self, volume: int) -> bool:
        """Set the volume (0-100)"""
        try:
            self._volume = max(0, min(100, volume))
            logger.log(LogLevel.INFO, f"Mock: Volume set to {self._volume}%")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Mock: Error setting volume: {str(e)}")
            return False

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Stop the progress thread
            if self._progress_thread:
                self._stop_progress = True
                try:
                    self._progress_thread.join(timeout=2.0)
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Mock: Error stopping progress thread: {str(e)}")

            # Stop playback
            self.stop()
            logger.log(LogLevel.INFO, "Mock: Resources cleaned up")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Mock: Error during cleanup: {str(e)}")
        finally:
            self._is_playing = False
            self._current_track = None
            self._playlist = None
            self._progress_thread = None

    def _notify_playback_status(self, status: str) -> None:
        """Notify playback state change"""
        if self._playback_subject:
            playlist_info = None
            track_info = None

            if status != 'stopped':
                if self._playlist:
                    playlist_info = {
                        'name': self._playlist.name,
                        'track_count': len(self._playlist.tracks) if self._playlist.tracks else 0
                    }

                if self._current_track:
                    track_info = {
                        'number': self._current_track.number,
                        'title': self._current_track.title or f'Track {self._current_track.number}',
                        'filename': self._current_track.filename,
                        'duration': self._track_duration
                    }

            self._playback_subject.notify_playback_status(status, playlist_info, track_info)
            logger.log(LogLevel.INFO, "Mock: Playback status update", extra={
                'status': status,
                'playlist': playlist_info,
                'current_track': track_info
            })

    def _start_progress_thread(self) -> None:
        """Start the progress tracking thread"""
        if self._progress_thread:
            self._stop_progress = True
            self._progress_thread.join(timeout=1.0)

        self._stop_progress = False
        self._progress_thread = threading.Thread(target=self._progress_loop)
        self._progress_thread.daemon = True
        self._progress_thread.start()

    def _progress_loop(self) -> None:
        """Progress tracking loop"""
        last_update_time = 0

        while not self._stop_progress:
            if self._is_playing and self._playback_subject and self._current_track:
                current_time = time.time()

                # Update progress every 500ms
                if current_time - last_update_time >= 0.5:
                    last_update_time = current_time

                    # Calculate the current position
                    elapsed = current_time - self._track_start_time

                    # If the end of the track is reached, go to the next
                    if elapsed >= self._track_duration:
                        # Simulate the end of the track
                        self._handle_track_end()
                    else:
                        # Prepare track and playlist info for progress notification
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

            # Sleep to avoid CPU overload
            time.sleep(0.1)

    def _handle_track_end(self) -> None:
        """Handle the end of a track"""
        if self._is_playing and self._current_track and self._playlist:
            next_number = self._current_track.number + 1
            if next_number <= len(self._playlist.tracks):
                logger.log(LogLevel.INFO, f"Mock: Track ended, playing next: {next_number}")
                self.play_track(next_number)
            else:
                logger.log(LogLevel.INFO, "Mock: Playlist ended")
                self.stop()
