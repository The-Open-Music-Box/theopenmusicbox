#!/usr/bin/env python3
"""
Test Physical Controls Manual Script.

Manual testing script for physical controls integration.
Can be used to test both mock and real GPIO hardware.
"""

import os
import sys
import asyncio
import signal
from typing import Optional

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.src.controllers.physical_controls_manager import PhysicalControlsManager
from app.src.config.hardware_config import HardwareConfig
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

logger = get_logger(__name__)


class MockAudioController:
    """Mock audio controller for testing."""

    def __init__(self):
        self.current_track = 1
        self.is_playing = False
        self.volume = 50

    def next_track(self) -> bool:
        """Simulate next track."""
        self.current_track += 1
        print(f"🎵 NEXT TRACK: Track {self.current_track}")
        return True

    def previous_track(self) -> bool:
        """Simulate previous track."""
        self.current_track = max(1, self.current_track - 1)
        print(f"🎵 PREVIOUS TRACK: Track {self.current_track}")
        return True

    def toggle_playback(self) -> bool:
        """Simulate play/pause toggle."""
        self.is_playing = not self.is_playing
        state = "PLAYING" if self.is_playing else "PAUSED"
        print(f"🎵 PLAY/PAUSE: {state}")
        return True

    def increase_volume(self) -> bool:
        """Simulate volume increase."""
        self.volume = min(100, self.volume + 5)
        print(f"🔊 VOLUME UP: {self.volume}%")
        return True

    def decrease_volume(self) -> bool:
        """Simulate volume decrease."""
        self.volume = max(0, self.volume - 5)
        print(f"🔉 VOLUME DOWN: {self.volume}%")
        return True


class PhysicalControlsTester:
    """Physical controls testing application."""

    def __init__(self, use_mock: bool = True):
        """Initialize tester.

        Args:
            use_mock: Whether to use mock hardware or real GPIO
        """
        self.use_mock = use_mock
        self.running = True
        self.manager: Optional[PhysicalControlsManager] = None
        self.audio_controller = MockAudioController()

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Set environment variable for mock mode
        if use_mock:
            os.environ["USE_MOCK_HARDWARE"] = "true"
        else:
            os.environ.pop("USE_MOCK_HARDWARE", None)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False

    async def initialize(self) -> bool:
        """Initialize physical controls."""
        try:
            print("=" * 60)
            print("🔌 PHYSICAL CONTROLS TESTER")
            print("=" * 60)
            print(f"Mode: {'Mock Hardware' if self.use_mock else 'Real GPIO Hardware'}")
            print("=" * 60)

            # Create hardware config
            hardware_config = HardwareConfig(
                gpio_next_track_button=26,
                gpio_previous_track_button=16,
                gpio_volume_encoder_clk=8,
                gpio_volume_encoder_dt=12,
                gpio_volume_encoder_sw=7,
                mock_hardware=self.use_mock
            )

            print("📋 Hardware Configuration:")
            print(f"  Next Track Button: GPIO {hardware_config.gpio_next_track_button}")
            print(f"  Previous Track Button: GPIO {hardware_config.gpio_previous_track_button}")
            print(f"  Play/Pause Button: GPIO {hardware_config.gpio_volume_encoder_sw}")
            print(f"  Volume Encoder CLK: GPIO {hardware_config.gpio_volume_encoder_clk}")
            print(f"  Volume Encoder DT: GPIO {hardware_config.gpio_volume_encoder_dt}")
            print()

            # Create physical controls manager
            self.manager = PhysicalControlsManager(
                audio_controller=self.audio_controller,
                hardware_config=hardware_config
            )

            # Initialize
            print("🔧 Initializing physical controls...")
            success = await self.manager.initialize()

            if success:
                print("✅ Physical controls initialized successfully!")

                # Get status
                status = self.manager.get_status()
                print("\n📊 Status:")
                for key, value in status.items():
                    print(f"  {key}: {value}")

                return True
            else:
                print("❌ Failed to initialize physical controls")
                return False

        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            return False

    async def run_manual_test(self):
        """Run manual testing interface."""
        if not self.use_mock:
            print("\n🔌 Real GPIO Mode: Press physical buttons to test")
            print("   - GPIO 26: Next Track")
            print("   - GPIO 16: Previous Track")
            print("   - GPIO 7: Play/Pause")
            print("   - Rotary Encoder: Volume Control")
            print("\n⌨️  Or use keyboard commands:")
        else:
            print("\n🧪 Mock Mode: Use keyboard commands to simulate:")

        print("   n = Next Track")
        print("   p = Previous Track")
        print("   s = Play/Pause (Space)")
        print("   + = Volume Up")
        print("   - = Volume Down")
        print("   q = Quit")
        print("\nPress Enter after each command, or Ctrl+C to quit")
        print("=" * 60)

        # Current state display
        print(f"🎵 Current: Track {self.audio_controller.current_track} | "
              f"{'Playing' if self.audio_controller.is_playing else 'Paused'} | "
              f"Volume {self.audio_controller.volume}%")

        if self.use_mock:
            await self._run_keyboard_interface()
        else:
            await self._run_hardware_monitoring()

    async def _run_keyboard_interface(self):
        """Run keyboard interface for mock testing."""
        mock_controls = self.manager.get_physical_controls()

        while self.running:
            try:
                # Use asyncio to handle input without blocking
                command = await asyncio.to_thread(input, "\n> ")
                command = command.strip().lower()

                if command in ['q', 'quit', 'exit']:
                    break
                elif command in ['n', 'next']:
                    await mock_controls.simulate_next_track()
                elif command in ['p', 'prev', 'previous']:
                    await mock_controls.simulate_previous_track()
                elif command in ['s', 'space', 'play', 'pause']:
                    await mock_controls.simulate_play_pause()
                elif command in ['+', 'up', 'vol+']:
                    await mock_controls.simulate_volume_up()
                elif command in ['-', 'down', 'vol-']:
                    await mock_controls.simulate_volume_down()
                elif command == 'status':
                    status = self.manager.get_status()
                    print("📊 Current Status:")
                    for key, value in status.items():
                        print(f"  {key}: {value}")
                elif command == 'help':
                    print("Available commands: n, p, s, +, -, status, help, q")
                elif command:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")

            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"❌ Error processing command: {e}")

    async def _run_hardware_monitoring(self):
        """Run hardware monitoring for real GPIO testing."""
        print("🔌 Monitoring hardware controls... (Ctrl+C to quit)")

        try:
            while self.running:
                # Just wait and let hardware events trigger callbacks
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            pass

    async def cleanup(self):
        """Clean up resources."""
        if self.manager:
            print("\n🧹 Cleaning up...")
            await self.manager.cleanup()
            print("✅ Cleanup completed")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Physical Controls Integration")
    parser.add_argument(
        "--real-gpio",
        action="store_true",
        help="Use real GPIO hardware instead of mock"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        # Enable debug logging
        import logging
        logging.basicConfig(level=logging.DEBUG)

    use_mock = not args.real_gpio

    if args.real_gpio and os.geteuid() != 0:
        print("⚠️  Real GPIO mode requires root privileges")
        print("   Run with: sudo python3 test_physical_controls.py --real-gpio")
        return 1

    tester = PhysicalControlsTester(use_mock=use_mock)

    try:
        if await tester.initialize():
            await tester.run_manual_test()
        else:
            print("❌ Failed to initialize tester")
            return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    finally:
        await tester.cleanup()

    print("\n🏁 Test completed")
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))