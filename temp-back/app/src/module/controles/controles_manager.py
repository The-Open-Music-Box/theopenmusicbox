# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Controls Manager Module.

Provides a central manager for all physical controls, handling
initialization, event processing, and resource cleanup.

This manager acts as a facade over the hardware-specific implementations
and provides a unified RxPy observable for all control events.
"""

import threading
from typing import List

from rx.subject import Subject

from app.src.module.controles.controles_factory import create_controles_hardware
from app.src.module.controles.events.controles_events import ControlesEventType
from app.src.module.controles.input_devices.button import Button
from app.src.module.controles.input_devices.rotary_encoder import RotaryEncoder
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.config import config

logger = ImprovedLogger(__name__)


class ControlesManager:
    """Central manager for all physical controls.

    This class:
    1. Creates and manages the appropriate hardware implementation
    2. Initializes physical control devices (buttons and rotary encoders)
    3. Provides an observable stream of control events
    4. Handles resource cleanup

    It follows the Facade pattern, providing a simple interface to the complex
    underlying controls subsystem.
    """

    def __init__(self):
        """Initialize the controls manager.

        The manager starts in an uninitialized state and must be
        explicitly initialized via the initialize() method before use.
        """
        self._hardware = None
        self._initialized = False
        self._running = False
        self._lock = threading.Lock()

        # RxPy Subject for event emission
        self._event_subject = Subject()

        # Store device instances for cleanup
        self._devices: List[object] = []

    def initialize(self) -> bool:
        """Initialize the controls system.

        Creates the appropriate hardware implementation and ensures
        everything is ready for operation.

        Returns:
            True if initialization succeeded, False otherwise
        """
        with self._lock:
            if self._initialized:
                logger.log(LogLevel.WARNING, "Controls manager already initialized")
                return True

            try:
                # Create hardware implementation via factory
                self._hardware = create_controles_hardware()

                # Mark as initialized
                self._initialized = True
                logger.log(LogLevel.INFO, "Controls manager initialized successfully")
                return True
            except Exception as e:
                logger.log(
                    LogLevel.ERROR, f"Failed to initialize controls manager: {str(e)}"
                )
                return False

    def start(self) -> bool:
        """Start the controls system.

        Creates and initializes all control devices using the configured pin assignments.
        Must be called after initialize() and before using the system.

        Returns:
            True if system started successfully, False otherwise
        """
        with self._lock:
            if not self._initialized:
                logger.log(
                    LogLevel.ERROR, "Cannot start controls system: Not initialized"
                )
                return False

            if self._running:
                logger.log(LogLevel.WARNING, "Controls system already running")
                return True

            try:
                # Create input devices with appropriate pin assignments and event types

                # Create "next track" button
                next_track_button = Button(
                    hardware=self._hardware,
                    pin=config.hardware.gpio_next_track_button,
                    event_type=ControlesEventType.NEXT_TRACK,
                    name="next_track",
                    event_subject=self._event_subject,
                    pull_up=True,  # Connected to GND
                )
                self._devices.append(next_track_button)

                # Create "previous track" button
                prev_track_button = Button(
                    hardware=self._hardware,
                    pin=config.hardware.gpio_previous_track_button,
                    event_type=ControlesEventType.PREVIOUS_TRACK,
                    name="previous_track",
                    event_subject=self._event_subject,
                    pull_up=True,  # Connected to GND
                )
                self._devices.append(prev_track_button)

                # Create volume rotary encoder
                volume_encoder = RotaryEncoder(
                    hardware=self._hardware,
                    clk_pin=config.hardware.gpio_volume_encoder_clk,
                    dt_pin=config.hardware.gpio_volume_encoder_dt,
                    name="volume",
                    clockwise_event_type=ControlesEventType.VOLUME_UP,
                    counter_clockwise_event_type=ControlesEventType.VOLUME_DOWN,
                    event_subject=self._event_subject,
                    sw_pin=config.hardware.gpio_volume_encoder_sw,
                    sw_event_type=ControlesEventType.PLAY_PAUSE,
                    pull_up=True,
                )
                self._devices.append(volume_encoder)

                # Mark as running
                self._running = True
                logger.log(LogLevel.INFO, "✓ Controls system started successfully")
                return True
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Failed to start controls system: {str(e)}")
                # Clean up any devices that were created before the error
                self._cleanup_devices()
                return False

    def stop(self) -> None:
        """Stop the controls system.

        Releases hardware resources but keeps the manager initialized,
        so it can be started again later.
        """
        with self._lock:
            if not self._running:
                return

            self._cleanup_devices()
            self._running = False
            logger.log(LogLevel.INFO, "Controls system stopped")

    def cleanup(self) -> None:
        """Clean up all resources.

        Stops the system if it's running and releases all hardware
        resources. After calling this, the manager must be re-
        initialized before use.
        """
        with self._lock:
            # Stop the system if it's running
            if self._running:
                self.stop()

            # Clean up hardware resources
            if self._hardware:
                try:
                    self._hardware.cleanup()
                except Exception as e:
                    logger.log(
                        LogLevel.WARNING, f"Error cleaning up hardware: {str(e)}"
                    )

            # Reset initialization state
            self._initialized = False
            self._hardware = None
            logger.log(LogLevel.INFO, "Controls manager cleaned up")

    def _cleanup_devices(self) -> None:
        """Clean up all device instances.

        Called internally when stopping or cleaning up the system.
        """
        # Clear the devices list
        self._devices.clear()
        logger.log(LogLevel.DEBUG, "Devices cleaned up")

    @property
    def event_observable(self):
        """Get the observable for control events.

        Returns the RxPy Subject that emits ControlesEvents.
        Subscribers will receive events from all control devices.

        Returns:
            The RxPy Subject for control events
        """
        return self._event_subject

    @property
    def is_initialized(self) -> bool:
        """Check if the controls manager is initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    @property
    def is_running(self) -> bool:
        """Check if the controls system is running.

        Returns:
            True if running, False otherwise
        """
        return self._running
