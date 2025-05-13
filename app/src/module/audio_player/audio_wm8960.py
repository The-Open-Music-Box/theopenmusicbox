import os
import sys
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import mutagen
from mutagen.mp3 import MP3
from pydub import AudioSegment

# Choose appropriate logger based on available imports
try:
    from app.src.common.logging.logger import logger, LogLevel
    from app.src.common.exception import AppError
    from app.src.common.model.playback import PlaybackState, PlaybackSubject
except ImportError:
    from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
    from app.src.helpers.exceptions import AppError
    from app.src.services.notification_service import PlaybackSubject
    # PlaybackState may not exist in the old code
    PlaybackState = None
    logger = ImprovedLogger(__name__)

from .audio_hardware import AudioPlayerHardware
from .audio_backend import AudioBackend
from .pygame_audio_backend import PygameAudioBackend
from app.src.model.track import Track
from app.src.model.playlist import Playlist

class AudioPlayerWM8960(AudioPlayerHardware):
    """
    AudioPlayerWM8960 implements the audio player hardware interface for the WM8960 codec.
    Playback state is managed and exposed through public properties `is_playing` and `is_paused`.

    This implementation uses an audio backend abstraction layer to avoid direct dependency
    on specific audio libraries like pygame.
    """

    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        super().__init__(playback_subject)
        self._playback_subject = playback_subject
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        self._progress_thread = None
        self._stop_progress = False
        self._volume = 100
        self._stream_start_time = 0
        self._audio_cache = {}
        self._paused_position = 0
        self._pause_time = 0

        try:
            # Initialize the audio backend (using pygame under the hood)
            self._audio_backend = PygameAudioBackend()
            if not self._audio_backend.initialize():
                raise AppError.hardware_error(
                    message="Audio backend initialization failed",
                    component="audio",
                    operation="init"
                )

            # Register track end event handler
            self._audio_backend.register_end_event_callback(self._handle_track_end)

            logger.log(LogLevel.INFO, "✓ Audio system initialized with WM8960 (audio-only)")

            # Start the progress tracking thread
            self._start_progress_thread()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize audio system: {str(e)}")
            raise AppError.hardware_error(
                message=f"Audio initialization failed: {str(e)}",
                component="audio",
                operation="init"
            )

    @property
    def is_paused(self) -> bool:
        """
        Return True if the player is paused (not playing, but a track is loaded).
        """
        return not self._is_playing and self._current_track is not None

    @property
    def is_playing(self) -> bool:
        """Check if the player is currently playing audio.

        Returns:
            bool: True if audio is playing, False otherwise.
        """
        # Use both our internal state and the backend's state
        return self._is_playing and self._audio_backend.is_playing()

    def play_track(self, track_number: int) -> bool:
        """Play a specific track from the playlist"""
        try:
            # Stop current playback without clearing playlist
            self.stop(clear_playlist=False)

            if not self._playlist or not self._playlist.tracks:
                logger.log(LogLevel.WARNING, "No playlist or empty playlist")
                return False

            track = next((t for t in self._playlist.tracks if t.number == track_number), None)
            if not track:
                logger.log(LogLevel.WARNING, f"Track number {track_number} not found in playlist")
                return False

            self._current_track = track
            logger.log(LogLevel.INFO, f"Playing track: {track.title or track.filename}")

            # Notify that we're loading the track
            if self._playback_subject:
                self._notify_playback_status("loading")

            try:
                # Use audio backend abstraction instead of direct pygame calls
                if not self._audio_backend.load_audio(str(track.path)):
                    raise Exception("Failed to load audio file")

                self._audio_backend.set_volume(self._volume / 100.0)
                if not self._audio_backend.play():
                    raise Exception("Failed to start playback")

                # Track playback start time for progress calculation
                self._stream_start_time = time.time()
                self._is_playing = True

                # Notify that playback has started
                if self._playback_subject:
                    self._notify_playback_status("playing")

                logger.log(LogLevel.INFO, f"✓ Track started: '{track.title or track.filename}'")
                return True
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Failed to play track: {str(e)}")
                # Reset the current track if we couldn't play it
                self._current_track = None
                return False

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error in play_track: {str(e)}")
            return False

    def _notify_playback_status(self, status: str) -> None:
        """Notify playback status change"""
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
                        'duration': self._get_track_duration(self._current_track.path)
                    }

            self._playback_subject.notify_playback_status(status, playlist_info, track_info)
            logger.log(LogLevel.INFO, f"Playback status update", extra={
                'status': status,
                'playlist': playlist_info,
                'current_track': track_info
            })

    def pause(self) -> bool:
        """Pause playback and preserve current position"""
        if not self._is_playing or not self._current_track:
            logger.log(LogLevel.WARNING, "No active playback to pause")
            return False

        try:
            # Calculate the current position based on elapsed time
            # This is more reliable than using the audio backend's position
            elapsed = 0
            if self._stream_start_time > 0:
                elapsed = time.time() - self._stream_start_time
                if elapsed > 0:  # Sanity check
                    self._paused_position = elapsed
                    logger.log(LogLevel.INFO, f"Paused at position: {self._paused_position:.2f}s")

            # Also store the pause time for time-based calculations
            self._pause_time = time.time()

            # Pause the playback using the audio backend
            if not self._audio_backend.pause():
                logger.log(LogLevel.WARNING, "Audio backend failed to pause playback")
                # Continue anyway, as we've stored the position and might recover

            self._is_playing = False

            # Notify pause status
            if self._playback_subject:
                self._notify_playback_status("paused")

            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error pausing playback: {str(e)}")
            return False

    def resume(self) -> bool:
        """Resume playback with fallback to reloading if unpause fails silently

        This method handles resuming playback after a pause. It includes:
        1. Using the exact position stored during pause
        2. A complete check of the audio backend state
        3. Several fallback mechanisms in case of failure
        """
        if not self.is_paused or not self._current_track:
            logger.log(LogLevel.WARNING, "No paused playback to resume")
            return False

        logger.log(LogLevel.INFO, f"Attempting to resume from position: {self._paused_position:.2f}s")

        try:
            # First, try the simple unpause through the audio backend
            if self._audio_backend.unpause():
                # Wait a tiny bit and check if it's actually playing
                time.sleep(0.1)  # Small delay to let the audio backend update its state

                if self._audio_backend.is_playing():
                    # Direct unpause worked!
                    logger.log(LogLevel.INFO, "Successfully resumed using simple unpause")
                    self._is_playing = True

                    if self._playback_subject:
                        self._notify_playback_status('playing')

                    # Update the stream start time to account for the pause duration
                    pause_duration = time.time() - self._pause_time
                    self._stream_start_time += pause_duration

                    return True

            # If we get here, the unpause didn't work (common issue)
            # Fallback: reload and seek to the paused position
            logger.log(LogLevel.WARNING, "Simple unpause failed, trying reload and seek")
            return self.play_current_from_position(self._paused_position)

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during resume: {str(e)}")
            # Final fallback: reload and seek to saved position
            logger.log(LogLevel.WARNING, "Error during resume, trying reload fallback")
            return self.play_current_from_position(self._paused_position)

    def play_current_from_position(self, position_seconds: float) -> bool:
        """Play the current track from a specific position with robust error handling

        Args:
            position_seconds: Position in seconds to start playback from

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "No current track to resume")
            return False

        # IMPORTANT: Save state references before any reinitialization
        saved_track = self._current_track
        saved_playlist = self._playlist
        current_track_number = saved_track.number

        try:
            # Make sure we have a valid position
            total_duration = self._get_track_duration(saved_track.path)
            if position_seconds < 0:
                position_seconds = 0
            if position_seconds > total_duration:
                position_seconds = 0  # Start from beginning if position is beyond duration

            # Stop any current playback first to clear internal state
            try:
                pygame.mixer.music.stop()
            except Exception as e:
                logger.log(LogLevel.WARNING, f"Error stopping playback: {str(e)}")

            # To avoid video system errors, use only the audio driver
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            os.environ['SDL_AUDIODRIVER'] = 'alsa'

            # Reset pygame completely if needed (helps on Raspberry Pi)
            if not pygame.mixer.get_init() or not pygame.get_init():
                logger.log(LogLevel.WARNING, "Pygame not fully initialized, reinitializing...")
                try:
                    pygame.mixer.quit()
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error quitting mixer: {str(e)}")

                try:
                    pygame.quit()
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error quitting pygame: {str(e)}")

                # Complete reinitialization of pygame in audio-only mode
                try:
                    # Re-initialize base components
                    pygame.init()
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    # Disable the display module to avoid errors
                    pygame.display.quit()
                    logger.log(LogLevel.INFO, "Pygame successfully reinitialized in audio-only mode")
                except Exception as init_error:
                    logger.log(LogLevel.ERROR, f"Failed to reinitialize pygame: {str(init_error)}")
                    # Wait a bit before retrying
                    time.sleep(0.2)
                    pygame.init()
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    pygame.display.quit()

            # IMPORTANT: Ensure the file exists and use the correct path
            file_path = str(saved_track.path)

            # Make sure we haven't lost playlist state
            # If attributes have been reset, restore them
            if not self._current_track or not self._playlist:
                self._current_track = saved_track
                self._playlist = saved_playlist
                logger.log(LogLevel.INFO, "Restored playlist state after reinitialization")

            # Try loading with retry mechanism
            load_attempts = 0
            max_attempts = 3  # Increase number of attempts
            while load_attempts < max_attempts:
                try:
                    pygame.mixer.music.load(file_path)
                    break
                except Exception as load_error:
                    load_attempts += 1
                    if load_attempts >= max_attempts:
                        logger.log(LogLevel.ERROR, f"Final load attempt failed: {load_error}.")
                        if saved_track and saved_track.path and os.path.exists(saved_track.path):
                            logger.log(LogLevel.INFO, f"Track exists at path: {saved_track.path}")
                        else:
                            logger.log(LogLevel.ERROR, f"Track file not found: {saved_track.path}")
                        raise load_error
                    logger.log(LogLevel.WARNING, f"Load attempt {load_attempts} failed: {load_error}. Retrying...")
                    # Brief delay before retry
                    time.sleep(0.1)  # Longer wait to let the system stabilize
                    # Reinitialize pygame if needed between attempts
                    if load_attempts == 2:
                        pygame.mixer.quit()
                        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Start playback with explicit position
            logger.log(LogLevel.INFO, f"Starting playback from position {position_seconds:.2f}s")
            pygame.mixer.music.play(start=position_seconds)

            # Verify playback started properly with additional retries
            pygame.time.delay(100)  # Plus long pour laisser le temps de démarrer

            start_attempts = 0
            max_start_attempts = 2
            while not pygame.mixer.music.get_busy() and start_attempts < max_start_attempts:
                start_attempts += 1
                logger.log(LogLevel.WARNING, f"Start attempt {start_attempts} failed. Retrying...")
                # Retry with different approach
                if start_attempts == 1:
                    # Try standard play with position
                    pygame.mixer.music.play(start=position_seconds)
                else:
                    # Last resort: try from beginning
                    pygame.mixer.music.play()
                pygame.time.delay(100)

            # Update internal state but only if playback actually started
            if pygame.mixer.music.get_busy():
                self._stream_start_time = time.time() - position_seconds  # Adjust start time
                self._is_playing = True

            # Only notify status change if we're actually playing
            if self._is_playing:
                self._notify_playback_status('playing')
                logger.log(LogLevel.INFO, f"Successfully resumed track from position {position_seconds:.2f}s: {self._current_track.title}")
                return True
            else:
                logger.log(LogLevel.ERROR, "Failed to resume playback after multiple attempts")
                return False

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error playing from position: {str(e)}")
            # Last resort attempt: try to completely restart playback from beginning
            try:
                self.play_track(self._current_track.number)
                return self._is_playing
            except:
                return False

    def stop(self, clear_playlist: bool = True) -> None:
        """Stop playback"""
        was_playing = self._is_playing
        try:
            pygame.mixer.music.stop()
            self._is_playing = False
            self._current_track = None
            if clear_playlist:
                self._playlist = None
            if was_playing:
                self._notify_playback_status('stopped')
                logger.log(LogLevel.INFO, "Playback stopped")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during stop: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Stop the progress thread
            if self._progress_thread:
                self._stop_progress = True
                try:
                    self._progress_thread.join(timeout=2.0)
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error stopping progress thread: {str(e)}")

            # Stop playback and quit pygame mixer
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except pygame.error as e:
                logger.log(LogLevel.WARNING, f"Pygame error during cleanup: {str(e)}")

            # Clear audio cache
            try:
                self._audio_cache.clear()
            except AttributeError as e:
                logger.log(LogLevel.WARNING, f"Audio cache attribute missing: {str(e)}")
            except Exception as e:
                logger.log(LogLevel.WARNING, f"Unexpected error clearing audio cache: {str(e)}")

            logger.log(LogLevel.INFO, "All resources cleaned up successfully")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during cleanup: {str(e)}")
        finally:
            self._is_playing = False
            self._current_track = None
            self._playlist = None
            self._progress_thread = None

    def set_playlist(self, playlist: Playlist) -> bool:
        """Set the current playlist and start playback"""
        try:
            self.stop()
            self._playlist = playlist
            if self._playlist and self._playlist.tracks:
                logger.log(LogLevel.INFO, f"Set playlist with {len(self._playlist.tracks)} tracks")
                return self.play_track(1)  # Play first track
            logger.log(LogLevel.WARNING, "Empty playlist or no tracks")
            return False
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting playlist: {str(e)}")
            return False

    def next_track(self) -> None:
        """Play next track"""
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "No current track or playlist")
            return

        next_number = self._current_track.number + 1
        if next_number <= len(self._playlist.tracks):
            logger.log(LogLevel.INFO, f"Moving to next track: {next_number}")
            self.play_track(next_number)
        else:
            logger.log(LogLevel.INFO, "Reached end of playlist")

    def previous_track(self) -> None:
        """Play previous track"""
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "No current track or playlist")
            return

        prev_number = self._current_track.number - 1
        if prev_number > 0:
            logger.log(LogLevel.INFO, f"Moving to previous track: {prev_number}")
            self.play_track(prev_number)
        else:
            logger.log(LogLevel.INFO, "Already at first track")

    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)"""
        try:
            self._volume = max(0, min(100, volume))
            # Convert 0-100 range to 0.0-1.0 for pygame
            pygame_volume = self._volume / 100.0
            pygame.mixer.music.set_volume(pygame_volume)
            logger.log(LogLevel.INFO, f"Volume set to {self._volume}%")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting volume: {str(e)}")
            return False

    def _get_current_track(self):
        """(Private) Return the currently playing track (not part of Protocol)"""
        return self._current_track

    def _get_playlist(self):
        """(Private) Return the current playlist (not part of Protocol)"""
        return self._playlist

    def _get_volume(self):
        """(Private) Return current volume (not part of Protocol)"""
        return self._volume

    def _setup_event_handler(self):
        """Set up event handler"""
        self._start_progress_thread()

    def _start_progress_thread(self):
        """Start progress tracking thread"""
        if self._progress_thread:
            self._stop_progress = True
            self._progress_thread.join(timeout=1.0)

        self._stop_progress = False
        self._progress_thread = threading.Thread(target=self._progress_loop)
        self._progress_thread.daemon = True
        self._progress_thread.start()

    def _progress_loop(self):
        """Progress tracking loop"""
        last_playing_state = False
        last_update_time = 0
        tick = 0
        while not self._stop_progress:
            tick += 1
            if self._is_playing and self._playback_subject and self._current_track:
                current_time = time.time()
                if current_time - last_update_time >= 1.0:
                    last_update_time = current_time
                    self._update_progress()

                # Check if music has stopped playing (track ended)
                current_playing_state = pygame.mixer.music.get_busy()
                if last_playing_state and not current_playing_state:
                    logger.log(LogLevel.INFO, f"[PROGRESS_LOOP] Detected track end at tick={tick}")
                    self._handle_track_end()
                last_playing_state = current_playing_state
            time.sleep(0.1)  # Update more frequently to catch track end

    def _update_progress(self):
        """Update and send current progress"""
        if not self._current_track or not self._playback_subject:
            logger.log(LogLevel.WARNING, "[UPDATE_PROGRESS] No current_track or playback_subject; skipping progress update.")
            return

        try:
            # Check if playback is active via pygame
            busy = pygame.mixer.music.get_busy()

            # If internal state indicates 'playing' but pygame says it's stopped, this is an error
            if self._is_playing and not busy and pygame.mixer.get_init():
                logger.log(LogLevel.WARNING, "[UPDATE_PROGRESS] Audio state mismatch: _is_playing=True but pygame says it's not busy")
                # Do not send update in this case to avoid conflicting timecodes
                return

            # Calculate time elapsed since playback started
            elapsed = time.time() - self._stream_start_time if self._stream_start_time > 0 else 0
            total = self._get_track_duration(self._current_track.path)

            # Avoid negative values or values greater than total duration
            if elapsed < 0:
                elapsed = 0
            if total > 0 and elapsed > total:
                elapsed = total

            track_info = {
                'number': self._current_track.number,
                'title': getattr(self._current_track, 'title', f'Track {self._current_track.number}'),
                'filename': getattr(self._current_track, 'filename', None),
                'duration': total
            }
            playlist_info = self._playlist.to_dict() if self._playlist and hasattr(self._playlist, 'to_dict') else None

            # Only send the update if we are in playback mode
            # to avoid conflicting timecodes
            if self._is_playing:
                self._playback_subject.notify_track_progress(
                    elapsed=elapsed,
                    total=total,
                    track_number=track_info.get('number'),
                    track_info=track_info,
                    playlist_info=playlist_info,
                    is_playing=self._is_playing
                )

                # Do not log every update to avoid log overload
                # Log only every 10 seconds or at key moments
                if int(elapsed) % 10 == 0 or int(elapsed) == 0 or int(elapsed) == int(total):
                    logger.log(LogLevel.INFO, f"[UPDATE_PROGRESS] notify_track_progress called (elapsed={elapsed:.2f} / {total:.2f})")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error updating progress: {str(e)}")

    def _get_track_duration(self, file_path: Path) -> float:
        """Get track duration in seconds"""
        try:
            if str(file_path).lower().endswith('.mp3'):
                audio = MP3(str(file_path))
                return audio.info.length
            return 0
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Error getting track duration: {str(e)}")
            return 0

    def _handle_track_end(self):
        """Handle end of track"""
        if self._is_playing and self._current_track and self._playlist:
            next_number = self._current_track.number + 1
            if next_number <= len(self._playlist.tracks):
                logger.log(LogLevel.INFO, f"Track ended, playing next: {next_number}")
                self.play_track(next_number)
            else:
                logger.log(LogLevel.INFO, "Playlist ended")
                self.stop()
