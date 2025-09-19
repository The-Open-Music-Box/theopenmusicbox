#!/usr/bin/env python3
"""
GPIO Logging Test

Test GPIO controls with enhanced logging to see if events are detected.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

async def test_gpio_with_enhanced_logging():
    """Test GPIO controls with detailed logging."""
    print("=" * 60)
    print("🔍 GPIO LOGGING TEST")
    print("=" * 60)

    # Import after path setup
    from app.src.config.hardware_config import HardwareConfig
    from app.src.infrastructure.hardware.controls.gpio_controls_implementation import GPIOPhysicalControls
    from app.src.domain.protocols.physical_controls_protocol import PhysicalControlEvent

    # Create hardware config
    config = HardwareConfig()
    print("📋 Hardware Configuration:")
    print(f"   Next button: GPIO {config.gpio_next_track_button}")
    print(f"   Previous button: GPIO {config.gpio_previous_track_button}")
    print(f"   Play/Pause button: GPIO {config.gpio_volume_encoder_sw}")
    print(f"   Volume encoder CLK: GPIO {config.gpio_volume_encoder_clk}")
    print(f"   Volume encoder DT: GPIO {config.gpio_volume_encoder_dt}")
    print()

    # Create GPIO controls
    gpio_controls = GPIOPhysicalControls(config)

    # Set up event handlers with detailed logging
    def handle_next():
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🎯 [{timestamp}] NEXT TRACK EVENT TRIGGERED!")

    def handle_previous():
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🎯 [{timestamp}] PREVIOUS TRACK EVENT TRIGGERED!")

    def handle_play_pause():
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🎯 [{timestamp}] PLAY/PAUSE EVENT TRIGGERED!")

    def handle_volume_up():
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🎯 [{timestamp}] VOLUME UP EVENT TRIGGERED!")

    def handle_volume_down():
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🎯 [{timestamp}] VOLUME DOWN EVENT TRIGGERED!")

    # Register event handlers
    gpio_controls.set_event_handler(PhysicalControlEvent.BUTTON_NEXT_TRACK, handle_next)
    gpio_controls.set_event_handler(PhysicalControlEvent.BUTTON_PREVIOUS_TRACK, handle_previous)
    gpio_controls.set_event_handler(PhysicalControlEvent.BUTTON_PLAY_PAUSE, handle_play_pause)
    gpio_controls.set_event_handler(PhysicalControlEvent.ENCODER_VOLUME_UP, handle_volume_up)
    gpio_controls.set_event_handler(PhysicalControlEvent.ENCODER_VOLUME_DOWN, handle_volume_down)

    # Initialize GPIO controls
    print("🔌 Initializing GPIO controls...")
    success = await gpio_controls.initialize()

    if not success:
        print("❌ Failed to initialize GPIO controls")
        return False

    print("✅ GPIO controls initialized successfully")

    # Show status
    status = gpio_controls.get_status()
    print("\n📊 GPIO Controls Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")

    if not status.get("gpio_available", False):
        print("\n⚠️ Running in mock mode - physical buttons won't work")
        print("To test with real hardware, run this script on a Raspberry Pi")
        return True

    print("\n" + "=" * 60)
    print("🎯 LISTENING FOR BUTTON PRESSES")
    print("=" * 60)
    print("Press your physical buttons and rotate the encoder...")
    print("Events will be logged above when detected.")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    try:
        # Listen for events
        start_time = asyncio.get_event_loop().time()
        while True:
            await asyncio.sleep(0.1)

            # Status update every 10 seconds
            elapsed = asyncio.get_event_loop().time() - start_time
            if int(elapsed) > 0 and int(elapsed) % 10 == 0:
                print(f"\n📊 [{int(elapsed)}s] Still listening for GPIO events...")
                await asyncio.sleep(1)  # Avoid repeated messages

    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")

    finally:
        print("\n🧹 Cleaning up GPIO controls...")
        await gpio_controls.cleanup()

    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_gpio_with_enhanced_logging())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)