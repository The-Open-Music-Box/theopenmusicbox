#!/usr/bin/env python3
"""
Debug script pour tester l'audio directement sur Raspberry Pi.
Ce script teste différentes configurations ALSA/pygame pour identifier le problème.
"""

import os
import sys
import subprocess
import time

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def run_command(cmd, description):
    """Execute a shell command and return result."""
    print(f"\n🔧 {description}")
    print(f"   Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        print(f"   Exit code: {result.returncode}")
        if result.stdout.strip():
            print(f"   STDOUT: {result.stdout.strip()}")
        if result.stderr.strip():
            print(f"   STDERR: {result.stderr.strip()}")
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"   ❌ TIMEOUT after 10s")
        return False, "", "TIMEOUT"
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, "", str(e)

def test_pygame_device(device_name, description):
    """Test pygame with a specific device."""
    print(f"\n{'='*60}")
    print(f"🎵 TESTING: {description}")
    print(f"   Device: {device_name}")
    print(f"{'='*60}")

    try:
        import pygame

        # Clean slate
        if pygame.mixer.get_init():
            pygame.mixer.quit()

        # Set SDL environment
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        os.environ['SDL_AUDIODEV'] = device_name

        print(f"   SDL_AUDIODRIVER = {os.environ.get('SDL_AUDIODRIVER')}")
        print(f"   SDL_AUDIODEV = {os.environ.get('SDL_AUDIODEV')}")

        # Initialize pygame
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=8192)
        success = pygame.mixer.init()

        if pygame.mixer.get_init():
            init_info = pygame.mixer.get_init()
            print(f"   ✅ pygame.mixer initialized: {init_info}")

            # Try to load a simple sound (beep)
            try:
                # Generate a simple beep sound file
                import wave
                import math
                import struct

                # Create a 1-second 440Hz beep
                sample_rate = 44100
                duration = 1.0
                frequency = 440

                frames = int(duration * sample_rate)
                wav_file = "/tmp/test_beep.wav"

                with wave.open(wav_file, 'w') as wf:
                    wf.setnchannels(1)  # mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)

                    for i in range(frames):
                        value = int(32767 * math.sin(frequency * 2 * math.pi * i / sample_rate))
                        wf.writeframes(struct.pack('<h', value))

                print(f"   📁 Created test beep: {wav_file}")

                # Try to load and play
                sound = pygame.mixer.Sound(wav_file)
                print(f"   📢 Sound loaded successfully")

                channel = sound.play()
                print(f"   ▶️  Playing sound...")

                # Wait for playback
                start_time = time.time()
                while channel.get_busy() and (time.time() - start_time) < 3:
                    time.sleep(0.1)

                if channel.get_busy():
                    print(f"   ⚠️  Sound still playing after 3s")
                else:
                    print(f"   ✅ Sound playback completed")

                # Clean up
                os.unlink(wav_file)

            except Exception as e:
                print(f"   ❌ Failed to play test sound: {e}")

            pygame.mixer.quit()
            return True

        else:
            print(f"   ❌ pygame.mixer failed to initialize")
            return False

    except Exception as e:
        print(f"   ❌ Exception during pygame test: {e}")
        return False

def main():
    print("🚀 DEBUG AUDIO - RASPBERRY PI REAL HARDWARE")
    print("=" * 60)

    # 1. System info
    print("\n📋 SYSTEM INFORMATION")
    run_command("uname -a", "System info")
    run_command("lsb_release -a", "OS version")

    # 2. Audio hardware detection
    print("\n🔊 AUDIO HARDWARE DETECTION")
    run_command("aplay -l", "List audio devices")
    run_command("cat /proc/asound/cards", "ALSA cards")

    # 3. Check ALSA configuration
    print("\n⚙️ ALSA CONFIGURATION")
    success, stdout, stderr = run_command("cat /etc/asound.conf", "ALSA config")

    asound_exists = os.path.exists('/etc/asound.conf')
    print(f"   /etc/asound.conf exists: {asound_exists}")

    # 4. Test ALSA devices directly
    print("\n🎵 ALSA DIRECT TESTS")

    # Find a test audio file or use speaker-test
    run_command("timeout 3s speaker-test -t sine -f 1000 -l 1 -D default", "Test default device with speaker-test")

    if os.path.exists('/usr/share/sounds/alsa/Front_Left.wav'):
        test_file = '/usr/share/sounds/alsa/Front_Left.wav'
        run_command(f"timeout 3s aplay -D default {test_file}", "Test default with aplay")
        run_command(f"timeout 3s aplay -D hw:wm8960soundcard,0 {test_file}", "Test hw direct with aplay")
        run_command(f"timeout 3s aplay -D plughw:wm8960soundcard,0 {test_file}", "Test plughw with aplay")
        if asound_exists:
            run_command(f"timeout 3s aplay -D dmixed {test_file}", "Test dmixed with aplay")
    else:
        print("   ⚠️  No test audio file found in /usr/share/sounds/alsa/")

    # 5. Test pygame with different devices
    print("\n🐍 PYGAME TESTS")

    # Test different device configurations
    devices_to_test = [
        ('default', 'Default ALSA device (should use dmix if configured)'),
        ('hw:wm8960soundcard,0', 'Direct hardware access'),
        ('plughw:wm8960soundcard,0', 'Hardware with plugin layer'),
    ]

    if asound_exists:
        devices_to_test.append(('dmixed', 'Direct dmix device'))

    results = {}
    for device, description in devices_to_test:
        results[device] = test_pygame_device(device, description)

    # 6. Summary
    print("\n📊 SUMMARY")
    print("=" * 60)
    print(f"ALSA Configuration: {'dmix configured' if asound_exists else 'direct hardware'}")
    print("\nPygame Results:")
    for device, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {device:<25} {status}")

    # 7. Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 60)

    working_devices = [device for device, success in results.items() if success]
    if working_devices:
        print(f"✅ Working devices found: {', '.join(working_devices)}")
        print(f"📝 Recommendation: Use device '{working_devices[0]}' in WM8960AudioBackend")
    else:
        print("❌ No pygame devices working!")
        print("📝 Recommendations:")
        print("   1. Check ALSA configuration")
        print("   2. Verify WM8960 hardware setup")
        print("   3. Test with pulseaudio if available")
        print("   4. Check pygame/SDL version compatibility")

if __name__ == "__main__":
    main()