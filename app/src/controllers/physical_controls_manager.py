# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Physical controls manager for handling hardware input devices.

This manager handles physical control devices such as buttons, rotary encoders,
and other GPIO-based input devices. It provides a clean interface between
hardware controls and the audio controller.
"""

from typing import Optional, Callable

from app.src.controllers.audio_controller import AudioController
from app.src.module.controles import get_controles_manager
from app.src.module.controles.events.controles_events import ControlesEventType
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class PhysicalControlsManager:
    """Manager for physical control devices and hardware inputs.
    
    Handles initialization, event subscription, and cleanup of physical
    control devices. Coordinates between hardware events and audio control.
    """

    def __init__(self, audio_controller: AudioController):
        """Initialize the PhysicalControlsManager.
        
        Args:
            audio_controller: AudioController instance for handling audio operations
        """
        self.audio_controller = audio_controller
        self.controls_manager = None
        self.controls_subscription = None
        self._is_initialized = False

    def initialize(self) -> bool:
        """Initialize physical controls integration.
        
        Sets up the controls manager and subscribes to control events.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.controls_manager = get_controles_manager()

            if (
                self.controls_manager
                and self.controls_manager.initialize()
                and self.controls_manager.start()
            ):
                logger.log(LogLevel.INFO, "Controls manager started successfully")

                self.controls_subscription = (
                    self.controls_manager.event_observable.subscribe(
                        self._handle_control_event,
                        on_error=lambda e: logger.log(
                            LogLevel.ERROR, f"Error in control event handling: {str(e)}"
                        ),
                    )
                )
                logger.log(LogLevel.INFO, "Subscribed to physical control events")
                self._is_initialized = True
                return True
            else:
                logger.log(
                    LogLevel.WARNING,
                    "Failed to start controls manager or it is not available",
                )
                return False
                
        except (AttributeError, TypeError, ValueError, RuntimeError, ImportError) as e:
            logger.log(
                LogLevel.ERROR, f"Failed to set up controls integration: {str(e)}"
            )
            return False

    def cleanup(self) -> None:
        """Clean up resources associated with physical controls.

        Unsubscribes from control events and releases resources.
        """
        try:
            if self.controls_subscription:
                self.controls_subscription.dispose()
                self.controls_subscription = None
                logger.log(LogLevel.INFO, "Unsubscribed from physical control events")

            if self.controls_manager:
                self.controls_manager.stop()
                self.controls_manager = None
                logger.log(LogLevel.INFO, "Controls manager stopped successfully")
                
            self._is_initialized = False
            
        except (AttributeError, TypeError, RuntimeError) as e:
            logger.log(
                LogLevel.ERROR, f"Error while cleaning up controls resources: {str(e)}"
            )

    def is_initialized(self) -> bool:
        """Check if physical controls are initialized.
        
        Returns:
            True if controls are initialized and ready, False otherwise
        """
        return self._is_initialized

    def _handle_control_event(self, event) -> None:
        """Handle control events from physical inputs.

        Args:
            event: The ControlesEvent to handle
        """
        if not self.audio_controller.is_audio_available():
            logger.log(
                LogLevel.WARNING,
                "Cannot handle control event: No audio service available.",
            )
            return

        logger.log(
            LogLevel.INFO,
            f"[EVENT_HANDLER] Received: {event.event_type.name} from {event.source}, metadata: {event.metadata}",
        )

        try:
            if event.event_type == ControlesEventType.PLAY_PAUSE:
                success = self.audio_controller.toggle_playback()
                if not success:
                    logger.log(
                        LogLevel.ERROR,
                        "Failed to toggle playback from physical control"
                    )

            elif event.event_type == ControlesEventType.VOLUME_DOWN:
                # Note: VOLUME_DOWN actually increases volume (clockwise rotation)
                success = self.audio_controller.increase_volume()
                if not success:
                    logger.log(
                        LogLevel.ERROR,
                        "Failed to increase volume from physical control"
                    )

            elif event.event_type == ControlesEventType.VOLUME_UP:
                # Note: VOLUME_UP actually decreases volume (counter-clockwise rotation)
                success = self.audio_controller.decrease_volume()
                if not success:
                    logger.log(
                        LogLevel.ERROR,
                        "Failed to decrease volume from physical control"
                    )

            elif event.event_type == ControlesEventType.NEXT_TRACK:
                success = self.audio_controller.next_track()
                if not success:
                    logger.log(
                        LogLevel.ERROR,
                        "Failed to skip to next track from physical control"
                    )

            elif event.event_type == ControlesEventType.PREVIOUS_TRACK:
                success = self.audio_controller.previous_track()
                if not success:
                    logger.log(
                        LogLevel.ERROR,
                        "Failed to go to previous track from physical control"
                    )

            else:
                logger.log(
                    LogLevel.WARNING,
                    f"Unhandled control event type: {event.event_type.name}",
                )

        except (AttributeError, TypeError, ValueError, KeyError, IndexError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Error handling control event {event.event_type.name}: {str(e)}",
            )

    def get_status(self) -> dict:
        """Get the current status of physical controls.
        
        Returns:
            Dictionary containing status information
        """
        return {
            "initialized": self._is_initialized,
            "controls_manager_available": self.controls_manager is not None,
            "subscription_active": self.controls_subscription is not None,
            "audio_controller_available": self.audio_controller is not None
        }
