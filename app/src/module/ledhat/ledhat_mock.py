# app/src/module/ledhat/ledhat_mock.py

import time
import threading
from typing import Tuple, Optional, Dict, Any, List
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .ledhat_interface import LedHatInterface

logger = ImprovedLogger(__name__)

class MockLedHat(LedHatInterface):
    """
    Mock implementation of the LED strip controller for testing and development.
    """

    def __init__(self, num_pixels: int = 36, brightness: float = 0.2):
        """
        Initialize the mock LED strip controller.

        Args:
            num_pixels: Number of LEDs on the strip
            brightness: LED brightness (0.0 to 1.0)
        """
        self.num_pixels = num_pixels
        self.brightness = brightness
        self.pixels = [(0, 0, 0)] * num_pixels  # Simulates a pixel array
        self._running = False
        self._current_animation = None
        self._animation_params = {}
        self._animation_thread = None
        logger.log(LogLevel.INFO, f"Initialized Mock LED Hat with {num_pixels} pixels")

    def set_pixel(self, i: int, color: Tuple[int, int, int]) -> None:
        """
        Set the color of a specific pixel.

        Args:
            i: Pixel index
            color: RGB tuple (r, g, b) with values from 0 to 255
        """
        if 0 <= i < self.num_pixels:
            self.pixels[i] = color
            logger.log(LogLevel.DEBUG, f"[MockLedHat] Set pixel {i} to color {color}")

    def set_all_pixels(self, color: Tuple[int, int, int]) -> None:
        """
        Set all pixels to the same color.

        Args:
            color: RGB tuple (r, g, b) with values from 0 to 255
        """
        self.pixels = [color] * self.num_pixels
        logger.log(LogLevel.DEBUG, f"[MockLedHat] Set all pixels to color {color}")

    def clear(self) -> None:
        """Turn off all pixels."""
        self.pixels = [(0, 0, 0)] * self.num_pixels
        logger.log(LogLevel.DEBUG, "[MockLedHat] Cleared all pixels")

    def start_animation(self, animation_name: str, **kwargs) -> None:
        """
        Start a continuous animation in a separate thread.

        Args:
            animation_name: Name of the animation to run
            **kwargs: Animation-specific parameters
        """
        self.stop_animation()
        self._current_animation = animation_name
        self._animation_params = kwargs
        self._running = True

        # Start the animation in a separate thread
        self._animation_thread = threading.Thread(
            target=self._run_animation,
            args=(animation_name, kwargs),
            daemon=True
        )
        self._animation_thread.start()
        logger.log(LogLevel.INFO, f"[MockLedHat] Started animation '{animation_name}' with params {kwargs}")

    def _run_animation(self, animation_name: str, kwargs: dict) -> None:
        """
        Simulates the execution of the specified animation in a separate thread.

        Args:
            animation_name: Name of the animation to run
            kwargs: Animation-specific parameters
        """
        try:
            # Simulate the animation running for a few seconds
            animation_duration = kwargs.get('duration', 10)
            start_time = time.time()

            while self._running and (time.time() - start_time < animation_duration):
                # Simulate an animation update
                logger.log(LogLevel.DEBUG, f"[MockLedHat] Running animation '{animation_name}' (t={time.time() - start_time:.1f}s)")
                time.sleep(0.5)  # Reduce log frequency

            logger.log(LogLevel.INFO, f"[MockLedHat] Animation '{animation_name}' completed or stopped")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"[MockLedHat] Error in animation {animation_name}: {e}")
        finally:
            # Reset state if the animation ends
            if self._current_animation == animation_name:
                self._running = False
                self._current_animation = None
                self._animation_params = {}

    def stop_animation(self) -> None:
        """Stop the current animation."""
        if self._running:
            self._running = False
            if self._animation_thread and self._animation_thread.is_alive():
                self._animation_thread.join(timeout=1.0)  # Wait for the thread to terminate
            self._current_animation = None
            self._animation_params = {}
            self._animation_thread = None
            logger.log(LogLevel.INFO, "[MockLedHat] Animation stopped")

    def close(self) -> None:
        """Clean up and release resources."""
        try:
            logger.log(LogLevel.INFO, "Cleaning up mock LED hat resources")
            self.stop_animation()
            self.clear()
            logger.log(LogLevel.INFO, "Mock LED hat resources cleaned up successfully")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during mock LED hat cleanup: {e}")

    def cleanup(self) -> None:
        """Alias for close() for container compatibility."""
        self.close()

    @property
    def current_animation(self) -> Optional[str]:
        """Returns the name of the current animation, or None if no animation is running."""
        return self._current_animation

    @property
    def animation_params(self) -> Dict[str, Any]:
        """Returns the parameters of the current animation."""
        return self._animation_params.copy()