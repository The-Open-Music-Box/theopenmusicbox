#!/usr/bin/env python3
"""Test script to verify WM8960 audio device detection."""

import subprocess
import os


def detect_wm8960_device():
    """Detect WM8960 audio device automatically."""
    print("Testing WM8960 device detection...")

    try:
        # Try to get list of audio devices
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
    except FileNotFoundError:
        print("aplay not found - not on Raspberry Pi")
        return "plughw:1,0"

    if result.returncode == 0:
        print("\n=== Audio devices found ===")
        print(result.stdout)

        output = result.stdout
        # Look for WM8960 card
        for line in output.split("\n"):
            if "wm8960" in line.lower():
                # Extract card number for hw:X,0 format
                if "card" in line.lower():
                    # Parse "card X: cardname" to get card number
                    parts = line.split("card")
                    if len(parts) >= 2:
                        card_part = parts[1].split(":")[0].strip()
                        if card_part.isdigit():
                            # Use plughw for better compatibility
                            device = f"plughw:{card_part},0"
                            print(f"\n✅ WM8960 detected at: {device}")
                            return device

        # Fallback: look for any card with wm8960soundcard
        for line in output.split("\n"):
            if "wm8960soundcard" in line.lower():
                if "card" in line:
                    card_num = line.split("card")[1].split(":")[0].strip()
                    if card_num.isdigit():
                        device = f"plughw:{card_num},0"
                        print(f"\n✅ WM8960 detected (fallback) at: {device}")
                        return device

    print("\n❌ WM8960 not detected, using default")
    return "plughw:0,0"


def test_pygame_init(device):
    """Test pygame initialization with the detected device."""
    print(f"\n=== Testing pygame with device: {device} ===")

    try:
        import pygame

        # Configure SDL
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        os.environ['SDL_AUDIODEV'] = device

        print(f"SDL_AUDIODRIVER: {os.environ.get('SDL_AUDIODRIVER')}")
        print(f"SDL_AUDIODEV: {os.environ.get('SDL_AUDIODEV')}")

        # Initialize pygame mixer
        if pygame.mixer.get_init():
            pygame.mixer.quit()

        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
        pygame.mixer.init()

        if pygame.mixer.get_init():
            init_info = pygame.mixer.get_init()
            print(f"✅ pygame initialized successfully: {init_info}")
            pygame.mixer.quit()
            return True
        else:
            print("❌ pygame mixer failed to initialize")
            return False

    except ImportError:
        print("❌ pygame not installed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("WM8960 Audio Detection Test")
    print("=" * 40)

    # Detect device
    device = detect_wm8960_device()

    # Test pygame
    success = test_pygame_init(device)

    print("\n" + "=" * 40)
    if success:
        print("✅ Audio system should work correctly")
    else:
        print("❌ Audio system may have issues")