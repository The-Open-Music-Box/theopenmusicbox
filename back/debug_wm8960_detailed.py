#!/usr/bin/env python3
"""Diagnostic détaillé pour WM8960 - problème d'absence de son.

Ce script teste chaque composant individuellement pour identifier pourquoi
pygame s'initialise correctement mais aucun son ne sort.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def run_command(cmd, description, capture=True, timeout=5):
    """Execute une commande et affiche le résultat."""
    print(f"\n🔍 {description}")
    print(f"Commande: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, timeout=timeout)
        else:
            result = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout)

        print(f"Return code: {result.returncode}")
        if capture:
            if result.stdout.strip():
                print(f"STDOUT:\n{result.stdout}")
            if result.stderr.strip():
                print(f"STDERR:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout après {timeout}s")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_alsa_devices():
    """Test la configuration ALSA."""
    print("=" * 60)
    print("🔊 TESTS ALSA")
    print("=" * 60)

    # Liste des devices
    run_command(["aplay", "-l"], "Liste des devices ALSA")

    # Test du device WM8960 spécifiquement
    run_command(["aplay", "-D", "hw:wm8960soundcard", "--list-pcms"], "Test device WM8960")

    # Mixer settings
    run_command(["amixer", "scontents"], "Contrôles mixer ALSA")

    # Test aplay avec fichier test
    run_command(["aplay", "-D", "hw:wm8960soundcard,0", "/usr/share/sounds/alsa/Front_Center.wav"],
               "Test aplay direct sur WM8960")

def test_pygame_basic():
    """Test pygame de base."""
    print("=" * 60)
    print("🐍 TESTS PYGAME BASIC")
    print("=" * 60)

    try:
        import pygame
        print(f"✅ pygame version: {pygame.version.ver}")

        # Test sans configuration SDL spéciale
        print("\n🔍 Test pygame sans configuration SDL...")
        pygame.mixer.quit()  # Nettoie l'état précédent
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
        pygame.mixer.init()

        if pygame.mixer.get_init():
            init_info = pygame.mixer.get_init()
            print(f"✅ pygame mixer init réussi: {init_info}")
        else:
            print("❌ pygame mixer init échoué")
            return False

        pygame.mixer.quit()
        return True
    except Exception as e:
        print(f"❌ Erreur pygame: {e}")
        return False

def test_pygame_wm8960():
    """Test pygame avec configuration WM8960."""
    print("=" * 60)
    print("🎵 TESTS PYGAME + WM8960")
    print("=" * 60)

    try:
        import pygame

        # Configuration SDL pour WM8960
        print("\n🔍 Configuration SDL pour WM8960...")
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        os.environ['SDL_AUDIODEV'] = 'hw:wm8960soundcard,0'
        print(f"SDL_AUDIODRIVER: {os.environ['SDL_AUDIODRIVER']}")
        print(f"SDL_AUDIODEV: {os.environ['SDL_AUDIODEV']}")

        # Clean previous state
        try:
            pygame.mixer.quit()
        except:
            pass

        # Initialize pygame mixer
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
        pygame.mixer.init()

        if pygame.mixer.get_init():
            init_info = pygame.mixer.get_init()
            print(f"✅ pygame mixer WM8960 init réussi: {init_info}")
        else:
            print("❌ pygame mixer WM8960 init échoué")
            return False

        # Test avec un fichier audio simple
        test_file = "/usr/share/sounds/alsa/Front_Center.wav"
        if Path(test_file).exists():
            print(f"\n🔍 Test lecture avec pygame: {test_file}")
            pygame.mixer.music.load(test_file)
            pygame.mixer.music.play()

            print("🎵 Lecture démarrée, attente 3 secondes...")
            time.sleep(3)

            if pygame.mixer.music.get_busy():
                print("🎵 pygame.mixer.music.get_busy() = True")
            else:
                print("🎵 pygame.mixer.music.get_busy() = False")

            pygame.mixer.music.stop()
        else:
            print(f"❌ Fichier test non trouvé: {test_file}")

        pygame.mixer.quit()
        return True

    except Exception as e:
        print(f"❌ Erreur pygame WM8960: {e}")
        return False

def test_wm8960_backend():
    """Test du WM8960AudioBackend."""
    print("=" * 60)
    print("🎛️ TEST WM8960AUDIOBACKEND")
    print("=" * 60)

    try:
        from app.src.domain.audio.backends.implementations.wm8960_audio_backend import WM8960AudioBackend

        print("🔍 Initialisation WM8960AudioBackend...")
        backend = WM8960AudioBackend()
        print("✅ Backend initialisé")

        # Test avec fichier
        test_file = "/usr/share/sounds/alsa/Front_Center.wav"
        if Path(test_file).exists():
            print(f"\n🔍 Test playback: {test_file}")
            success = backend.play_file(test_file)
            print(f"play_file() result: {success}")

            if success:
                print("🎵 Lecture démarrée, attente 3 secondes...")
                time.sleep(3)

                print(f"is_playing: {backend.is_playing}")
                print(f"is_busy: {backend.is_busy}")

                backend.stop()
            else:
                print("❌ Échec du démarrage de la lecture")
        else:
            print(f"❌ Fichier test non trouvé: {test_file}")

        backend.cleanup()
        print("✅ Backend nettoyé")
        return True

    except Exception as e:
        print(f"❌ Erreur WM8960AudioBackend: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_system_audio():
    """Vérifications système audio."""
    print("=" * 60)
    print("🔧 VÉRIFICATIONS SYSTÈME")
    print("=" * 60)

    # Process audio
    run_command(["ps", "aux"], "Processus système (grep audio dans la sortie)", capture=True)

    # Modules kernel
    run_command(["lsmod"], "Modules kernel chargés (grep snd dans la sortie)", capture=True)

    # Device tree overlays
    run_command(["cat", "/boot/firmware/config.txt"], "Configuration device tree", capture=True)

def main():
    """Test principal."""
    print("🧪 DIAGNOSTIC DÉTAILLÉ WM8960 - ABSENCE DE SON")
    print("=" * 80)

    # Tests étape par étape
    test_alsa_devices()
    test_pygame_basic()
    test_pygame_wm8960()
    test_wm8960_backend()
    check_system_audio()

    print("\n" + "=" * 80)
    print("🏁 DIAGNOSTIC TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    main()