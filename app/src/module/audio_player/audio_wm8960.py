import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from mutagen.mp3 import MP3

from app.src.helpers.exceptions import AppError
from app.src.model.track import Track
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.notification_service import PlaybackSubject

from .audio_hardware import AudioPlayerHardware
from .base_audio_player import BaseAudioPlayer
from .pygame_audio_backend import PygameAudioBackend

logger = ImprovedLogger(__name__)


class AudioPlayerWM8960(BaseAudioPlayer, AudioPlayerHardware):
    """AudioPlayerWM8960 implements the audio player hardware interface for the
    WM8960 codec. Playback state is managed and exposed through public
    properties `is_playing` and `is_paused`.

    This implementation uses an audio backend abstraction layer to avoid
    direct dependency on specific audio libraries like pygame.
    """

    # MARK: - Initialization and Setup

    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        super().__init__(playback_subject)
        self._audio_cache = {}
        self._alsa_process = None

        try:
            self._audio_backend = PygameAudioBackend()
            if not self._audio_backend.initialize():
                raise AppError.hardware_error(
                    message="Audio backend initialization failed",
                    component="audio",
                    operation="init",
                )

            self.set_volume(self._volume)

            # Register track end event handler
            self._audio_backend.register_end_event_callback(self._handle_track_end)

            logger.log(
                LogLevel.INFO, "✓ Audio system initialized with WM8960 (audio-only)"
            )

            # Start the progress tracking thread
            self._start_progress_thread()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize audio system: {str(e)}")
            raise AppError.hardware_error(
                message=f"Audio initialization failed: {str(e)}",
                component="audio",
                operation="init",
            )

    # MARK: - Playback Control

    def play_track(self, track_number: int) -> bool:
        """Play a specific track from the playlist."""
        with self._state_lock:
            try:
                # Stop current playback without clearing playlist
                self.stop(clear_playlist=False)

                if not self._playlist or not self._playlist.tracks:
                    logger.log(LogLevel.WARNING, "No playlist or empty playlist")
                    return False

                track = next(
                    (t for t in self._playlist.tracks if t.number == track_number), None
                )
                if not track:
                    logger.log(
                        LogLevel.WARNING,
                        f"Track number {track_number} not found in playlist",
                    )
                    return False

                self._current_track = track
                logger.log(
                    LogLevel.INFO, f"Playing track: {track.title or track.filename}"
                )

                # Notify that we're loading the track
                self._notify_playback_status("loading")

                # This inner try-except block handles the audio loading and playback
                try:
                    # Use audio backend abstraction instead of direct pygame calls
                    if not self._audio_backend.load(str(track.path)):
                        logger.log(
                            LogLevel.ERROR, f"Failed to load audio file: {track.path}"
                        )
                        # Attempt ALSA fallback if loading fails
                        return self._fallback_to_alsa(str(track.path))

                    logger.log(
                        LogLevel.INFO,
                        f"AudioPlayerWM8960: Setting backend volume to {self._volume} (0-100 scale)",
                    )
                    if not self._audio_backend.set_volume(self._volume):
                        logger.log(
                            LogLevel.WARNING, "Failed to set volume via audio backend."
                        )

                    if not self._audio_backend.play():
                        logger.log(
                            LogLevel.ERROR, "Audio backend failed to start playback."
                        )
                        # Attempt ALSA fallback if play fails
                        return self._fallback_to_alsa(str(track.path))

                    # Track playback start time for progress calculation
                    self._stream_start_time = time.time()
                    self._is_playing = True

                    # Notify that playback has started
                    self._notify_playback_status("playing")

                    logger.log(
                        LogLevel.INFO,
                        f"✓ Track started: '{track.title or track.filename}' via Pygame backend",
                    )
                    return True
                except Exception as e:  # Catches errors from load, set_volume, play
                    logger.log(
                        LogLevel.ERROR,
                        f"Error during Pygame backend playback attempt for track {track.title or track.filename}: {str(e)}",
                    )
                    logger.log(
                        LogLevel.INFO,
                        f"Attempting ALSA fallback for track: {track.title or track.filename}",
                    )
                    return self._fallback_to_alsa(str(track.path))  # Fallback to ALSA
            # Catches errors from outer logic (playlist handling, etc.)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Outer error in play_track: {str(e)}")
                return False

    def pause(self) -> bool:
        """Pause playback and preserve current position."""
        with self._state_lock:
            if not self._is_playing or not self._current_track:
                logger.log(LogLevel.WARNING, "No active playback to pause")
                return False

            try:
                # Calculate the current position based on elapsed time
                elapsed = 0
                if self._stream_start_time > 0:
                    elapsed = time.time() - self._stream_start_time
                    if elapsed > 0:  # Sanity check
                        self._paused_position = elapsed
                        logger.log(
                            LogLevel.INFO,
                            f"Paused at position: {self._paused_position:.2f}s",
                        )

                # Also store the pause time for time-based calculations
                self._pause_time = time.time()

                # Pause the playback using the audio backend
                if not self._audio_backend.pause():
                    logger.log(
                        LogLevel.WARNING, "Audio backend failed to pause playback"
                    )

                self._is_playing = False

                # Notify pause status
                self._notify_playback_status("paused")

                return True
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error pausing playback: {str(e)}")
                return False

    def resume(self) -> bool:
        """Resume playback with fallback to reloading if unpause fails
        silently."""
        with self._state_lock:
            if not self.is_paused or not self._current_track:
                logger.log(LogLevel.WARNING, "No paused playback to resume")
                return False

            logger.log(
                LogLevel.INFO,
                f"Attempting to resume from position: {self._paused_position:.2f}s",
            )

            try:
                # First, try the simple resume through the audio backend
                if self._audio_backend.resume():  # Changed from unpause()
                    # Wait a tiny bit and check if it's actually playing
                    # Small delay to let the audio backend update its state
                    time.sleep(0.1)

                    if self._audio_backend.is_playing():
                        # Direct unpause worked!
                        logger.log(
                            LogLevel.INFO, "Successfully resumed using simple unpause"
                        )
                        self._is_playing = True
                        self._notify_playback_status("playing")

                        # Update the stream start time to account for the pause duration
                        pause_duration = time.time() - self._pause_time
                        self._stream_start_time += pause_duration
                        return True

                # If we get here, the unpause didn't work
                # Fallback: reload and seek to the paused position
                logger.log(
                    LogLevel.WARNING, "Simple unpause failed, trying reload and seek"
                )
                return self.play_current_from_position(self._paused_position)

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error during resume: {str(e)}")
                # Final fallback: reload and seek to saved position
                logger.log(
                    LogLevel.WARNING, "Error during resume, trying reload fallback"
                )
                return self.play_current_from_position(self._paused_position)

    def _validate_position(self, position_seconds: float, track_path: Path) -> float:
        """Validate and adjust the position if needed."""
        total_duration = self._get_track_duration(track_path)
        if position_seconds < 0:
            return 0
        if position_seconds > total_duration:
            return 0  # Start from beginning if position is beyond duration
        return position_seconds

    def _prepare_audio_backend(self) -> bool:
        """Prepare the audio backend for playback."""
        try:
            self._audio_backend.stop()
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Error stopping playback: {str(e)}")

        # Set environment variables
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "alsa"

        # Reinitialize if needed
        if not self._audio_backend.is_playing():
            return self._reinitialize_audio_backend()
        return True

    def _reinitialize_audio_backend(self) -> bool:
        """Reinitialize the audio backend if needed."""
        try:
            self._audio_backend.shutdown()
            if not self._audio_backend.initialize():
                logger.log(LogLevel.ERROR, "Failed to reinitialize audio backend")
                time.sleep(0.2)
                return self._audio_backend.initialize()
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error reinitializing audio backend: {str(e)}")
            return False

    def _load_and_play_from_position(
        self, track: Track, position_seconds: float
    ) -> bool:
        """Load and play a track from a specific position."""
        try:
            load_attempts = 0
            max_attempts = 3
            while load_attempts < max_attempts:
                try:
                    if self._audio_backend.load(str(track.path)):
                        break
                    else:
                        raise Exception("Audio backend failed to load file")
                except Exception as load_error:
                    load_attempts += 1
                    if load_attempts >= max_attempts:
                        logger.log(
                            LogLevel.ERROR, f"Final load attempt failed: {load_error}."
                        )
                        if track and track.path and os.path.exists(track.path):
                            logger.log(
                                LogLevel.INFO, f"Track exists at path: {track.path}"
                            )
                        else:
                            logger.log(
                                LogLevel.ERROR, f"Track file not found: {track.path}"
                            )
                        raise load_error
                    logger.log(
                        LogLevel.WARNING,
                        f"Load attempt {load_attempts} failed: {load_error}. Retrying...",
                    )
                    time.sleep(0.1)
                    if load_attempts == 2:
                        self._audio_backend.shutdown()
                        self._audio_backend.initialize()

            # Set the position and start playback
            logger.log(
                LogLevel.INFO,
                f"Starting playback from position {position_seconds:.2f}s",
            )
            self._audio_backend.set_position(position_seconds)
            self._audio_backend.set_volume(self._volume)

            if not self._audio_backend.play():
                logger.log(
                    LogLevel.ERROR, "Failed to start playback after setting position"
                )
                return False

            time.sleep(0.1)  # Wait for playback to start

            # Verify playback started
            start_attempts = 0
            max_start_attempts = 2
            while (
                not self._audio_backend.is_playing()
                and start_attempts < max_start_attempts
            ):
                start_attempts += 1
                logger.log(
                    LogLevel.WARNING,
                    f"Start attempt {start_attempts} failed. Retrying...",
                )
                if start_attempts == 1:
                    self._audio_backend.set_position(position_seconds)
                    self._audio_backend.play()
                else:
                    self._audio_backend.play()  # Last resort: try from beginning
                time.sleep(0.1)

            if self._audio_backend.is_playing():
                self._stream_start_time = time.time() - position_seconds
                self._is_playing = True
                self._notify_playback_status("playing")
                logger.log(
                    LogLevel.INFO,
                    f"Successfully resumed track from position {position_seconds:.2f}s: {track.title}",
                )
                return True
            else:
                logger.log(
                    LogLevel.ERROR, "Failed to resume playback after multiple attempts"
                )
                return False
        except Exception as e:
            logger.log(
                LogLevel.ERROR, f"Error in _load_and_play_from_position: {str(e)}"
            )
            return False

    def _fallback_to_alsa(self, track_path: str) -> bool:
        """Fallback to direct ALSA playback if Pygame fails."""
        try:
            logger.log(LogLevel.WARNING, f"Attempting ALSA fallback for {track_path}")

            # Use aplay for WAV files or mpg123 for MP3 files
            if track_path.lower().endswith(".mp3"):
                cmd = ["mpg123", "-a", "default", track_path]
            else:
                cmd = ["aplay", track_path]

            # Kill any existing processes
            try:
                if hasattr(self, "_alsa_process") and self._alsa_process:
                    self._alsa_process.terminate()
                    self._alsa_process.wait(timeout=1)
            except Exception as e:
                logger.log(
                    LogLevel.WARNING,
                    f"Error terminating previous ALSA process: {str(e)}",
                )

            # Start new process
            self._alsa_process = subprocess.Popen(cmd)
            logger.log(
                LogLevel.INFO,
                f"Started ALSA fallback process with command: {' '.join(cmd)}",
            )

            # Set state
            self._is_playing = True
            self._stream_start_time = time.time()

            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"ALSA fallback failed: {str(e)}")
            return False

    def _attempt_fallback_playback(self) -> bool:
        """Attempt to restart playback from the beginning as a last resort."""
        try:
            if self._current_track:
                # First try normal playback
                if self.play_track(self._current_track.number):
                    return True

                # If that fails, try ALSA fallback
                logger.log(
                    LogLevel.WARNING, "Normal playback failed, trying ALSA fallback"
                )
                return self._fallback_to_alsa(str(self._current_track.path))
            return False
        except Exception as e:
            logger.log(LogLevel.ERROR, f"All fallback attempts failed: {str(e)}")
            return False

    def play_current_from_position(self, position_seconds: float) -> bool:
        """Play the current track from a specific position with robust error
        handling."""
        with self._state_lock:
            if not self._current_track or not self._playlist:
                logger.log(LogLevel.WARNING, "No current track to resume")
                return False

            saved_track = self._current_track

            try:
                position_seconds = self._validate_position(
                    position_seconds, saved_track.path
                )
                if not self._prepare_audio_backend():
                    return False
                return self._load_and_play_from_position(saved_track, position_seconds)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error playing from position: {str(e)}")
                return self._attempt_fallback_playback()

    def stop(self, clear_playlist: bool = True) -> None:
        """Stop playback."""
        with self._state_lock:
            was_playing = self._is_playing
            try:
                self._audio_backend.stop()
                self._is_playing = False
                self._current_track = None
                if clear_playlist:
                    self._playlist = None
                if was_playing:
                    self._notify_playback_status("stopped")
                logger.log(LogLevel.INFO, "Playback stopped")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error during stop: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources."""
        super().cleanup()  # Call BaseAudioPlayer's cleanup
        with self._state_lock:
            try:
                self._audio_backend.shutdown()
            except Exception as e:
                logger.log(
                    LogLevel.WARNING, f"Audio backend error during cleanup: {str(e)}"
                )

            try:
                self._audio_cache.clear()
            except AttributeError as e:
                logger.log(LogLevel.WARNING, f"Audio cache attribute missing: {str(e)}")
            except Exception as e:
                logger.log(
                    LogLevel.WARNING, f"Unexpected error clearing audio cache: {str(e)}"
                )

            logger.log(LogLevel.INFO, "WM8960 resources cleaned up successfully")

    # MARK: - Playlist Management (Most methods are inherited from BaseAudioPlayer)

    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)"""
        with self._state_lock:
            # First update the internal volume value via the parent class
            super().set_volume(volume)  # This always returns True and sets self._volume

            # Now try to set the volume in the audio backend
            backend_success = self._audio_backend.set_volume(self._volume)
            if not backend_success:
                logger.log(LogLevel.WARNING, "Audio backend failed to set volume")
                return False  # Return False if backend failed

            logger.log(LogLevel.INFO, f"Volume set to {self._volume}%")
            return True  # Return True only if both operations succeeded

    # MARK: - Internal Helpers (Most methods are inherited or removed)

    def _check_playback_active(self) -> bool:
        """Check if playback is currently active using the audio backend."""
        with self._state_lock:
            return self._audio_backend.is_playing()

    def _update_progress(self):
        """Update and send current progress."""
        with self._state_lock:
            if not self._current_track or not self._playback_subject:
                logger.log(
                    LogLevel.WARNING,
                    "[UPDATE_PROGRESS] No current_track or playback_subject; skipping progress update.",
                )
                return

            try:
                # Check if playback is active via audio backend
                busy = self._audio_backend.is_playing()

                # If internal state indicates 'playing' but backend says it's stopped,
                # this is an error
                if self._is_playing and not busy:
                    logger.log(
                        LogLevel.WARNING,
                        "[UPDATE_PROGRESS] Audio state mismatch: _is_playing=True but audio backend says it's not playing",
                    )
                    # Do not send update in this case to avoid conflicting timecodes
                    return

                # Calculate time elapsed since playback started
                elapsed = (
                    time.time() - self._stream_start_time
                    if self._stream_start_time > 0
                    else 0
                )
                total = self._get_track_duration(self._current_track.path)

                # Avoid negative values or values greater than total duration
                if elapsed < 0:
                    elapsed = 0
                if total > 0 and elapsed > total:
                    elapsed = total

                track_info = {
                    "number": self._current_track.number,
                    "title": getattr(
                        self._current_track,
                        "title",
                        f"Track {self._current_track.number}",
                    ),
                    "filename": getattr(self._current_track, "filename", None),
                    "duration": total,
                }
                playlist_info = (
                    self._playlist.to_dict()
                    if self._playlist and hasattr(self._playlist, "to_dict")
                    else None
                )

                # Only send the update if we are in playback mode
                # to avoid conflicting timecodes
                if self._is_playing:
                    self._playback_subject.notify_track_progress(
                        elapsed=elapsed,
                        total=total,
                        track_number=track_info.get("number"),
                        track_info=track_info,
                        playlist_info=playlist_info,
                        is_playing=self._is_playing,
                    )

                    # Do not log every update to avoid log overload
                    # Log only every 10 seconds or at key moments
                    if (
                        int(elapsed) % 10 == 0
                        or int(elapsed) == 0
                        or int(elapsed) == int(total)
                    ):
                        logger.log(
                            LogLevel.INFO,
                            f"[UPDATE_PROGRESS] notify_track_progress called (elapsed={elapsed:.2f} / {total:.2f})",
                        )

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error updating progress: {str(e)}")

    def _get_track_duration(self, file_path: Path) -> float:
        """Get track duration in seconds."""
        with self._state_lock:
            try:
                if str(file_path) in self._audio_cache:
                    return self._audio_cache[str(file_path)]

                if str(file_path).lower().endswith(".mp3"):
                    audio = MP3(str(file_path))
                    duration = audio.info.length
                    self._audio_cache[str(file_path)] = duration
                    return duration
                return 0
            except Exception as e:
                logger.log(LogLevel.WARNING, f"Error getting track duration: {str(e)}")
                return 0
