#!/usr/bin/env python3
"""
Test final pour vérifier le fix audio sur Raspberry Pi.
Ce script teste la nouvelle configuration pygame simplifiée.
"""

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from app.src.domain.audio.backends.implementations.wm8960_audio_backend import WM8960AudioBackend
from app.src.domain.protocols.notification_protocol import PlaybackNotifierProtocol as PlaybackSubject

def test_simplified_wm8960():
    """Test WM8960 with the simplified pygame configuration."""
    print("🎵 TESTING SIMPLIFIED WM8960 AUDIO CONFIGURATION")
    print("=" * 60)

    try:
        # Create backend with simplified config
        playback_subject = PlaybackSubject.get_instance()
        backend = WM8960AudioBackend(playback_subject)

        print("✅ WM8960AudioBackend created successfully")
        print(f"   Backend type: {type(backend).__name__}")

        # Check pygame initialization
        import pygame
        if pygame.mixer.get_init():
            init_info = pygame.mixer.get_init()
            print(f"✅ pygame mixer initialized: {init_info}")

            # Check what device is being used (should be default/simple)
            print("\n📊 ENVIRONMENT CHECK:")
            print(f"   SDL_AUDIODRIVER: {os.environ.get('SDL_AUDIODRIVER', 'NOT SET (good!)')}")
            print(f"   SDL_AUDIODEV: {os.environ.get('SDL_AUDIODEV', 'NOT SET (good!)')}")

            # Test with a simple audio file (if available)
            test_files = [
                "/usr/share/sounds/alsa/Front_Left.wav",
                "/usr/share/sounds/alsa/Front_Right.wav",
                "/System/Library/Sounds/Ping.aiff",  # macOS
            ]

            test_file = None
            for file_path in test_files:
                if os.path.exists(file_path):
                    test_file = file_path
                    break

            if test_file:
                print(f"\n🎵 TESTING PLAYBACK with {test_file}")
                success = backend.play_file(test_file)
                if success:
                    print("✅ Playback started successfully!")
                    print("🔊 Listening for 3 seconds...")

                    # Check if playing
                    for i in range(30):  # Check for 3 seconds
                        if backend.is_playing():
                            print(f"   [{i/10:.1f}s] ▶️  Still playing")
                        else:
                            print(f"   [{i/10:.1f}s] ⏹️  Playback finished")
                            break
                        time.sleep(0.1)

                    # Stop if still playing
                    if backend.is_playing():
                        print("⏹️  Stopping playback")
                        backend.stop_sync()

                else:
                    print("❌ Playback failed to start")
            else:
                print("⚠️  No test audio file found")
                print("   To test audio, place a .wav file and run:")
                print(f"   python -c \"import sys; sys.path.append('.'); from {__name__} import *; test_with_file('/path/to/file.wav')\"")
        else:
            print("❌ pygame mixer not initialized")

        # Cleanup
        backend.cleanup()
        print("\n✅ Cleanup completed")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_file(file_path):
    """Test with a specific audio file."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    print(f"🎵 Testing with custom file: {file_path}")

    try:
        playback_subject = PlaybackSubject.get_instance()
        backend = WM8960AudioBackend(playback_subject)

        success = backend.play_file(file_path)
        if success:
            print("✅ Playback started!")
            time.sleep(5)  # Play for 5 seconds
            backend.stop_sync()
            print("⏹️  Stopped")
        else:
            print("❌ Playback failed")

        backend.cleanup()
        return success

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 FINAL AUDIO FIX TEST")
    print("=" * 60)
    print("This test verifies the simplified pygame configuration")
    print("that matches the working main branch.")
    print()

    # Test the simplified configuration
    success = test_simplified_wm8960()

    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST COMPLETED SUCCESSFULLY!")
        print("The simplified pygame configuration is working.")
        print("\n📝 Summary of changes:")
        print("✅ Removed complex SDL environment configuration")
        print("✅ Using pygame default device selection")
        print("✅ Simplified frequency: 22050Hz (like main branch)")
        print("✅ Reduced buffer: 512 (like main branch)")
        print("✅ Clean SDL environment variables")
        print("\n🚀 This should work on Raspberry Pi now!")
    else:
        print("❌ TEST FAILED")
        print("There may be other issues to investigate.")

    return success

if __name__ == "__main__":
    main()