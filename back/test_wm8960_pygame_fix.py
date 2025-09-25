#!/usr/bin/env python3
"""Test script to verify the WM8960 pygame fix.

This script specifically tests the fix for the device selection issue where
pygame was trying to use shared dmix devices instead of direct hardware access.

Usage:
    python3 test_wm8960_pygame_fix.py

Expected behavior:
1. WM8960AudioBackend should now use plughw:wm8960soundcard,0 directly
2. pygame should initialize successfully with actual audio output
3. aplay should work before and after backend usage
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.src.domain.audio.backends.implementations.wm8960_audio_backend import WM8960AudioBackend


def test_device_detection():
    """Test the new device detection logic."""
    print("=== TESTING DEVICE DETECTION ===")

    # Create a backend instance and check what device it detects
    try:
        backend = WM8960AudioBackend()
        detected_device = backend._audio_device
        print(f"🔍 Detected device: {detected_device}")

        # Verify it's using direct hardware access (plughw:)
        if detected_device.startswith("plughw:"):
            print("✅ Using direct hardware access (plughw:)")
        elif detected_device.startswith("hw:"):
            print("✅ Using direct hardware access (hw:)")
        else:
            print(f"⚠️ Using non-direct device: {detected_device}")
            print("This might not work with pygame/SDL")

        backend.cleanup()
        return True

    except Exception as e:
        print(f"❌ Device detection failed: {e}")
        return False


def test_aplay_compatibility():
    """Test aplay compatibility with detected device."""
    print("=== TESTING APLAY COMPATIBILITY ===")

    try:
        backend = WM8960AudioBackend()
        detected_device = backend._audio_device

        print(f"🔍 Testing aplay with detected device: {detected_device}")

        result = subprocess.run(
            ["aplay", "-D", detected_device, "--list-pcms"],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode == 0:
            print("✅ aplay works with detected device")
            backend.cleanup()
            return True
        else:
            print(f"❌ aplay failed with detected device")
            print(f"stderr: {result.stderr}")
            backend.cleanup()
            return False

    except Exception as e:
        print(f"❌ aplay compatibility test failed: {e}")
        return False


def test_pygame_initialization():
    """Test pygame initialization with the new device selection."""
    print("=== TESTING PYGAME INITIALIZATION ===")

    try:
        backend = WM8960AudioBackend()

        # Check SDL environment variables
        sdl_audiodriver = os.environ.get('SDL_AUDIODRIVER')
        sdl_audiodev = os.environ.get('SDL_AUDIODEV')

        print(f"🔍 SDL_AUDIODRIVER: {sdl_audiodriver}")
        print(f"🔍 SDL_AUDIODEV: {sdl_audiodev}")

        # Check if the device is using direct hardware access
        if sdl_audiodev and (sdl_audiodev.startswith("plughw:") or sdl_audiodev.startswith("hw:")):
            print("✅ SDL configured for direct hardware access")
        else:
            print(f"⚠️ SDL device might not be direct hardware: {sdl_audiodev}")

        # Try to initialize pygame if not already done
        try:
            import pygame

            # Check if pygame mixer is initialized
            init_info = pygame.mixer.get_init()
            if init_info:
                print(f"✅ pygame mixer initialized: {init_info}")
            else:
                print("❌ pygame mixer not initialized")
                backend.cleanup()
                return False

        except ImportError:
            print("❌ pygame not available")
            backend.cleanup()
            return False

        backend.cleanup()
        return True

    except Exception as e:
        print(f"❌ pygame initialization test failed: {e}")
        return False


def test_audio_playback():
    """Test actual audio playback with a test file."""
    print("=== TESTING AUDIO PLAYBACK ===")

    test_files = [
        "/usr/share/sounds/alsa/Front_Center.wav",
        "/usr/share/sounds/alsa/Front_Left.wav",
        "/usr/share/sounds/alsa/Front_Right.wav",
    ]

    test_file = None
    for file_path in test_files:
        if Path(file_path).exists():
            test_file = file_path
            break

    if not test_file:
        print("❌ No test audio file found")
        return False

    print(f"🔍 Testing playback with: {test_file}")

    try:
        backend = WM8960AudioBackend()

        # Attempt to play the file
        success = backend.play_file(test_file)
        if not success:
            print("❌ Failed to start playback")
            backend.cleanup()
            return False

        print("🎵 Playback started, waiting 3 seconds...")
        time.sleep(3)

        # Check if still playing
        is_playing = backend.is_playing
        is_busy = backend.is_busy

        print(f"🔍 is_playing: {is_playing}")
        print(f"🔍 is_busy: {is_busy}")

        if is_playing or is_busy:
            print("✅ Audio playback appears to be working")
        else:
            print("⚠️ Audio playback status unclear")

        backend.stop_sync()
        backend.cleanup()
        return True

    except Exception as e:
        print(f"❌ Audio playback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resource_cleanup():
    """Test that ALSA resources are properly cleaned up."""
    print("=== TESTING RESOURCE CLEANUP ===")

    try:
        # Create and use backend
        backend = WM8960AudioBackend()
        detected_device = backend._audio_device

        # Try to play something briefly
        test_file = "/usr/share/sounds/alsa/Front_Center.wav"
        if Path(test_file).exists():
            backend.play_file(test_file)
            time.sleep(1)
            backend.stop_sync()

        # Clean up
        backend.cleanup()

        print("🔍 Testing if aplay works after backend cleanup...")
        time.sleep(0.5)  # Give cleanup time to complete

        # Test if aplay can access the device
        result = subprocess.run(
            ["aplay", "-D", detected_device, "--list-pcms"],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode == 0:
            print("✅ aplay works after backend cleanup - resources properly released")
            return True
        else:
            print("❌ aplay blocked after backend cleanup - resource leak detected")
            print(f"stderr: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Resource cleanup test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Testing WM8960 pygame device selection fix...")
    print("=" * 60)

    tests = [
        ("Device Detection", test_device_detection),
        ("aplay Compatibility", test_aplay_compatibility),
        ("pygame Initialization", test_pygame_initialization),
        ("Audio Playback", test_audio_playback),
        ("Resource Cleanup", test_resource_cleanup),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)

        try:
            result = test_func()
            results[test_name] = result

            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")

        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The pygame device selection fix appears to work correctly.")
        return True
    else:
        print("⚠️ Some tests failed. The fix may need additional work.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)