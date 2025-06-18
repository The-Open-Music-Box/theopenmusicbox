import os
import time

import pygame

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

# MARK: - Audio Engine Class


class AudioEngine:
    """Handles low-level Pygame audio initialization and playback."""

    # MARK: - Initialization
    def __init__(self):
        self._initialized = False
        self.initialize()

    def initialize(self) -> bool:
        """Initialize Pygame for audio playback."""
        try:
            # Disable unnecessary components to avoid XDG_RUNTIME_DIR errors
            os.environ["SDL_VIDEODRIVER"] = "dummy"  # Disable video mode
            os.environ["SDL_AUDIODRIVER"] = "alsa"  # Force ALSA for Raspberry Pi

            # Initialize only the required pygame subsystems
            pygame.init()  # Minimal initialization
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

            # Explicitly disable the display module
            pygame.display.quit()

            self._initialized = True
            logger.log(LogLevel.INFO, "✓ Audio engine initialized successfully")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize audio engine: {str(e)}")
            self._initialized = False
            return False

    # MARK: - State Management
    def reinitialize(self) -> bool:
        """Reinitialize Pygame if needed."""
        if self._initialized and pygame.get_init() and pygame.mixer.get_init():
            return True

        try:
            # Clean shutdown if components are partially initialized
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            if pygame.get_init():
                pygame.quit()

            time.sleep(0.1)  # Wait for resources to be released
            return self.initialize()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to reinitialize audio engine: {str(e)}")
            return False

    def ensure_initialized(self) -> bool:
        """Ensure Pygame is properly initialized, reinitializing if needed."""
        if (
            not self._initialized
            or not pygame.get_init()
            or not pygame.mixer.get_init()
        ):
            return self.reinitialize()
        return True

    # MARK: - Audio File Management
    def load_file(self, file_path: str, max_attempts: int = 3) -> bool:
        """Load an audio file with retry mechanism."""
        if not self.ensure_initialized():
            return False

        attempts = 0
        while attempts < max_attempts:
            try:
                pygame.mixer.music.load(file_path)
                return True
            except Exception as e:
                attempts += 1
                logger.log(
                    LogLevel.WARNING,
                    f"Load attempt {attempts} failed: {e}. Retrying...",
                )
                time.sleep(0.1)

                # Reinitialize mixer on the second attempt
                if attempts == 2:
                    pygame.mixer.quit()
                    pygame.mixer.init(
                        frequency=44100, size=-16, channels=2, buffer=1024
                    )

        logger.log(LogLevel.ERROR, "All load attempts failed")
        return False

    # MARK: - Playback Control
    def play(self, start_position: float = 0.0) -> bool:
        """Play currently loaded audio from the specified position."""
        if not self.ensure_initialized():
            return False

        try:
            pygame.mixer.music.play(start=start_position)

            # Verify playback started correctly
            pygame.time.delay(100)
            return pygame.mixer.music.get_busy()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error starting playback: {str(e)}")
            return False

    def pause(self) -> bool:
        """Pause current playback."""
        if not self.ensure_initialized() or not pygame.mixer.music.get_busy():
            return False

        try:
            pygame.mixer.music.pause()
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error pausing playback: {str(e)}")
            return False

    def unpause(self) -> bool:
        """Unpause current playback."""
        if not self.ensure_initialized():
            return False

        try:
            pygame.mixer.music.unpause()
            pygame.time.delay(50)
            pygame.event.pump()
            return pygame.mixer.music.get_busy()
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error resuming playback: {str(e)}")
            return False

    def stop(self) -> bool:
        """Stop current playback."""
        if not self.ensure_initialized():
            return False

        try:
            pygame.mixer.music.stop()
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error stopping playback: {str(e)}")
            return False

    # MARK: - Volume Control
    def set_volume(self, volume: int) -> bool:
        """Set playback volume (0-100)."""
        if not self.ensure_initialized():
            return False

        try:
            # Pygame volume is 0.0 to 1.0
            normalized_volume = max(0, min(100, volume)) / 100.0
            pygame.mixer.music.set_volume(normalized_volume)
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting volume: {str(e)}")
            return False

    # MARK: - State Query
    def get_busy(self) -> bool:
        """Check if playback is active."""
        if not self.ensure_initialized():
            return False

        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False

    # MARK: - Resource Management
    def cleanup(self) -> None:
        """Clean up Pygame resources."""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            if pygame.get_init():
                pygame.quit()
            self._initialized = False
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during cleanup: {str(e)}")
