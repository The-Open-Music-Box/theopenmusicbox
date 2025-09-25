#!/usr/bin/env python3
"""Debug pygame WM8960 - Force tous les tests pour comprendre le problème."""

import os
import sys
import time
import subprocess

def test_pygame_step_by_step():
    """Test pygame étape par étape avec debug maximum."""
    print("🔍 DEBUG PYGAME WM8960 - ÉTAPE PAR ÉTAPE")
    print("=" * 60)

    # Étape 1: Vérifications préliminaires
    print("\n1️⃣ VÉRIFICATIONS SYSTÈME")
    print("-" * 30)

    # Check mixer status AVANT pygame
    print("MIXER STATUS AVANT pygame:")
    subprocess.run(["amixer", "sget", "Speaker Playback ZC"], capture_output=False)
    subprocess.run(["amixer", "sget", "Headphone Playback ZC"], capture_output=False)

    # Étape 2: Test pygame basique
    print("\n2️⃣ TEST PYGAME BASIQUE")
    print("-" * 30)

    try:
        import pygame
        print(f"✅ pygame version: {pygame.version.ver}")
        print(f"✅ SDL version: {pygame.version.SDL}")
    except ImportError as e:
        print(f"❌ pygame import failed: {e}")
        return False

    # Étape 3: Configuration SDL
    print("\n3️⃣ CONFIGURATION SDL")
    print("-" * 30)

    os.environ['SDL_AUDIODRIVER'] = 'alsa'
    os.environ['SDL_AUDIODEV'] = 'plughw:wm8960soundcard,0'

    print(f"SDL_AUDIODRIVER: {os.environ['SDL_AUDIODRIVER']}")
    print(f"SDL_AUDIODEV: {os.environ['SDL_AUDIODEV']}")

    # Étape 4: Clean state
    print("\n4️⃣ NETTOYAGE ÉTAT PYGAME")
    print("-" * 30)

    try:
        if pygame.mixer.get_init():
            print("🧹 Nettoyage état pygame existant...")
            pygame.mixer.quit()
            time.sleep(0.1)
        else:
            print("✅ Pas d'état pygame à nettoyer")
    except:
        print("✅ Pas d'état pygame existant")

    # Étape 5: Init pygame avec debug
    print("\n5️⃣ INITIALISATION PYGAME")
    print("-" * 30)

    print("🎛️ pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)")
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)

    print("🎛️ pygame.mixer.init()")
    pygame.mixer.init()

    init_result = pygame.mixer.get_init()
    if init_result:
        print(f"✅ pygame init SUCCESS: {init_result}")
        freq, format, channels = init_result
        print(f"   - Frequency: {freq}Hz")
        print(f"   - Format: {format}")
        print(f"   - Channels: {channels}")
    else:
        print("❌ pygame init FAILED")
        return False

    # Étape 6: Test avec fichier simple
    print("\n6️⃣ TEST LECTURE FICHIER")
    print("-" * 30)

    test_file = "/usr/share/sounds/alsa/Front_Center.wav"
    if not os.path.exists(test_file):
        print(f"❌ Fichier test non trouvé: {test_file}")
        return False

    print(f"📁 Fichier test: {test_file}")

    try:
        print("🎵 pygame.mixer.music.load()")
        pygame.mixer.music.load(test_file)
        print("✅ Load réussi")

        print("🎵 pygame.mixer.music.play()")
        pygame.mixer.music.play()
        print("✅ Play appelé")

        # Check status immédiatement
        busy_status = pygame.mixer.music.get_busy()
        print(f"🎵 pygame.mixer.music.get_busy(): {busy_status}")

        if not busy_status:
            print("❌ WARNING: get_busy() = False immédiatement après play()")
            print("   Cela peut indiquer un problème SDL/ALSA")

        # Wait and monitor
        print("⏳ Attente 5 secondes...")
        for i in range(5):
            time.sleep(1)
            busy = pygame.mixer.music.get_busy()
            print(f"   Seconde {i+1}: busy={busy}")
            if not busy:
                print("   ❌ Lecture s'est arrêtée prématurément")
                break

        print("🛑 pygame.mixer.music.stop()")
        pygame.mixer.music.stop()

    except Exception as e:
        print(f"❌ Erreur pendant la lecture: {e}")
        return False

    # Étape 7: Test volume
    print("\n7️⃣ TEST VOLUME")
    print("-" * 30)

    try:
        # Test différents volumes
        for vol in [0.1, 0.5, 1.0]:
            print(f"🔊 Test volume {vol}")
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.load(test_file)
            pygame.mixer.music.play()
            time.sleep(1)
            pygame.mixer.music.stop()
    except Exception as e:
        print(f"❌ Erreur test volume: {e}")

    # Étape 8: Cleanup
    print("\n8️⃣ NETTOYAGE FINAL")
    print("-" * 30)

    pygame.mixer.quit()
    print("✅ pygame.mixer.quit() appelé")

    # Check si les variables SDL interfèrent après
    if 'SDL_AUDIODRIVER' in os.environ:
        del os.environ['SDL_AUDIODRIVER']
    if 'SDL_AUDIODEV' in os.environ:
        del os.environ['SDL_AUDIODEV']
    print("✅ Variables SDL nettoyées")

    print("\n" + "=" * 60)
    print("🏁 TEST TERMINÉ")
    print("=" * 60)

    return True

if __name__ == "__main__":
    print("🧪 SUPER DEBUG PYGAME + WM8960")
    print("Arrêtez l'application AVANT de lancer ce script!")
    input("Appuyez sur Entrée pour continuer...")

    success = test_pygame_step_by_step()

    print(f"\n📊 RÉSULTAT: {'SUCCESS' if success else 'FAILED'}")

    print("\n💡 SI VOUS N'ENTENDEZ PAS DE SON:")
    print("   1. pygame s'initialise mais n'envoie pas vraiment l'audio")
    print("   2. Le problème est dans SDL/ALSA/pygame sur Raspberry Pi")
    print("   3. Il faut investiguer la configuration SDL plus profondément")

    sys.exit(0 if success else 1)