# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Physical controls manager for handling hardware input devices.

This manager handles physical control devices such as buttons, rotary encoders,
and other GPIO-based input devices. It provides a clean interface between
hardware controls and the audio controller.
"""


from typing import Optional

from app.src.controllers.audio_controller import AudioController
from app.src.domain.protocols.physical_controls_protocol import (
    PhysicalControlsProtocol,
    PhysicalControlEvent,
)
from app.src.infrastructure.hardware.controls.controls_factory import PhysicalControlsFactory
from app.src.config.hardware_config import HardwareConfig
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from app.src.services.error.unified_error_decorator import handle_errors

logger = get_logger(__name__)


class PhysicalControlsManager:
    """Manager for physical control devices and hardware inputs.

    Handles initialization, event subscription, and cleanup of physical
    control devices. Coordinates between hardware events and audio control.
    """

    def __init__(self, audio_controller: AudioController = None, hardware_config: Optional[HardwareConfig] = None):
        """Initialize PhysicalControlsManager with real GPIO integration.

        Args:
            audio_controller: AudioController instance for handling audio operations
            hardware_config: Hardware configuration for GPIO pins
        """
        # Use unified controller if not provided
        if audio_controller is None:
            from app.src.domain.controllers.unified_controller import unified_controller

            audio_controller = unified_controller

        self.audio_controller = audio_controller

        # Get hardware config if not provided
        if hardware_config is None:
            from app.src.config import config
            hardware_config = config.hardware_config

        self.hardware_config = hardware_config
        self._is_initialized = False
        self._physical_controls: Optional[PhysicalControlsProtocol] = None

        # Create physical controls implementation
        self._physical_controls = PhysicalControlsFactory.create_controls(self.hardware_config)

        logger.log(LogLevel.INFO, "PhysicalControlsManager initialized with GPIO integration")

    @handle_errors("initialize")
    async def initialize(self) -> bool:
        """Initialize physical controls with real GPIO integration.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            if not self.audio_controller:
                logger.log(LogLevel.ERROR, "No audio controller available for physical controls integration")
                return False

            if not self._physical_controls:
                logger.log(LogLevel.ERROR, "No physical controls implementation available")
                return False

            # Initialize the physical controls hardware
            success = await self._physical_controls.initialize()
            if not success:
                logger.log(LogLevel.ERROR, "Failed to initialize physical controls hardware")
                return False

            # Setup event handlers for GPIO events
            self._setup_event_handlers()

            self._is_initialized = True
            logger.log(LogLevel.INFO, "✅ Physical controls manager initialized with GPIO integration")
            return True

        except Exception as e:
            logger.log(LogLevel.ERROR, f"❌ Failed to initialize physical controls: {e}")
            return False

    def _setup_event_handlers(self) -> None:
        """Setup event handlers for physical control events."""
        if not self._physical_controls:
            return

        # Setup button event handlers
        self._physical_controls.set_event_handler(
            PhysicalControlEvent.BUTTON_NEXT_TRACK,
            self.handle_next_track
        )

        self._physical_controls.set_event_handler(
            PhysicalControlEvent.BUTTON_PREVIOUS_TRACK,
            self.handle_previous_track
        )

        self._physical_controls.set_event_handler(
            PhysicalControlEvent.BUTTON_PLAY_PAUSE,
            self.handle_play_pause
        )

        # Setup encoder event handlers
        self._physical_controls.set_event_handler(
            PhysicalControlEvent.ENCODER_VOLUME_UP,
            lambda: self.handle_volume_change("up")
        )

        self._physical_controls.set_event_handler(
            PhysicalControlEvent.ENCODER_VOLUME_DOWN,
            lambda: self.handle_volume_change("down")
        )

        logger.log(LogLevel.INFO, "Physical control event handlers configured")

    @handle_errors("cleanup")
    async def cleanup(self) -> None:
        """Clean up physical controls resources."""
        if self._is_initialized and self._physical_controls:
            logger.log(LogLevel.INFO, "Cleaning up physical controls manager")
            try:
                await self._physical_controls.cleanup()
                logger.log(LogLevel.INFO, "✅ Physical controls hardware cleanup completed")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"❌ Error during physical controls cleanup: {e}")

            self._is_initialized = False

    def is_initialized(self) -> bool:
        """Check if physical controls are initialized.

        Returns:
            True if controls are initialized and ready, False otherwise
        """
        return self._is_initialized

    @handle_errors("handle_play_pause")
    def handle_play_pause(self) -> None:
        """Handle play/pause control for domain architecture."""
        logger.log(LogLevel.INFO, "🎮 Physical Control: Play/Pause button pressed")
        if hasattr(self.audio_controller, "toggle_playback"):
            success = self.audio_controller.toggle_playback()
            if success:
                logger.log(LogLevel.INFO, "✅ Play/pause action completed successfully")
            else:
                logger.log(LogLevel.WARNING, "⚠️ Play/pause failed via domain audio controller")
        else:
            logger.log(LogLevel.WARNING, "⚠️ Play/pause not supported by current audio controller")

    @handle_errors("handle_volume_change")
    def handle_volume_change(self, direction: str) -> None:
        """Handle volume change control for domain architecture.

        Args:
            direction: Volume change direction ("up" or "down")
        """
        logger.log(LogLevel.INFO, f"🎮 Physical Control: Volume {direction} encoder rotated")
        if direction == "up" and hasattr(self.audio_controller, "increase_volume"):
            success = self.audio_controller.increase_volume()
            action = "increased"
        elif direction == "down" and hasattr(self.audio_controller, "decrease_volume"):
            success = self.audio_controller.decrease_volume()
            action = "decreased"
        else:
            logger.log(
                LogLevel.WARNING, f"⚠️ Volume {direction} not supported by current audio controller"
            )
            return
        if success:
            logger.log(LogLevel.INFO, f"✅ Volume {action} successfully")
        else:
            logger.log(LogLevel.WARNING, f"⚠️ Volume {direction} failed via domain controller")

    @handle_errors("handle_next_track")
    def handle_next_track(self) -> None:
        """Handle next track control for domain architecture."""
        logger.log(LogLevel.INFO, "🎮 Physical Control: Next track button pressed")
        # Try sync wrapper first, then fallback to async method
        if hasattr(self.audio_controller, "next_track_sync"):
            success = self.audio_controller.next_track_sync()
            if success:
                logger.log(LogLevel.INFO, "✅ Next track action completed successfully")
            else:
                logger.log(LogLevel.WARNING, "⚠️ Next track failed via domain audio controller")
        elif hasattr(self.audio_controller, "next_track"):
            success = self.audio_controller.next_track()
            if success:
                logger.log(LogLevel.INFO, "✅ Next track action completed successfully")
            else:
                logger.log(LogLevel.WARNING, "⚠️ Next track failed via domain audio controller")
        else:
            logger.log(LogLevel.WARNING, "⚠️ Next track not supported by current audio controller")

    @handle_errors("handle_previous_track")
    def handle_previous_track(self) -> None:
        """Handle previous track control for domain architecture."""
        logger.log(LogLevel.INFO, "🎮 Physical Control: Previous track button pressed")
        # Try sync wrapper first, then fallback to async method
        if hasattr(self.audio_controller, "previous_track_sync"):
            success = self.audio_controller.previous_track_sync()
            if success:
                logger.log(LogLevel.INFO, "✅ Previous track action completed successfully")
            else:
                logger.log(LogLevel.WARNING, "⚠️ Previous track failed via domain audio controller")
        elif hasattr(self.audio_controller, "previous_track"):
            success = self.audio_controller.previous_track()
            if success:
                logger.log(LogLevel.INFO, "✅ Previous track action completed successfully")
            else:
                logger.log(LogLevel.WARNING, "⚠️ Previous track failed via domain audio controller")
        else:
            logger.log(LogLevel.WARNING, "⚠️ Previous track not supported by current audio controller")

    def get_status(self) -> dict:
        """Get the current status of physical controls.

        Returns:
            Dictionary containing status information
        """
        base_status = {
            "initialized": self._is_initialized,
            "audio_controller_available": self.audio_controller is not None,
            "domain_architecture": True,
            "gpio_integration": True,
        }

        # Add physical controls status if available
        if self._physical_controls:
            base_status.update(self._physical_controls.get_status())

        return base_status

    def get_physical_controls(self) -> Optional[PhysicalControlsProtocol]:
        """Get the physical controls implementation for testing.

        Returns:
            The physical controls implementation instance
        """
        return self._physical_controls
