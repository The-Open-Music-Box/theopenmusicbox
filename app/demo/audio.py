# app/demo/audio.py

import time
import sys

# We use pygame for audio playback and mutagen to get the MP3 duration
try:
    import pygame
except ImportError:
    print("Please install pygame (pip install pygame)")
    sys.exit(1)

try:
    from mutagen.mp3 import MP3
except ImportError:
    print("Please install mutagen (pip install mutagen)")
    sys.exit(1)

# MP3 file name
audio_file = "test.mp3"

# Get the MP3 file duration
try:
    audio_info = MP3(audio_file)
    duration = audio_info.info.length
except Exception as e:
    print("Error reading MP3 file information:", e)
    sys.exit(1)

# Initialize pygame mixer module
pygame.mixer.init()
try:
    pygame.mixer.music.load(audio_file)
except Exception as e:
    print("Error loading audio file:", e)
    sys.exit(1)

print("Playing '{}' (duration: {:.1f} seconds)".format(audio_file, duration))
pygame.mixer.music.play()

start_time = time.time()

# Function to display a progress bar
def display_progress(elapsed, total, bar_length=50):
    progress = elapsed / total
    if progress > 1:
        progress = 1
    filled_length = int(bar_length * progress)
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    return "[{}] {:>6.2f}%".format(bar, progress * 100)

# Progress update loop
while pygame.mixer.music.get_busy():
    elapsed = time.time() - start_time
    progress_bar = display_progress(elapsed, duration)
    sys.stdout.write("\r" + progress_bar)
    sys.stdout.flush()
    time.sleep(0.1)

print("\nPlayback completed.")
