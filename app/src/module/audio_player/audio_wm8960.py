import pygame
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import time
import threading
import os
from mutagen.mp3 import MP3
from pydub import AudioSegment
import io

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.helpers.exceptions import AppError
from app.src.services.notification_service import PlaybackSubject
from app.src.module.audio_player.audio_hardware import AudioPlayerHardware
from app.src.model.track import Track
from app.src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class AudioPlayerWM8960(AudioPlayerHardware):
    """
    AudioPlayerWM8960 implements the audio player hardware interface for the WM8960 codec. Playback state is managed and exposed through public properties `is_playing` and `is_paused`.
    """

    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        super().__init__(playback_subject)
        # TODO: remove optional
        self._playback_subject = playback_subject
        # TODO: set to nil at init
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        self._progress_thread = None
        self._stop_progress = False
        self._volume = 100
        self._stream_start_time = 0
        self._audio_cache = {}
        # TODO: improve
        self._paused_position = 0
        self._pause_time = 0

        try:
            # Disable unnecessary components to avoid XDG_RUNTIME_DIR errors
            os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Disable video mode
            os.environ['SDL_AUDIODRIVER'] = 'alsa'   # Force ALSA for Raspberry Pi

            # Initialize only the required pygame subsystems
            pygame.init()  # Minimal initialization
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Explicitly disable the display module
            pygame.display.quit()

            logger.log(LogLevel.INFO, "✓ Audio system initialized with WM8960 (audio-only)")

            # Set up the event handler
            self._setup_event_handler()
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
    def is_playing(self):
        """Check if the player is currently playing audio.

        Returns:
            bool: True if audio is playing, False otherwise.
        """
        return self._is_playing

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
            self._notify_playback_status('loading')

            # Play the file based on its format
            file_path = str(track.path)
            success = False

            try:
                # Load and play the audio file
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                self._stream_start_time = time.time()
                success = True
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error playing file: {str(e)}")
                success = False

            if success:
                self._is_playing = True
                self._notify_playback_status('playing')
                return True
            else:
                self._current_track = None
                self._notify_playback_status('stopped')
                return False

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Play error: {str(e)}")
            self._current_track = None
            self._notify_playback_status('stopped')
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

    def pause(self) -> None:
        """Pause playback and preserve current position"""
        if self._is_playing:
            try:
                # Save the current position before pausing
                current_time = time.time()
                elapsed_since_start = current_time - self._stream_start_time

                # Ensure the position is positive and valid
                if elapsed_since_start < 0:
                    elapsed_since_start = 0

                # Store the exact position for resuming
                self._paused_position = elapsed_since_start
                logger.log(LogLevel.DEBUG, f"Pause: memorized exact position: {self._paused_position:.2f}s")

                # Pause pygame
                pygame.mixer.music.pause()

                # Update state
                self._is_playing = False
                self._pause_time = current_time  # Record when pause was requested

                # Notify the interface
                self._notify_playback_status('paused')
                logger.log(LogLevel.INFO, "Playback paused")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error pausing: {str(e)}")

    def resume(self) -> None:
        """Resume playback with fallback to reloading if unpause fails silently

        This method handles resuming playback after a pause. It includes:
        1. Using the exact position stored during pause
        2. A complete check of the Pygame state
        3. Several fallback mechanisms in case of failure
        """
        # Only attempt to resume if not already playing and a track is defined
        if not self._is_playing and self._current_track:
            # STATE STORAGE - Keep safe references for restoration
            saved_track = self._current_track

            # POSITION DE REPRISE - Utiliser la position exacte mémorisée lors de la pause
            if hasattr(self, '_paused_position') and self._paused_position > 0:
                # Use the exact position stored during pause
                last_pos = self._paused_position
                logger.log(LogLevel.INFO, f"Resuming from stored position: {last_pos:.2f}s")
            else:
                # Fallback to traditional calculation - should not normally be used anymore
                last_pos = 0
                if self._stream_start_time > 0:
                    current_time = time.time()
                    elapsed = current_time - self._stream_start_time
                    if elapsed > 0:
                        # Limit the position to the track duration to avoid overflows
                        track_duration = self._get_track_duration(saved_track.path)
                        last_pos = min(elapsed, track_duration - 1) if track_duration > 0 else elapsed
                        logger.log(LogLevel.INFO, f"Calculated resume position (fallback): {last_pos:.2f}s")

                        # Check if the position is too close to the end
                        if track_duration > 0 and last_pos > track_duration - 5:
                            logger.log(LogLevel.INFO, f"Position too close to end, restarting track")
                            last_pos = 0
                    else:
                        last_pos = 0

            # Initialiser le flag de succès
            success = False

            # ENVIRONMENT CHECK - Ensure Pygame is ready
            # Explicitly disable video components to avoid XDG_RUNTIME_DIR errors
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            os.environ['SDL_AUDIODRIVER'] = 'alsa'

            # Fully reinitialize if necessary
            if not pygame.get_init() or not pygame.mixer.get_init():
                logger.log(LogLevel.WARNING, "Pygame not fully initialized before resume, reinitializing...")
                try:
                    # Clean and complete shutdown
                    pygame.mixer.quit()
                    pygame.quit()
                    time.sleep(0.1)  # Wait for resources to be released

                    # Complete reinitialization
                    pygame.init()
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    pygame.display.quit()  # Disable display module

                    logger.log(LogLevel.INFO, "Pygame successfully reinitialized for audio-only operation")
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"Error during complete Pygame reinitialization: {str(e)}")
                    # Wait a bit longer and try again
                    time.sleep(0.2)
                    try:
                        pygame.init()
                        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    except Exception as e2:
                        logger.log(LogLevel.ERROR, f"Fatal error reinitializing Pygame: {str(e2)}")
                        # Cannot continue if Pygame cannot be initialized
                        return

            # STANDARD RESUME ATTEMPT - first try unpause()
            try:
                # Check that we have a loaded sound before attempting to resume
                if pygame.mixer.music.get_busy() or pygame.mixer.music.get_pos() >= 0:
                    # First attempt: standard resume
                    pygame.mixer.music.unpause()
                    self._is_playing = True

                    # Wait briefly and check if resume worked
                    pygame.time.delay(50)  # 50ms should be enough to detect problems

                    # Force the mixer to process events
                    pygame.event.pump()

                    # Check that playback actually resumed
                    if pygame.mixer.music.get_busy():
                        success = True
                        # Update stream_start_time to account for pause
                        self._stream_start_time = time.time() - last_pos
                        self._notify_playback_status('playing')
                        logger.log(LogLevel.INFO, f"Resume succeeded at position {last_pos:.2f}s")
                    else:
                        logger.log(LogLevel.WARNING, "Standard resume failed silently, falling back to reload")
                        success = False
                else:
                    logger.log(LogLevel.WARNING, "No sound loaded or pending, cannot resume directly")
                    success = False
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error during resume: {str(e)}")
                success = False

            # FALLBACK - If direct resume fails, reload and seek position
            if not success:
                try:
                    # Ensure state variables are intact
                    if not self._current_track:
                        self._current_track = saved_track

                    # Reload from the calculated position
                    if last_pos > 0:
                        logger.log(LogLevel.INFO, f"Forced reload: Resuming at position {last_pos:.2f}s")
                        # Use the dedicated method for loading from a position
                        result = self.play_current_from_position(last_pos)
                        if not result:
                            logger.log(LogLevel.WARNING, "Unable to resume from exact position, restarting track")
                            self.play_track(self._current_track.number)
                    else:
                        # Simply restart the track if we don't have a valid position
                        logger.log(LogLevel.INFO, f"Forced reload: Restarting track {self._current_track.number}")
                        self.play_track(self._current_track.number)
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"Error in resume fallback mechanism: {str(e)}")
                    try:
                        # Last resort - simply try to play from the beginning
                        logger.log(LogLevel.WARNING, "Last resort: attempt to play from beginning")
                        self.play_track(self._current_track.number)
                    except Exception as fallback_error:
                        logger.log(LogLevel.ERROR, f"Complete resume failure: {str(fallback_error)}")
                        self._is_playing = False
                        self._notify_playback_status('stopped')

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
