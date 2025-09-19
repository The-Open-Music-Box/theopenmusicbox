#!/usr/bin/env python3
"""
Button Detection Test for TheOpenMusicBox

Tests if GPIO buttons are actually being detected when pressed.
"""

import sys
import time
import signal
import os

def signal_handler(sig, frame):
    print("\n🛑 Test interrupted by user")
    cleanup_gpio()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def cleanup_gpio():
    """Clean up GPIO state."""
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
        print("🧹 GPIO cleaned up")
    except:
        pass

def test_button_detection():
    """Test if buttons are being detected."""
    print("=" * 60)
    print("🔘 BUTTON DETECTION TEST")
    print("=" * 60)
    print("Testing if GPIO buttons respond to physical presses...")
    print()

    # Check if we're on a Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry' not in f.read():
                print("⚠️ Not running on Raspberry Pi - button detection unavailable")
                return False
    except:
        print("⚠️ Could not determine if running on Raspberry Pi")
        return False

    # Try to import GPIO libraries
    try:
        import RPi.GPIO as GPIO
        from gpiozero import Button, RotaryEncoder, Device
        from gpiozero.pins.rpigpio import RPiGPIOFactory
        Device.pin_factory = RPiGPIOFactory()
        print("✅ GPIO libraries imported successfully")
    except ImportError as e:
        print(f"❌ GPIO libraries not available: {e}")
        return False

    # GPIO pin configuration
    pins = {
        'next_button': 26,
        'previous_button': 19,
        'play_pause_button': 13,
        'volume_encoder_clk': 20,
        'volume_encoder_dt': 21
    }

    print("📋 Testing pins:")
    for name, pin in pins.items():
        print(f"   {name}: GPIO {pin}")
    print()

    button_objects = {}
    press_counts = {}

    # Initialize buttons with event handlers
    for name, pin in pins.items():
        if 'encoder' not in name:  # Only test buttons, not encoder pins directly
            try:
                press_counts[name] = 0

                def make_handler(button_name):
                    def handler():
                        press_counts[button_name] += 1
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"🎯 [{timestamp}] {button_name} pressed! (count: {press_counts[button_name]})")
                    return handler

                # Try with pull_up=True first
                button_objects[name] = Button(pin, pull_up=True, bounce_time=0.3)
                button_objects[name].when_pressed = make_handler(name)
                print(f"✅ {name} (GPIO {pin}) initialized with pull_up")

            except Exception as e:
                print(f"❌ Failed to initialize {name} (GPIO {pin}): {e}")
                try:
                    # Try without pull_up
                    button_objects[name] = Button(pin, pull_up=False, bounce_time=0.3)
                    button_objects[name].when_pressed = make_handler(name)
                    print(f"⚠️ {name} (GPIO {pin}) initialized without pull_up")
                except Exception as e2:
                    print(f"❌ {name} (GPIO {pin}) completely failed: {e2}")

    # Test encoder
    try:
        encoder = RotaryEncoder(pins['volume_encoder_clk'], pins['volume_encoder_dt'], bounce_time=0.01)

        def on_encoder_cw():
            timestamp = time.strftime("%H:%M:%S")
            print(f"🔊 [{timestamp}] Volume encoder: CLOCKWISE")

        def on_encoder_ccw():
            timestamp = time.strftime("%H:%M:%S")
            print(f"🔉 [{timestamp}] Volume encoder: COUNTER-CLOCKWISE")

        encoder.when_rotated_clockwise = on_encoder_cw
        encoder.when_rotated_counter_clockwise = on_encoder_ccw

        print(f"✅ Volume encoder (GPIO {pins['volume_encoder_clk']}/{pins['volume_encoder_dt']}) initialized")

    except Exception as e:
        print(f"❌ Failed to initialize encoder: {e}")
        encoder = None

    print("\n" + "=" * 60)
    print("🎯 DETECTION TEST ACTIVE")
    print("=" * 60)
    print("Press your physical buttons and rotate the encoder...")
    print("You should see detection messages appear below.")
    print("Press Ctrl+C to stop the test.")
    print("=" * 60)

    try:
        # Test for 60 seconds or until interrupted
        start_time = time.time()
        while time.time() - start_time < 60:
            time.sleep(0.1)

            # Show status every 10 seconds
            elapsed = int(time.time() - start_time)
            if elapsed > 0 and elapsed % 10 == 0:
                print(f"\n📊 [{elapsed}s] Still listening for button presses...")
                total_presses = sum(press_counts.values())
                if total_presses > 0:
                    print(f"   Total button presses detected: {total_presses}")
                else:
                    print("   No button presses detected yet.")
                print("   (Try pressing buttons harder or check wiring)")
                time.sleep(1)  # Avoid repeated messages

    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")

    # Final summary
    print("\n" + "=" * 60)
    print("📊 DETECTION TEST SUMMARY")
    print("-" * 40)

    total_presses = sum(press_counts.values())
    if total_presses > 0:
        print(f"✅ Total button presses detected: {total_presses}")
        for name, count in press_counts.items():
            if count > 0:
                print(f"   {name}: {count} presses")
        print("\n🎉 Button detection is working!")
    else:
        print("❌ No button presses detected")
        print("\n🔧 Possible issues:")
        print("   1. Buttons not physically connected")
        print("   2. Wrong wiring (check pin connections)")
        print("   3. Buttons need different pull-up configuration")
        print("   4. Electrical issues (loose connections, bad buttons)")
        print("   5. Need to run with sudo for GPIO access")

    # Cleanup
    for name, button in button_objects.items():
        try:
            button.close()
        except:
            pass

    if encoder:
        try:
            encoder.close()
        except:
            pass

    cleanup_gpio()
    return total_presses > 0

if __name__ == "__main__":
    try:
        success = test_button_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        cleanup_gpio()
        sys.exit(1)