# app/src/module/ledhat/ledhat_rpi_ws281x.py

import time
import math
import threading
from typing import Tuple, Optional, Dict, Any, List
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .ledhat_interface import LedHatInterface
from rpi_ws281x import PixelStrip, Color

logger = ImprovedLogger(__name__)

class RpiWs281xLedHat(LedHatInterface):
    """
    Implementation for Raspberry Pi LED strip controller using the rpi_ws281x library.
    Based on the example code in app/demo/ledhat.py.
    """

    def __init__(self, num_pixels: int, brightness: float, pin: int):
        """
        Initialize the LED strip controller for Raspberry Pi with rpi_ws281x.

        Args:
            num_pixels: Number of LEDs on the strip
            brightness: LED brightness (0.0 to 1.0)
            pin: The GPIO pin to which the strip is connected
        """
        self.num_pixels = num_pixels

        # Convert brightness (0.0-1.0) to integer value (0-255)
        led_brightness = int(brightness * 255)

        # Configuration for the LED strip
        LED_FREQ_HZ = 800000  # LED signal frequency in Hz
        LED_DMA = 10          # DMA channel to use for generating signal
        LED_INVERT = False    # Invert the signal (when using NPN transistor)
        LED_CHANNEL = 0       # '0' for GPIO 12, 18

        # Create the strip object with configuration
        self.pixels = PixelStrip(
            num_pixels, pin, LED_FREQ_HZ, LED_DMA, LED_INVERT, led_brightness, LED_CHANNEL
        )

        # Initialize the library
        self.pixels.begin()

        self._running = False
        self._current_animation = None
        self._animation_params = {}
        self._animation_thread = None
        logger.log(LogLevel.INFO, f"Initialized Raspberry Pi LED Hat (rpi_ws281x) with {num_pixels} pixels")

    def clear(self) -> None:
        """Turn off all pixels."""
        for i in range(self.num_pixels):
            self.pixels.setPixelColor(i, Color(0, 0, 0))
        self.pixels.show()

    # MARK: Animation methods

    def _rotating_circle(self, color: Tuple[int, int, int] = (0, 0, 255),
                        wait: float = 0.1) -> None:
        """
        Animation of a light segment rotating around the LED circle.

        Args:
            color: RGB tuple (r, g, b) for the light segment color
            background_color: RGB tuple (r, g, b) for the background color
            segment_length: Number of lit LEDs in the segment
            rotation_time: Time in seconds for a complete rotation
            continuous: If True, the animation continues in a loop until stop_animation()
        """
        background_color: Tuple[int, int, int] = (0, 0, 0)
        segment_length: int = 5
        rotation_time: float = 3.0
        continuous: bool = True

        try:
            r, g, b = color
            color_value = Color(r, g, b)

            bg_r, bg_g, bg_b = background_color
            bg_color_value = Color(bg_r, bg_g, bg_b)

            # Calculate the delay between each step to achieve the desired rotation time
            steps = self.num_pixels
            wait = rotation_time / steps

            # Main animation loop

            while self._running:
                for start_pos in range(self.num_pixels):
                    # Reset all pixels to background color
                    for i in range(self.num_pixels):
                        self.pixels.setPixelColor(i, bg_color_value)

                    # Light up the LED segment
                    for i in range(segment_length):
                        pixel_pos = (start_pos + i) % self.num_pixels
                        self.pixels.setPixelColor(pixel_pos, color_value)

                    self.pixels.show()
                    time.sleep(wait)

                if not continuous:
                    break

            # If the animation is not continuous or has been stopped, turn off the LEDs
            if not self._running:
                self.clear()

        except Exception as e:
            import traceback
            logger.log(LogLevel.ERROR, f"Error in rotating_circle: {e}")
            logger.log(LogLevel.DEBUG, f"Details: {traceback.format_exc()}")

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
        logger.log(LogLevel.INFO, f"Started animation '{animation_name}' with params {kwargs}")

    def _run_animation(self, animation_name: str, kwargs: dict) -> None:
        """
        Run the specified animation in a separate thread.

        Args:
            animation_name: Name of the animation to run
            kwargs: Animation-specific parameters
        """
        try:
            if animation_name == "rotating_circle":
                self._rotating_circle(**kwargs)
            else:
                logger.log(LogLevel.WARNING, f"Unknown animation: {animation_name}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error in animation {animation_name}: {e}")
        finally:
            # Reset state if the animation ends
            if self._current_animation == animation_name:
                self._running = False
                self._current_animation = None
                self._animation_params = {}

    def stop_animation(self) -> None:
        """Stop the current animation."""
        self._running = False
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1.0)
        self._current_animation = None
        self._animation_params = {}
        self._animation_thread = None

    def cleanup(self) -> None:
        """Clean up and release resources."""
        try:
            logger.log(LogLevel.INFO, "Cleaning up LED hat resources")
            self.stop_animation()
            self.clear()
            # Force display of turned off LEDs
            self.pixels.show()
            logger.log(LogLevel.INFO, "LED hat resources cleaned up successfully")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during LED hat cleanup: {e}")
