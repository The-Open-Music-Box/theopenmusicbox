# app/demo/ledhat.py

import time
import math
from rpi_ws281x import PixelStrip, Color

# Configuration pour la strip LED
LED_COUNT = 36        # Nombre de LEDs dans l'anneau
LED_PIN = 12          # GPIO pin connecté aux LEDs (18 uses PWM!)
LED_FREQ_HZ = 800000  # Fréquence du signal LED en Hz
LED_DMA = 10          # Canal DMA à utiliser pour générer le signal
LED_BRIGHTNESS = 12   # Luminosité (0-255)
LED_INVERT = False    # Inversion du signal (si transistor NPN)
LED_CHANNEL = 0       # '0' pour GPIO 12, 18


def wheel(pos):
    """Génère une couleur à partir d'une position de roue 0-255"""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow_cycle(strip, wait_ms=20, duration=5):
    """Arc-en-ciel qui se déplace uniformément sur tous les pixels"""
    start_time = time.time()
    j = 0
    while time.time() - start_time < duration:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)
        j = (j + 1) % 256


def theater_chase(strip, color, wait_ms=50, duration=5):
    """Effet théâtral de poursuite"""
    start_time = time.time()
    while time.time() - start_time < duration:
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                if i + q < strip.numPixels():
                    strip.setPixelColor(i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                if i + q < strip.numPixels():
                    strip.setPixelColor(i + q, 0)


def breathing_effect(strip, color, wait_ms=5, duration=5):
    """Effet de respiration - la luminosité monte et descend"""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF

    start_time = time.time()
    while time.time() - start_time < duration:
        # Respiration complète
        for k in range(256):
            brightness = math.sin(math.pi * k / 255) * math.sin(math.pi * k / 255)
            r_adj = int(r * brightness)
            g_adj = int(g * brightness)
            b_adj = int(b * brightness)
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(r_adj, g_adj, b_adj))
            strip.show()
            time.sleep(wait_ms / 1000.0)

            # Vérifier si on dépasse la durée
            if time.time() - start_time >= duration:
                break


def circular_sweep(strip, color, wait_ms=5, duration=5):
    """Balayage circulaire avec traînée"""
    fade_factor = 0.9  # Facteur de diminution pour la traînée

    start_time = time.time()
    # Initialisation des couleurs
    pixel_values = [0] * strip.numPixels()

    steps = 0
    while time.time() - start_time < duration:
        # Appliquer le facteur de fondu à toutes les LEDs
        for i in range(strip.numPixels()):
            r = (pixel_values[i] >> 16) & 0xFF
            g = (pixel_values[i] >> 8) & 0xFF
            b = pixel_values[i] & 0xFF

            r = int(r * fade_factor)
            g = int(g * fade_factor)
            b = int(b * fade_factor)

            pixel_values[i] = Color(r, g, b)

        # Allumer la LED de tête
        head_pos = steps % strip.numPixels()
        pixel_values[head_pos] = color

        # Mise à jour des LEDs
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, pixel_values[i])

        strip.show()
        time.sleep(wait_ms / 1000.0)
        steps += 1


def sparkle_effect(strip, background, sparkle_color, wait_ms=50, duration=5):
    """Effet d'étincelle aléatoire sur fond coloré"""
    import random

    # Définir la couleur d'arrière-plan
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, background)
    strip.show()

    start_time = time.time()
    while time.time() - start_time < duration:
        # Choisir aléatoirement quelques LEDs pour briller
        sparkle_positions = set()
        for k in range(5):  # 5 étincelles à la fois
            sparkle_positions.add(random.randint(0, strip.numPixels() - 1))

        # Allumer les étincelles
        for pos in sparkle_positions:
            strip.setPixelColor(pos, sparkle_color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

        # Restaurer la couleur d'arrière-plan pour ces LEDs
        for pos in sparkle_positions:
            strip.setPixelColor(pos, background)


def clear_leds(strip):
    """Éteindre toutes les LEDs"""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()


def main(animation_duration=5, transition_time=1.0):
    # Création de l'objet strip avec la configuration
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)

    # Initialisation de la bibliothèque
    strip.begin()

    print(f'Démo d\'animation pour anneau de {LED_COUNT} LEDs WS2812B sur GPIO {LED_PIN}')
    print(f'Durée de chaque animation: {animation_duration} secondes')
    print(f'Temps de transition entre animations: {transition_time} secondes')

    try:
        while True:
            print('Effet arc-en-ciel')
            rainbow_cycle(strip, duration=animation_duration)
            time.sleep(transition_time)

            print('Effet théâtral rouge')
            theater_chase(strip, Color(127, 0, 0), duration=animation_duration)  # Rouge
            time.sleep(transition_time)

            print('Effet théâtral bleu')
            theater_chase(strip, Color(0, 0, 127), duration=animation_duration)  # Bleu
            time.sleep(transition_time)

            print('Effet de respiration bleu-vert')
            breathing_effect(strip, Color(0, 127, 127), duration=animation_duration)
            time.sleep(transition_time)

            print('Balayage circulaire avec traînée')
            circular_sweep(strip, Color(0, 255, 0), duration=animation_duration)  # Vert
            time.sleep(transition_time)

            print('Effet d\'étincelles')
            sparkle_effect(strip, Color(10, 0, 40), Color(255, 255, 255), duration=animation_duration)
            time.sleep(transition_time)

            # Éteindre toutes les LEDs
            clear_leds(strip)
            time.sleep(transition_time)

    except KeyboardInterrupt:
        clear_leds(strip)
        print("\nProgramme arrêté par l'utilisateur")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Démo d\'animations LED')
    parser.add_argument('--duration', type=float, default=10.0,
                        help='Durée de chaque animation en secondes (défaut: 10.0)')
    parser.add_argument('--transition', type=float, default=1.0,
                        help='Temps de transition entre les animations en secondes (défaut: 1.0)')
    args = parser.parse_args()

    main(animation_duration=args.duration, transition_time=args.transition)