# app/demo/audio.py

import time
import sys

# On utilise pygame pour la lecture audio et mutagen pour récupérer la durée du MP3
try:
    import pygame
except ImportError:
    print("Veuillez installer pygame (pip install pygame)")
    sys.exit(1)

try:
    from mutagen.mp3 import MP3
except ImportError:
    print("Veuillez installer mutagen (pip install mutagen)")
    sys.exit(1)

# Nom du fichier MP3
audio_file = "test.mp3"

# Récupération de la durée du fichier MP3
try:
    audio_info = MP3(audio_file)
    duration = audio_info.info.length
except Exception as e:
    print("Erreur lors de la lecture des informations du fichier MP3 :", e)
    sys.exit(1)

# Initialisation du module mixer de pygame
pygame.mixer.init()
try:
    pygame.mixer.music.load(audio_file)
except Exception as e:
    print("Erreur lors du chargement du fichier audio :", e)
    sys.exit(1)

print("Lecture de '{}' (durée : {:.1f} secondes)".format(audio_file, duration))
pygame.mixer.music.play()

start_time = time.time()

# Fonction pour afficher une barre de progression
def afficher_progression(elapsed, total, bar_length=50):
    progress = elapsed / total
    if progress > 1:
        progress = 1
    filled_length = int(bar_length * progress)
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    return "[{}] {:>6.2f}%".format(bar, progress * 100)

# Boucle de mise à jour de la progression
while pygame.mixer.music.get_busy():
    elapsed = time.time() - start_time
    progress_bar = afficher_progression(elapsed, duration)
    sys.stdout.write("\r" + progress_bar)
    sys.stdout.flush()
    time.sleep(0.1)

print("\nLecture terminée.")
