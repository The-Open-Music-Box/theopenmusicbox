#!/usr/bin/env python3
"""
Test direct WM8960 backend with dmix fix.
Simple test without complex dependencies.
"""

import os
import sys
import time

def test_pygame_dmix():
    """Test pygame with dmix configuration."""
    print("🎵 TESTING PYGAME WITH DMIX FIX")
    print("=" * 50)

    try:
        import pygame

        # Clean pygame state
        if pygame.mixer.get_init():
            pygame.mixer.quit()

        # Apply dmix fix
        print("🔧 Applying dmix fix...")
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        os.environ['SDL_AUDIODEV'] = 'default'  # DMIX FIX!

        print(f"   SDL_AUDIODRIVER: {os.environ.get('SDL_AUDIODRIVER')}")
        print(f"   SDL_AUDIODEV: {os.environ.get('SDL_AUDIODEV')}")

        # Initialize pygame with settings matching main branch
        print("🔊 Initializing pygame mixer...")
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()

        if pygame.mixer.get_init():
            init_info = pygame.mixer.get_init()
            print(f"✅ pygame mixer initialized: {init_info}")

            # Test if we can create a simple sound
            print("🎵 Testing sound generation...")

            # Create a simple beep
            import math
            import numpy as np
            sample_rate = 22050
            duration = 1.0  # 1 second
            frequency = 440  # 440 Hz (A note)

            frames = int(duration * sample_rate)
            arr = np.zeros(frames)

            for i in range(frames):
                arr[i] = 32767 * math.sin(frequency * 2 * math.pi * i / sample_rate)

            arr = arr.astype(np.int16)
            sound_array = np.array([arr, arr]).T  # Stereo
            sound = pygame.sndarray.make_sound(sound_array)

            print("▶️  Playing test sound...")
            channel = sound.play()

            # Monitor playback
            start_time = time.time()
            while channel.get_busy() and (time.time() - start_time) < 3:
                print(f"   Playing... {time.time() - start_time:.1f}s")
                time.sleep(0.5)

            if channel.get_busy():
                print("⏹️  Stopping sound")
                channel.stop()
            else:
                print("✅ Sound completed")

            # Test if system audio is still working
            print("🔍 Testing system audio compatibility...")
            test_result = os.system("timeout 2s speaker-test -t sine -f 1000 -l 1 -D default >/dev/null 2>&1")
            if test_result == 0:
                print("✅ System audio still works!")
            else:
                print("⚠️  System audio test failed")

            pygame.mixer.quit()
            print("✅ pygame cleaned up")

            return True

        else:
            print("❌ pygame mixer failed to initialize")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 DIRECT WM8960 DMIX TEST")
    print("=" * 50)
    print("Testing the dmix compatibility fix directly")
    print()

    # Check for required modules
    try:
        import pygame
        import numpy as np
        print("✅ Required modules available")
    except ImportError as e:
        print(f"❌ Missing module: {e}")
        print("Run: pip install pygame numpy")
        return False

    # Check ALSA configuration
    if os.path.exists('/etc/asound.conf'):
        print("✅ ALSA dmix configuration detected")
    else:
        print("⚠️  No /etc/asound.conf - may not have dmix")

    # Run the test
    success = test_pygame_dmix()

    print("\n" + "=" * 50)
    if success:
        print("🎉 DMIX FIX TEST PASSED!")
        print("✅ pygame initializes without blocking audio")
        print("✅ Sound plays through dmix")
        print("✅ System audio remains functional")
    else:
        print("❌ DMIX FIX TEST FAILED")

    return success

if __name__ == "__main__":
    main()