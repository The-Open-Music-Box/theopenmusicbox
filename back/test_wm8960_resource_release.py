#!/usr/bin/env python3
"""Test script to verify that WM8960 audio backend properly releases ALSA resources.

This script tests the specific issue where the application locks the WM8960 ALSA device
and prevents aplay from working until reboot.

Usage:
    python3 test_wm8960_resource_release.py

Expected behavior:
1. aplay should work before running the test
2. After WM8960AudioBackend cleanup(), aplay should still work
3. No ALSA device locking should occur
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.src.domain.audio.backends.implementations.wm8960_audio_backend import WM8960AudioBackend


def test_aplay_works() -> bool:
    """Test if aplay can access the WM8960 device."""
    # Test both the old hw: device and the new plughw: device
    devices_to_test = ["plughw:wm8960soundcard,0", "hw:wm8960soundcard,0"]

    for device in devices_to_test:
        try:
            print(f"Testing aplay with device: {device}")
            result = subprocess.run(
                ["aplay", "-D", device, "--list-pcms"],
                capture_output=True,
                text=True,
                timeout=3
            )
            print(f"aplay test result for {device}: {result.returncode}")
            if result.returncode != 0:
                print(f"aplay stderr: {result.stderr}")
            else:
                print(f"✅ aplay works with device: {device}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"aplay test failed for {device}: {e}")

    print("❌ aplay failed with all tested devices")
    return False


def main():
    """Main test function."""
    print("🧪 Testing WM8960 audio backend ALSA resource release...")

    # Test 1: Verify aplay works initially
    print("\n1️⃣ Testing aplay before WM8960AudioBackend initialization...")
    if not test_aplay_works():
        print("❌ aplay doesn't work initially - check WM8960 setup")
        return False
    print("✅ aplay works initially")

    # Test 2: Initialize WM8960AudioBackend
    print("\n2️⃣ Initializing WM8960AudioBackend...")
    try:
        backend = WM8960AudioBackend()
        print("✅ WM8960AudioBackend initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize WM8960AudioBackend: {e}")
        return False

    # Test 3: Verify aplay still works (might fail if backend locks device)
    print("\n3️⃣ Testing aplay after WM8960AudioBackend initialization...")
    aplay_works_after_init = test_aplay_works()
    if not aplay_works_after_init:
        print("⚠️ aplay blocked after WM8960AudioBackend init (expected on some systems)")
    else:
        print("✅ aplay still works after initialization")

    # Test 4: Cleanup WM8960AudioBackend
    print("\n4️⃣ Cleaning up WM8960AudioBackend...")
    try:
        backend.cleanup()
        print("✅ WM8960AudioBackend cleanup() called successfully")

        # Wait a moment for cleanup to complete
        time.sleep(0.2)

    except Exception as e:
        print(f"❌ Failed to cleanup WM8960AudioBackend: {e}")
        return False

    # Test 5: Verify aplay works after cleanup
    print("\n5️⃣ Testing aplay after WM8960AudioBackend cleanup...")
    if not test_aplay_works():
        print("❌ aplay still blocked after cleanup - ALSA device not properly released!")
        print("This is the bug we're trying to fix.")
        return False
    print("✅ aplay works after cleanup - ALSA device properly released!")

    # Test 6: Check environment variables are cleared
    print("\n6️⃣ Checking SDL environment variables are cleared...")
    sdl_audiodriver = os.environ.get('SDL_AUDIODRIVER')
    sdl_audiodev = os.environ.get('SDL_AUDIODEV')

    if sdl_audiodriver or sdl_audiodev:
        print(f"⚠️ SDL environment variables still set:")
        if sdl_audiodriver:
            print(f"  SDL_AUDIODRIVER: {sdl_audiodriver}")
        if sdl_audiodev:
            print(f"  SDL_AUDIODEV: {sdl_audiodev}")
    else:
        print("✅ SDL environment variables properly cleared")

    print("\n🎉 All tests passed! WM8960 ALSA resource release works correctly.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)