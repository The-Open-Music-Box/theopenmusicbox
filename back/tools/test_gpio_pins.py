#!/usr/bin/env python3
"""
GPIO Pin Tester for TheOpenMusicBox

Tests each GPIO pin individually to identify which ones work.
"""

import sys
import time
import signal

def signal_handler(sig, frame):
    print("\n🛑 Interrupted by user")
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

def test_individual_pin(pin, description):
    """Test a single GPIO pin."""
    print(f"\n🧪 Testing {description} (GPIO {pin})...")

    # Test with RPi.GPIO directly
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Test as input with pull-up
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        initial_state = GPIO.input(pin)
        print(f"   📊 Direct RPi.GPIO test: GPIO {pin} = {initial_state} (with pull-up)")

        GPIO.cleanup(pin)

        # Test as input without pull-up
        GPIO.setup(pin, GPIO.IN)
        no_pullup_state = GPIO.input(pin)
        print(f"   📊 Direct RPi.GPIO test: GPIO {pin} = {no_pullup_state} (no pull-up)")

        GPIO.cleanup(pin)
        print(f"   ✅ GPIO {pin} is accessible via RPi.GPIO")
        return True

    except Exception as e:
        print(f"   ❌ RPi.GPIO test failed: {e}")
        return False

def test_gpiozero_button(pin, description):
    """Test GPIO pin with gpiozero Button."""
    print(f"\n🔘 Testing Button on {description} (GPIO {pin})...")

    try:
        from gpiozero import Button, Device
        from gpiozero.pins.rpigpio import RPiGPIOFactory
        Device.pin_factory = RPiGPIOFactory()

        # Test with pull_up=True
        try:
            btn = Button(pin, pull_up=True, bounce_time=0.1)
            print(f"   ✅ Button with pull_up=True: OK")
            btn.close()
            time.sleep(0.1)
        except Exception as e:
            print(f"   ⚠️ Button with pull_up=True failed: {e}")

        # Test with pull_up=False
        try:
            btn = Button(pin, pull_up=False, bounce_time=0.1)
            print(f"   ✅ Button with pull_up=False: OK")
            btn.close()
            time.sleep(0.1)
        except Exception as e:
            print(f"   ⚠️ Button with pull_up=False failed: {e}")

        return True

    except Exception as e:
        print(f"   ❌ gpiozero Button test failed: {e}")
        return False

def test_gpiozero_encoder(clk_pin, dt_pin):
    """Test rotary encoder pins."""
    print(f"\n🔄 Testing RotaryEncoder (CLK: GPIO {clk_pin}, DT: GPIO {dt_pin})...")

    try:
        from gpiozero import RotaryEncoder, Device
        from gpiozero.pins.rpigpio import RPiGPIOFactory
        Device.pin_factory = RPiGPIOFactory()

        encoder = RotaryEncoder(clk_pin, dt_pin, bounce_time=0.01)
        print(f"   ✅ RotaryEncoder initialized successfully")

        # Test for a short time
        print(f"   📊 Testing encoder for 2 seconds...")
        start_steps = encoder.steps
        time.sleep(2)
        end_steps = encoder.steps

        if start_steps != end_steps:
            print(f"   🎯 Encoder detected movement: {end_steps - start_steps} steps")
        else:
            print(f"   📊 No movement detected (this is normal for testing)")

        encoder.close()
        return True

    except Exception as e:
        print(f"   ❌ RotaryEncoder test failed: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("🔍 GPIO PIN TESTER FOR THEOPENMUSICBOX")
    print("=" * 60)
    print("🎯 Testing the configured GPIO pins for physical controls")
    print()

    # Configuration from hardware_config.py (mise à jour détection réelle)
    gpio_config = {
        'next_button': 16,
        'previous_button': 26,
        'play_pause_button': 23,
        'volume_encoder_clk': 8,
        'volume_encoder_dt': 21
    }

    print("📋 Configured pins:")
    for name, pin in gpio_config.items():
        print(f"   {name}: GPIO {pin}")
    print()

    # Test each pin individually
    working_pins = []

    # Test buttons (pins mis à jour selon détection)
    for name, pin in [('next_button', 16), ('previous_button', 26), ('play_pause_button', 23)]:
        description = name.replace('_', ' ').title()

        if test_individual_pin(pin, description):
            working_pins.append(pin)
            test_gpiozero_button(pin, description)

        time.sleep(0.5)

    # Test encoder pins (pins selon détection réelle)
    test_individual_pin(8, "Volume Encoder CLK")
    test_individual_pin(21, "Volume Encoder DT")
    test_gpiozero_encoder(8, 21)

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("-" * 40)

    if working_pins:
        print("✅ Working GPIO pins:")
        for pin in working_pins:
            print(f"   - GPIO {pin}")
    else:
        print("❌ No GPIO pins could be accessed")
        print("\n🔧 Possible solutions:")
        print("   1. Run with sudo: sudo python3 test_gpio_pins.py")
        print("   2. Add user to gpio group: sudo usermod -a -G gpio $USER")
        print("   3. Install gpio packages: sudo apt-get install python3-rpi.gpio")
        print("   4. Check if pins are used by other processes")

    print("\n💡 If pins are working but buttons don't respond:")
    print("   - Check physical wiring")
    print("   - Verify button connections (normally open/closed)")
    print("   - Try different pull-up/pull-down settings")
    print("   - Check for electrical interference")

    cleanup_gpio()
    print("\n🏁 Test completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        cleanup_gpio()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        cleanup_gpio()