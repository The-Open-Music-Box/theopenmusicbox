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

    def __init__(self, num_pixels: int = 36, brightness: float = 0.2, pin: int = 12):
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

    def set_pixel(self, i: int, color: Tuple[int, int, int]) -> None:
        """
        Set the color of a specific pixel.

        Args:
            i: Pixel index
            color: RGB tuple (r, g, b) with values from 0 to 255
        """
        if 0 <= i < self.num_pixels:
            r, g, b = color
            self.pixels.setPixelColor(i, Color(r, g, b))

    def set_all_pixels(self, color: Tuple[int, int, int]) -> None:
        """
        Set all pixels to the same color.

        Args:
            color: RGB tuple (r, g, b) with values from 0 to 255
        """
        r, g, b = color
        for i in range(self.num_pixels):
            self.pixels.setPixelColor(i, Color(r, g, b))
        self.pixels.show()

    def clear(self) -> None:
        """Turn off all pixels."""
        for i in range(self.num_pixels):
            self.pixels.setPixelColor(i, Color(0, 0, 0))
        self.pixels.show()

    def rainbow_cycle(self, wait: float = 0.01) -> None:
        """
        Rainbow cycle animation.

        Args:
            wait: Wait time between updates (in seconds)
        """
        for j in range(255):
            if not self._running:
                break
            for i in range(self.num_pixels):
                rc_index = (i * 256 // self.num_pixels) + j
                self.pixels.setPixelColor(i, self._wheel(rc_index & 255))
            self.pixels.show()
            time.sleep(wait)

    def color_wipe(self, color: Tuple[int, int, int], wait: float = 0.05) -> None:
        """
        Progressive color filling animation.

        Args:
            color: RGB tuple (r, g, b) with values from 0 to 255
            wait: Wait time between updates (in seconds)
        """
        r, g, b = color
        for i in range(self.num_pixels):
            if not self._running:
                break
            self.pixels.setPixelColor(i, Color(r, g, b))
            self.pixels.show()
            time.sleep(wait)

    def theater_chase(self, color: Tuple[int, int, int], wait: float = 0.05, iterations: int = 10) -> None:
        """
        Theater chase animation.

        Args:
            color: RGB tuple (r, g, b) with values from 0 to 255
            wait: Wait time between updates (in seconds)
            iterations: Number of animation iterations
        """
        r, g, b = color
        color_value = Color(r, g, b)

        iteration_count = 0
        while self._running and (iterations <= 0 or iteration_count < iterations):
            for q in range(3):
                if not self._running:
                    break
                for i in range(0, self.num_pixels, 3):
                    if i + q < self.num_pixels:
                        self.pixels.setPixelColor(i + q, color_value)
                self.pixels.show()
                time.sleep(wait)
                for i in range(0, self.num_pixels, 3):
                    if i + q < self.num_pixels:
                        self.pixels.setPixelColor(i + q, Color(0, 0, 0))
            iteration_count += 1

    def pulse(self, color: Tuple[int, int, int], wait: float = 0.01, steps: int = 100) -> None:
        """
        Color pulsation animation.

        Args:
            color: RGB tuple (r, g, b) with values from 0 to 255
            wait: Wait time between updates (in seconds)
            steps: Number of steps for the pulsation
        """
        r, g, b = color

        while self._running:
            # Increasing intensity
            for i in range(steps):
                if not self._running:
                    break
                intensity = i / steps
                for j in range(self.num_pixels):
                    self.pixels.setPixelColor(j, Color(
                        int(r * intensity),
                        int(g * intensity),
                        int(b * intensity)
                    ))
                self.pixels.show()
                time.sleep(wait)

            # Decreasing intensity
            for i in range(steps, 0, -1):
                if not self._running:
                    break
                intensity = i / steps
                for j in range(self.num_pixels):
                    self.pixels.setPixelColor(j, Color(
                        int(r * intensity),
                        int(g * intensity),
                        int(b * intensity)
                    ))
                self.pixels.show()
                time.sleep(wait)

    def breathing_effect(self, color: Tuple[int, int, int], wait: float = 0.01, steps: int = 100) -> None:
        """
        Breathing effect - brightness rises and falls using a sinusoidal curve.

        Args:
            color: RGB tuple (r, g, b) with values from 0 to 255
            wait: Wait time between updates (in seconds)
            steps: Number of steps for the breathing effect
        """
        r, g, b = color

        while self._running:
            # Complete breathing cycle
            for k in range(steps):
                if not self._running:
                    break
                brightness = math.sin(math.pi * k / steps) * math.sin(math.pi * k / steps)
                r_adj = int(r * brightness)
                g_adj = int(g * brightness)
                b_adj = int(b * brightness)
                for i in range(self.num_pixels):
                    self.pixels.setPixelColor(i, Color(r_adj, g_adj, b_adj))
                self.pixels.show()
                time.sleep(wait)

    def rotating_circle(self, color: Tuple[int, int, int] = (0, 0, 255),
                       background_color: Tuple[int, int, int] = (0, 0, 0),
                       segment_length: int = 5,
                       rotation_time: float = 3.0,
                       continuous: bool = False) -> None:
        """
        Animation of a light segment rotating around the LED circle.

        Args:
            color: RGB tuple (r, g, b) for the light segment color
            background_color: RGB tuple (r, g, b) for the background color
            segment_length: Number of lit LEDs in the segment
            rotation_time: Time in seconds for a complete rotation
            continuous: If True, the animation continues in a loop until stop_animation()
        """
        try:
            r, g, b = color
            color_value = Color(r, g, b)

            bg_r, bg_g, bg_b = background_color
            bg_color_value = Color(bg_r, bg_g, bg_b)

            # Calculate the delay between each step to achieve the desired rotation time
            steps = self.num_pixels
            wait = rotation_time / steps

            # Main animation loop
            iterations = 0
            while self._running or iterations == 0:
                for start_pos in range(self.num_pixels):
                    if not self._running and iterations > 0:
                        break

                    # Reset all pixels to background color
                    for i in range(self.num_pixels):
                        self.pixels.setPixelColor(i, bg_color_value)

                    # Light up the LED segment
                    for i in range(segment_length):
                        pixel_pos = (start_pos + i) % self.num_pixels
                        self.pixels.setPixelColor(pixel_pos, color_value)

                    self.pixels.show()
                    time.sleep(wait)

                iterations += 1
                if not continuous and iterations >= 1:
                    break

            # If the animation is not continuous or has been stopped, turn off the LEDs
            if not self._running:
                self.clear()

        except Exception as e:
            import traceback
            logger.log(LogLevel.ERROR, f"Error in rotating_circle: {e}")
            logger.log(LogLevel.DEBUG, f"Details: {traceback.format_exc()}")

    def circular_sweep(self, color: Tuple[int, int, int], wait: float = 0.005, duration: float = 5.0) -> None:
        """
        Circular sweep with trail effect.

        Args:
            color: RGB tuple (r, g, b) with values from 0 to 255
            wait: Wait time between updates (in seconds)
            duration: Duration of the animation in seconds
        """
        r, g, b = color
        color_value = Color(r, g, b)
        fade_factor = 0.9  # Fade factor for the trail

        start_time = time.time()
        # Initialize colors
        pixel_values = [0] * self.num_pixels

        steps = 0
        while self._running and (time.time() - start_time < duration):
            # Apply fade factor to all LEDs
            for i in range(self.num_pixels):
                pixel_color = pixel_values[i]
                r = (pixel_color >> 16) & 0xFF
                g = (pixel_color >> 8) & 0xFF
                b = pixel_color & 0xFF

                r = int(r * fade_factor)
                g = int(g * fade_factor)
                b = int(b * fade_factor)

                pixel_values[i] = Color(r, g, b)

            # Light up the head LED
            head_pos = steps % self.num_pixels
            pixel_values[head_pos] = color_value

            # Update LEDs
            for i in range(self.num_pixels):
                self.pixels.setPixelColor(i, pixel_values[i])

            self.pixels.show()
            time.sleep(wait)
            steps += 1

    def sparkle_effect(self, background: Tuple[int, int, int], sparkle_color: Tuple[int, int, int],
                      wait: float = 0.05, duration: float = 5.0) -> None:
        """
        Random sparkle effect on colored background.

        Args:
            background: RGB tuple (r, g, b) for the background color
            sparkle_color: RGB tuple (r, g, b) for the sparkle color
            wait: Wait time between updates (in seconds)
            duration: Duration of the animation in seconds
        """
        import random

        bg_r, bg_g, bg_b = background
        bg_color = Color(bg_r, bg_g, bg_b)

        sp_r, sp_g, sp_b = sparkle_color
        sp_color = Color(sp_r, sp_g, sp_b)

        # Set the background color
        for i in range(self.num_pixels):
            self.pixels.setPixelColor(i, bg_color)
        self.pixels.show()

        start_time = time.time()
        while self._running and (time.time() - start_time < duration):
            # Randomly choose a few LEDs to sparkle
            sparkle_positions = set()
            for k in range(5):  # 5 sparkles at a time
                sparkle_positions.add(random.randint(0, self.num_pixels - 1))

            # Light up the sparkles
            for pos in sparkle_positions:
                self.pixels.setPixelColor(pos, sp_color)
            self.pixels.show()
            time.sleep(wait)

            # Restore the background color for these LEDs
            for pos in sparkle_positions:
                self.pixels.setPixelColor(pos, bg_color)

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
            if animation_name == "rainbow_cycle":
                self.rainbow_cycle(**kwargs)
            elif animation_name == "color_wipe":
                self.color_wipe(**kwargs)
            elif animation_name == "theater_chase":
                self.theater_chase(**kwargs)
            elif animation_name == "pulse":
                self.pulse(**kwargs)
            elif animation_name == "rotating_circle":
                self.rotating_circle(**kwargs)
            elif animation_name == "breathing_effect":
                self.breathing_effect(**kwargs)
            elif animation_name == "circular_sweep":
                self.circular_sweep(**kwargs)
            elif animation_name == "sparkle_effect":
                self.sparkle_effect(**kwargs)
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
            self._animation_thread.join(timeout=1.0)  # Wait for the thread to terminate
        self._current_animation = None
        self._animation_params = {}
        self._animation_thread = None

    def close(self) -> None:
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

    def cleanup(self) -> None:
        """Alias for close() for container compatibility."""
        self.close()

    def _wheel(self, pos: int) -> int:
        """
        Helper function for rainbow animation.

        Args:
            pos: Position in the color wheel (0-255)

        Returns:
            Color value in Color format
        """
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    @property
    def current_animation(self) -> Optional[str]:
        """Returns the name of the current animation, or None if no animation is running."""
        return self._current_animation

    @property
    def animation_params(self) -> Dict[str, Any]:
        """Returns the parameters of the current animation."""
        return self._animation_params