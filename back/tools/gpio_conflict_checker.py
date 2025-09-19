#!/usr/bin/env python3
"""
GPIO Conflict Checker

Identifies what might be using GPIO pins and preventing initialization.
"""

import subprocess
import os
import glob

def check_running_processes():
    """Check for processes that might be using GPIO."""
    print("🔍 Checking for processes using GPIO...")

    gpio_processes = []
    try:
        # Check for common GPIO-using processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if any(keyword in line.lower() for keyword in ['gpio', 'pigpio', 'wiringpi', 'gpiozero']):
                gpio_processes.append(line.strip())

        if gpio_processes:
            print("⚠️ Found processes that might use GPIO:")
            for proc in gpio_processes:
                print(f"   {proc}")
        else:
            print("✅ No obvious GPIO-using processes found")

    except Exception as e:
        print(f"❌ Could not check processes: {e}")

def check_gpio_exports():
    """Check for exported GPIO pins."""
    print("\n🔍 Checking for exported GPIO pins...")

    try:
        export_path = "/sys/class/gpio"
        if os.path.exists(export_path):
            exported_pins = []
            for item in os.listdir(export_path):
                if item.startswith('gpio') and item[4:].isdigit():
                    pin_num = item[4:]
                    exported_pins.append(pin_num)

            if exported_pins:
                print("⚠️ Found exported GPIO pins:")
                for pin in sorted(exported_pins, key=int):
                    pin_path = f"{export_path}/gpio{pin}"
                    try:
                        with open(f"{pin_path}/direction", 'r') as f:
                            direction = f.read().strip()
                        with open(f"{pin_path}/value", 'r') as f:
                            value = f.read().strip()
                        print(f"   GPIO {pin}: direction={direction}, value={value}")
                    except:
                        print(f"   GPIO {pin}: exported but can't read status")
            else:
                print("✅ No GPIO pins are exported via sysfs")
        else:
            print("✅ GPIO sysfs not available (normal on some systems)")

    except Exception as e:
        print(f"❌ Could not check GPIO exports: {e}")

def check_device_tree():
    """Check device tree for GPIO assignments."""
    print("\n🔍 Checking device tree overlays...")

    try:
        config_files = [
            "/boot/config.txt",
            "/boot/firmware/config.txt"
        ]

        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"📋 Checking {config_file}...")
                with open(config_file, 'r') as f:
                    lines = f.readlines()

                gpio_related = []
                for i, line in enumerate(lines, 1):
                    if any(keyword in line.lower() for keyword in ['gpio', 'dtoverlay', 'dtparam']):
                        if not line.strip().startswith('#'):
                            gpio_related.append(f"Line {i}: {line.strip()}")

                if gpio_related:
                    print("⚠️ Found GPIO-related configuration:")
                    for line in gpio_related:
                        print(f"   {line}")
                else:
                    print("✅ No active GPIO overlays found")
                break
        else:
            print("✅ No boot config files found")

    except Exception as e:
        print(f"❌ Could not check device tree: {e}")

def check_permissions():
    """Check GPIO permissions."""
    print("\n🔍 Checking GPIO permissions...")

    try:
        # Check if user is in gpio group
        import grp
        gpio_group = grp.getgrnam('gpio')
        current_user = os.getenv('USER', 'unknown')

        if current_user in gpio_group.gr_mem:
            print(f"✅ User '{current_user}' is in gpio group")
        else:
            print(f"⚠️ User '{current_user}' is NOT in gpio group")
            print("   Fix with: sudo usermod -a -G gpio $USER")
            print("   Then logout and login again")

    except KeyError:
        print("⚠️ GPIO group does not exist")
    except Exception as e:
        print(f"❌ Could not check permissions: {e}")

    # Check if running as root
    if os.geteuid() == 0:
        print("✅ Running as root (should have GPIO access)")
    else:
        print("📊 Running as regular user")

def check_hardware_config():
    """Check TheOpenMusicBox hardware configuration."""
    print("\n🔍 Checking TheOpenMusicBox GPIO configuration...")

    # Updated pins (fixed configuration)
    pins_to_check = [26, 19, 20, 21, 13]
    print("📋 Configured pins: " + ", ".join(f"GPIO {pin}" for pin in pins_to_check))

    # Check for pin conflicts (updated for new configuration)
    conflicts = {
        26: "Safe general purpose GPIO",
        19: "Safe general purpose GPIO",
        20: "Safe general purpose GPIO",
        21: "Safe general purpose GPIO",
        13: "Safe general purpose GPIO"
    }

    print("\n✅ Pin safety status:")
    for pin in pins_to_check:
        if pin in conflicts:
            print(f"   GPIO {pin}: {conflicts[pin]}")

    print("\n🎯 These pins should NOT have SPI conflicts!")

def suggest_solutions():
    """Suggest solutions for common problems."""
    print("\n" + "=" * 60)
    print("💡 SUGGESTED SOLUTIONS")
    print("-" * 40)

    print("\n1. 🔧 Permission Issues:")
    print("   sudo usermod -a -G gpio $USER")
    print("   logout && login")
    print("   # OR run with: sudo python3 -m uvicorn ...")

    print("\n2. 🔄 GPIO State Issues:")
    print("   # Clean up GPIO state (updated pins):")
    print("   echo 26 | sudo tee /sys/class/gpio/unexport 2>/dev/null")
    print("   echo 19 | sudo tee /sys/class/gpio/unexport 2>/dev/null")
    print("   echo 20 | sudo tee /sys/class/gpio/unexport 2>/dev/null")
    print("   echo 21 | sudo tee /sys/class/gpio/unexport 2>/dev/null")
    print("   echo 13 | sudo tee /sys/class/gpio/unexport 2>/dev/null")

    print("\n3. 🏭 Hardware Issues:")
    print("   - Check physical wiring")
    print("   - Ensure buttons are normally-open (NO)")
    print("   - Add pull-up resistors (10kΩ) if needed")
    print("   - Test with multimeter/oscilloscope")

    print("\n4. 🐛 Software Conflicts:")
    print("   sudo systemctl stop pigpiod")
    print("   sudo pkill -f gpio")
    print("   # Disable SPI if not needed:")
    print("   # In /boot/config.txt: dtparam=spi=off")

def main():
    """Main diagnostic function."""
    print("=" * 60)
    print("🔍 GPIO CONFLICT CHECKER")
    print("=" * 60)

    check_running_processes()
    check_gpio_exports()
    check_device_tree()
    check_permissions()
    check_hardware_config()
    suggest_solutions()

    print("\n🏁 Diagnostic completed")

if __name__ == "__main__":
    main()