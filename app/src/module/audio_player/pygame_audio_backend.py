"""
Pygame Audio Backend Implementation

This module implements the AudioBackend interface using pygame for audio playback.
"""

import os
import time
import pygame
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from mutagen.mp3 import MP3

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.audio_player.audio_backend import AudioBackend

logger = ImprovedLogger(__name__)


class PygameAudioBackend(AudioBackend):
    """Implementation of AudioBackend using pygame"""

    # MARK: - Initialization and Setup

    def __init__(self):
        """Initialize the pygame audio backend"""
        self._initialized = False
        self._end_event_callback = None
        self._current_file = None
        self._start_time = 0
        self._paused_position = 0
        self._duration_cache: Dict[str, float] = {}
        self._volume = 50

    def initialize(self) -> bool:
        """Initialize the pygame audio system"""
        try:
            # Set environment variables for audio-only mode
            os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Disable video mode
            os.environ['SDL_AUDIODRIVER'] = 'alsa'   # Force ALSA for Raspberry Pi

            # Initialize only the mixer module instead of all pygame modules
            # This avoids the need for video initialization
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Initialize pygame with only the modules we need
            # Explicitly exclude the display module
            pygame.init()

            # Set up MUSIC_END event handling
            pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
            self._music_end_event = pygame.USEREVENT + 1

            # Start a separate thread to check for events
            self._running = True
            self._event_thread = pygame.time.Clock()

            self._initialized = True

            # Set the default volume (50%)
            try:
                pygame.mixer.music.set_volume(self._volume / 100.0)
                logger.log(LogLevel.INFO, f"Default volume set to {self._volume}%")
            except Exception as e:
                logger.log(LogLevel.WARNING, f"Could not set default volume: {str(e)}")

            logger.log(LogLevel.INFO, "✓ Pygame audio backend initialized (audio-only mode)")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize pygame audio: {str(e)}")
            return False

    # MARK: - Lifecycle Methods

    def shutdown(self) -> bool:
        """Shut down the pygame audio system"""
        try:
            if self._initialized:
                pygame.mixer.quit()
                pygame.quit()
                self._initialized = False
                logger.log(LogLevel.INFO, "Pygame audio backend shut down")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to shut down pygame audio: {str(e)}")
            return False

    # MARK: - File Operations

    def load(self, file_path: Path) -> bool:
        """Load an audio file for playback"""
        try:
            if not self._initialized:
                logger.log(LogLevel.WARNING, "Cannot load file - pygame not initialized")
                return False

            pygame.mixer.music.load(str(file_path))
            self._current_file = file_path
            logger.log(LogLevel.INFO, f"Loaded audio file: {file_path}")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to load audio file: {str(e)}")
            return False

    # MARK: - Playback Control

    def play(self) -> bool:
        """Start playing the loaded audio"""
        try:
            if not self._initialized:
                logger.log(LogLevel.WARNING, "Cannot play - pygame not initialized")
                return False

            # Make sure the mixer is initialized
            if not pygame.mixer.get_init():
                logger.log(LogLevel.WARNING, "Mixer not initialized, reinitializing...")
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Try to play the audio
            try:
                pygame.mixer.music.play()
            except pygame.error as e:
                # If we get a video system error, try to reinitialize pygame
                if "video system not initialized" in str(e):
                    logger.log(LogLevel.WARNING, "Video system error, reinitializing pygame...")
                    # Reinitialize pygame with only the audio system
                    pygame.mixer.quit()
                    pygame.quit()

                    # Set environment variables again
                    os.environ['SDL_VIDEODRIVER'] = 'dummy'
                    os.environ['SDL_AUDIODRIVER'] = 'alsa'

                    # Initialize mixer first, then pygame
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    pygame.init()

                    # Set the volume again
                    pygame.mixer.music.set_volume(self._volume / 100.0)

                    # Try to load and play again
                    if self._current_file:
                        pygame.mixer.music.load(str(self._current_file))
                    pygame.mixer.music.play()
                else:
                    # If it's not a video system error, re-raise it
                    raise

            self._start_time = time.time()
            self._paused_position = 0

            # Clear the pygame event queue to avoid any stale events
            pygame.event.clear()
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to start playback: {str(e)}")
            return False

    def pause(self) -> bool:
        """Pause the currently playing audio"""
        try:
            if not self._initialized or not self.is_playing():
                return False

            # Make sure the mixer is initialized
            if not pygame.mixer.get_init():
                logger.log(LogLevel.WARNING, "Mixer not initialized, reinitializing...")
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Store the current position before pausing
            self._paused_position = self.get_position()

            # Try to pause the audio
            try:
                pygame.mixer.music.pause()
            except pygame.error as e:
                # If we get a video system error, just store the position
                # We'll handle resuming properly in the resume method
                if "video system not initialized" in str(e):
                    logger.log(LogLevel.WARNING, "Video system error during pause, storing position only")
                    # We've already stored the position, so we're good
                else:
                    # If it's not a video system error, re-raise it
                    raise

            logger.log(LogLevel.INFO, f"Paused at position: {self._paused_position:.2f}s")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to pause playback: {str(e)}")
            return False

    def resume(self) -> bool:
        """Resume playback from a paused state"""
        try:
            if not self._initialized:
                return False

            # Make sure the mixer is initialized
            if not pygame.mixer.get_init():
                logger.log(LogLevel.WARNING, "Mixer not initialized, reinitializing...")
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Only attempt to unpause if playback is initialized but paused
            if pygame.mixer.get_init() and not self.is_playing():
                try:
                    pygame.mixer.music.unpause()
                except pygame.error as e:
                    # If we get a video system error, try to reinitialize pygame
                    if "video system not initialized" in str(e):
                        logger.log(LogLevel.WARNING, "Video system error during resume, reinitializing pygame...")
                        # Reinitialize pygame with only the audio system
                        pygame.mixer.quit()
                        pygame.quit()

                        # Set environment variables again
                        os.environ['SDL_VIDEODRIVER'] = 'dummy'
                        os.environ['SDL_AUDIODRIVER'] = 'alsa'

                        # Initialize mixer first, then pygame
                        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                        pygame.init()

                        # Set the volume again
                        pygame.mixer.music.set_volume(self._volume / 100.0)

                        # Try to load and play from the paused position
                        if self._current_file:
                            pygame.mixer.music.load(str(self._current_file))
                            pygame.mixer.music.play(start=self._paused_position)
                            # Update the start time to account for the new position
                            self._start_time = time.time() - self._paused_position
                            logger.log(LogLevel.INFO, f"Resumed from position: {self._paused_position:.2f}s (reloaded)")
                            return True
                    else:
                        # If it's not a video system error, re-raise it
                        raise

                # Adjust start time to account for the pause duration
                pause_duration = time.time() - (self._start_time + self._paused_position)
                self._start_time += pause_duration
                logger.log(LogLevel.INFO, f"Resumed from position: {self._paused_position:.2f}s")
                return True
            return False
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to resume playback: {str(e)}")
            return False

    def stop(self) -> bool:
        """Stop playback and unload the current audio file"""
        try:
            if not self._initialized:
                return False

            # Make sure the mixer is initialized
            if not pygame.mixer.get_init():
                logger.log(LogLevel.WARNING, "Mixer not initialized, reinitializing...")
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Try to stop the audio
            try:
                pygame.mixer.music.stop()
            except pygame.error as e:
                # If we get a video system error, try to reinitialize pygame
                if "video system not initialized" in str(e):
                    logger.log(LogLevel.WARNING, "Video system error during stop, reinitializing pygame...")
                    # Reinitialize pygame with only the audio system
                    pygame.mixer.quit()
                    pygame.quit()

                    # Set environment variables again
                    os.environ['SDL_VIDEODRIVER'] = 'dummy'
                    os.environ['SDL_AUDIODRIVER'] = 'alsa'

                    # Initialize mixer first, then pygame
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    pygame.init()
                else:
                    # If it's not a video system error, re-raise it
                    raise

            self._current_file = None
            self._start_time = 0
            self._paused_position = 0
            logger.log(LogLevel.INFO, "Playback stopped")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to stop playback: {str(e)}")
            return False

    def set_position(self, position_seconds: float) -> bool:
        """Set the playback position"""
        try:
            if not self._initialized or not self._current_file:
                return False

            # Make sure the mixer is initialized
            if not pygame.mixer.get_init():
                logger.log(LogLevel.WARNING, "Mixer not initialized, reinitializing...")
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Convert position from seconds to ratio (0.0 to 1.0)
            duration = self.get_duration(self._current_file)
            if duration <= 0:
                return False

            position_ratio = max(0.0, min(1.0, position_seconds / duration))

            # Try to set the playback position
            try:
                pygame.mixer.music.rewind()
                pygame.mixer.music.set_pos(position_seconds)
            except pygame.error as e:
                # If we get a video system error, try to reinitialize pygame
                if "video system not initialized" in str(e):
                    logger.log(LogLevel.WARNING, "Video system error during position setting, reinitializing pygame...")
                    # Reinitialize pygame with only the audio system
                    pygame.mixer.quit()
                    pygame.quit()

                    # Set environment variables again
                    os.environ['SDL_VIDEODRIVER'] = 'dummy'
                    os.environ['SDL_AUDIODRIVER'] = 'alsa'

                    # Initialize mixer first, then pygame
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    pygame.init()

                    # Set the volume again
                    pygame.mixer.music.set_volume(self._volume / 100.0)

                    # Try to load and set position again
                    if self._current_file:
                        pygame.mixer.music.load(str(self._current_file))
                        pygame.mixer.music.rewind()
                        pygame.mixer.music.set_pos(position_seconds)
                else:
                    # If it's not a video system error, re-raise it
                    raise

            # Update the start time to reflect the new position
            self._start_time = time.time() - position_seconds
            logger.log(LogLevel.INFO, f"Set position to {position_seconds:.2f}s")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to set position: {str(e)}")
            return False

    def get_position(self) -> float:
        """Get the current playback position in seconds"""
        if not self._initialized or not self._current_file:
            return 0.0

        if self.is_playing():
            # Calculate position based on start time
            return time.time() - self._start_time
        else:
            # Return the stored position when paused
            return self._paused_position

    # MARK: - Volume Control

    def set_volume(self, volume: int) -> bool:
        """Set the playback volume"""
        try:
            if not self._initialized:
                return False

            # Make sure the mixer is initialized
            if not pygame.mixer.get_init():
                logger.log(LogLevel.WARNING, "Mixer not initialized, reinitializing...")
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Convert from 0-100 to 0.0-1.0
            volume_float = max(0.0, min(1.0, volume / 100.0))

            # Store the volume in the instance variable
            self._volume = volume

            # Try to set the volume
            try:
                pygame.mixer.music.set_volume(volume_float)
            except pygame.error as e:
                # If we get a video system error, try to reinitialize pygame
                if "video system not initialized" in str(e):
                    logger.log(LogLevel.WARNING, "Video system error during volume setting, reinitializing pygame...")
                    # Reinitialize pygame with only the audio system
                    pygame.mixer.quit()
                    pygame.quit()

                    # Set environment variables again
                    os.environ['SDL_VIDEODRIVER'] = 'dummy'
                    os.environ['SDL_AUDIODRIVER'] = 'alsa'

                    # Initialize mixer first, then pygame
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                    pygame.init()

                    # Try to set volume again
                    pygame.mixer.music.set_volume(volume_float)
                else:
                    # If it's not a video system error, re-raise it
                    raise

            logger.log(LogLevel.INFO, f"Set volume to {volume}%")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to set volume: {str(e)}")
            return False

    def get_volume(self) -> int:
        """Get the current volume"""
        if not self._initialized:
            return 0

        # Make sure the mixer is initialized
        if not pygame.mixer.get_init():
            return 0

        try:
            # Convert from 0.0-1.0 to 0-100
            return int(pygame.mixer.music.get_volume() * 100)
        except pygame.error as e:
            # If we get a video system error, return default volume
            if "video system not initialized" in str(e):
                logger.log(LogLevel.WARNING, "Video system error during get_volume, returning default volume")
                return self._volume if hasattr(self, '_volume') else 100
            # For other errors, return default but log them
            logger.log(LogLevel.ERROR, f"Error getting volume: {str(e)}")
            return 0
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Unexpected error in get_volume: {str(e)}")
            return 0

    # MARK: - Status Methods

    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        if not self._initialized:
            return False

        # Make sure the mixer is initialized
        if not pygame.mixer.get_init():
            return False

        try:
            return bool(pygame.mixer.music.get_busy())
        except pygame.error as e:
            # If we get a video system error, return False
            if "video system not initialized" in str(e):
                logger.log(LogLevel.WARNING, "Video system error during is_playing check")
                return False
            # For other errors, also return False but log them
            logger.log(LogLevel.ERROR, f"Error checking playback status: {str(e)}")
            return False
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Unexpected error in is_playing: {str(e)}")
            return False

    # MARK: - Event Handling and Metadata

    def register_end_event_callback(self, callback: Callable[[], None]) -> bool:
        """Register a callback to be called when playback ends"""
        if not self._initialized:
            return False

        self._end_event_callback = callback
        return True

    def get_duration(self, file_path: Path) -> float:
        """Get the duration of an audio file in seconds"""
        file_path_str = str(file_path)

        # Check if duration is cached
        if file_path_str in self._duration_cache:
            return self._duration_cache[file_path_str]

        try:
            duration = 0.0
            if file_path_str.lower().endswith('.mp3'):
                audio = MP3(file_path_str)
                duration = audio.info.length

            # Cache the duration for future use
            self._duration_cache[file_path_str] = duration
            return duration
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Error getting track duration: {str(e)}")
            return 0.0

    def process_events(self):
        """Process pygame events to detect track end"""
        if not self._initialized:
            return

        for event in pygame.event.get():
            if event.type == self._music_end_event and self._end_event_callback:
                logger.log(LogLevel.INFO, "Detected end of track event")
                self._end_event_callback()
