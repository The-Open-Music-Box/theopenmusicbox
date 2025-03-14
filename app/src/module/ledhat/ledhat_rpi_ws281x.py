# app/src/module/ledhat/ledhat_rpi_ws281x.py

import time
import math
import threading
from typing import Tuple, Optional, Dict, Any, List
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .ledhat_interface import LedHatInterface
from rpi_ws281x import PixelStrip, Color

logger = ImprovedLogger(__name__)

class RpiWs281xLedHat(LedHatInterface):
    """
    Implémentation pour Raspberry Pi du contrôleur de ruban LED utilisant la bibliothèque rpi_ws281x.
    Basée sur l'exemple de code dans app/demo/ledhat.py.
    """

    def __init__(self, num_pixels: int = 36, brightness: float = 0.2, pin: int = 12):
        """
        Initialise le contrôleur de ruban LED pour Raspberry Pi avec rpi_ws281x.

        Args:
            num_pixels: Nombre de LEDs sur le ruban
            brightness: Luminosité des LEDs (0.0 à 1.0)
            pin: La broche GPIO à laquelle le ruban est connecté
        """
        self.num_pixels = num_pixels

        # Conversion de la luminosité (0.0-1.0) en valeur entière (0-255)
        led_brightness = int(brightness * 255)

        # Configuration pour la strip LED
        LED_FREQ_HZ = 800000  # Fréquence du signal LED en Hz
        LED_DMA = 10          # Canal DMA à utiliser pour générer le signal
        LED_INVERT = False    # Inversion du signal (si transistor NPN)
        LED_CHANNEL = 0       # '0' pour GPIO 12, 18

        # Création de l'objet strip avec la configuration
        self.pixels = PixelStrip(
            num_pixels, pin, LED_FREQ_HZ, LED_DMA, LED_INVERT, led_brightness, LED_CHANNEL
        )

        # Initialisation de la bibliothèque
        self.pixels.begin()

        self._running = False
        self._current_animation = None
        self._animation_params = {}
        self._animation_thread = None
        logger.log(LogLevel.INFO, f"Initialized Raspberry Pi LED Hat (rpi_ws281x) with {num_pixels} pixels")

    def set_pixel(self, i: int, color: Tuple[int, int, int]) -> None:
        """
        Définit la couleur d'un pixel spécifique.

        Args:
            i: Index du pixel
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
        """
        if 0 <= i < self.num_pixels:
            r, g, b = color
            self.pixels.setPixelColor(i, Color(r, g, b))

    def set_all_pixels(self, color: Tuple[int, int, int]) -> None:
        """
        Définit tous les pixels à la même couleur.

        Args:
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
        """
        r, g, b = color
        for i in range(self.num_pixels):
            self.pixels.setPixelColor(i, Color(r, g, b))
        self.pixels.show()

    def clear(self) -> None:
        """Éteint tous les pixels."""
        for i in range(self.num_pixels):
            self.pixels.setPixelColor(i, Color(0, 0, 0))
        self.pixels.show()

    def rainbow_cycle(self, wait: float = 0.01) -> None:
        """
        Animation de cycle en arc-en-ciel.

        Args:
            wait: Temps d'attente entre les mises à jour (en secondes)
        """
        for j in range(255):
            if not self._running:
                break
            for i in range(self.num_pixels):
                rc_index = (i * 256 // self.num_pixels) + j
                self.pixels.setPixelColor(i, self._wheel(rc_index & 255))
            self.pixels.show()
            time.sleep(wait)

    def color_wipe(self, color: Tuple[int, int, int], wait: float = 0.05) -> None:
        """
        Animation de remplissage progressif d'une couleur.

        Args:
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
            wait: Temps d'attente entre les mises à jour (en secondes)
        """
        r, g, b = color
        for i in range(self.num_pixels):
            if not self._running:
                break
            self.pixels.setPixelColor(i, Color(r, g, b))
            self.pixels.show()
            time.sleep(wait)

    def theater_chase(self, color: Tuple[int, int, int], wait: float = 0.05, iterations: int = 10) -> None:
        """
        Animation de poursuite de théâtre.

        Args:
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
            wait: Temps d'attente entre les mises à jour (en secondes)
            iterations: Nombre d'itérations de l'animation
        """
        r, g, b = color
        color_value = Color(r, g, b)

        iteration_count = 0
        while self._running and (iterations <= 0 or iteration_count < iterations):
            for q in range(3):
                if not self._running:
                    break
                for i in range(0, self.num_pixels, 3):
                    if i + q < self.num_pixels:
                        self.pixels.setPixelColor(i + q, color_value)
                self.pixels.show()
                time.sleep(wait)
                for i in range(0, self.num_pixels, 3):
                    if i + q < self.num_pixels:
                        self.pixels.setPixelColor(i + q, Color(0, 0, 0))
            iteration_count += 1

    def pulse(self, color: Tuple[int, int, int], wait: float = 0.01, steps: int = 100) -> None:
        """
        Animation de pulsation d'une couleur.

        Args:
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
            wait: Temps d'attente entre les mises à jour (en secondes)
            steps: Nombre d'étapes pour la pulsation
        """
        r, g, b = color

        while self._running:
            # Augmentation de l'intensité
            for i in range(steps):
                if not self._running:
                    break
                intensity = i / steps
                for j in range(self.num_pixels):
                    self.pixels.setPixelColor(j, Color(
                        int(r * intensity),
                        int(g * intensity),
                        int(b * intensity)
                    ))
                self.pixels.show()
                time.sleep(wait)

            # Diminution de l'intensité
            for i in range(steps, 0, -1):
                if not self._running:
                    break
                intensity = i / steps
                for j in range(self.num_pixels):
                    self.pixels.setPixelColor(j, Color(
                        int(r * intensity),
                        int(g * intensity),
                        int(b * intensity)
                    ))
                self.pixels.show()
                time.sleep(wait)

    def breathing_effect(self, color: Tuple[int, int, int], wait: float = 0.01, steps: int = 100) -> None:
        """
        Effet de respiration - la luminosité monte et descend en utilisant une courbe sinusoïdale.

        Args:
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
            wait: Temps d'attente entre les mises à jour (en secondes)
            steps: Nombre d'étapes pour la respiration
        """
        r, g, b = color

        while self._running:
            # Respiration complète
            for k in range(steps):
                if not self._running:
                    break
                brightness = math.sin(math.pi * k / steps) * math.sin(math.pi * k / steps)
                r_adj = int(r * brightness)
                g_adj = int(g * brightness)
                b_adj = int(b * brightness)
                for i in range(self.num_pixels):
                    self.pixels.setPixelColor(i, Color(r_adj, g_adj, b_adj))
                self.pixels.show()
                time.sleep(wait)

    def rotating_circle(self, color: Tuple[int, int, int] = (0, 0, 255),
                       background_color: Tuple[int, int, int] = (0, 0, 0),
                       segment_length: int = 5,
                       rotation_time: float = 3.0,
                       continuous: bool = False) -> None:
        """
        Animation d'un segment lumineux qui tourne autour du cercle de LEDs.

        Args:
            color: Tuple RGB (r, g, b) pour la couleur du segment lumineux
            background_color: Tuple RGB (r, g, b) pour la couleur de fond
            segment_length: Nombre de LEDs allumées dans le segment
            rotation_time: Temps en secondes pour une rotation complète
            continuous: Si True, l'animation continue en boucle jusqu'à stop_animation()
        """
        try:
            r, g, b = color
            color_value = Color(r, g, b)

            bg_r, bg_g, bg_b = background_color
            bg_color_value = Color(bg_r, bg_g, bg_b)

            # Calculer le délai entre chaque étape pour atteindre le temps de rotation souhaité
            steps = self.num_pixels
            wait = rotation_time / steps

            # Boucle principale d'animation
            iterations = 0
            while self._running or iterations == 0:
                for start_pos in range(self.num_pixels):
                    if not self._running and iterations > 0:
                        break

                    # Réinitialiser tous les pixels à la couleur de fond
                    for i in range(self.num_pixels):
                        self.pixels.setPixelColor(i, bg_color_value)

                    # Allumer le segment de LEDs
                    for i in range(segment_length):
                        pixel_pos = (start_pos + i) % self.num_pixels
                        self.pixels.setPixelColor(pixel_pos, color_value)

                    self.pixels.show()
                    time.sleep(wait)

                iterations += 1
                if not continuous and iterations >= 1:
                    break

            # Si l'animation n'est pas continue ou a été arrêtée, éteindre les LEDs
            if not self._running:
                self.clear()

        except Exception as e:
            import traceback
            logger.log(LogLevel.ERROR, f"Erreur dans rotating_circle: {e}")
            logger.log(LogLevel.DEBUG, f"Détails: {traceback.format_exc()}")

    def circular_sweep(self, color: Tuple[int, int, int], wait: float = 0.005, duration: float = 5.0) -> None:
        """
        Balayage circulaire avec traînée.

        Args:
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
            wait: Temps d'attente entre les mises à jour (en secondes)
            duration: Durée de l'animation en secondes
        """
        r, g, b = color
        color_value = Color(r, g, b)
        fade_factor = 0.9  # Facteur de diminution pour la traînée

        start_time = time.time()
        # Initialisation des couleurs
        pixel_values = [0] * self.num_pixels

        steps = 0
        while self._running and (time.time() - start_time < duration):
            # Appliquer le facteur de fondu à toutes les LEDs
            for i in range(self.num_pixels):
                pixel_color = pixel_values[i]
                r = (pixel_color >> 16) & 0xFF
                g = (pixel_color >> 8) & 0xFF
                b = pixel_color & 0xFF

                r = int(r * fade_factor)
                g = int(g * fade_factor)
                b = int(b * fade_factor)

                pixel_values[i] = Color(r, g, b)

            # Allumer la LED de tête
            head_pos = steps % self.num_pixels
            pixel_values[head_pos] = color_value

            # Mise à jour des LEDs
            for i in range(self.num_pixels):
                self.pixels.setPixelColor(i, pixel_values[i])

            self.pixels.show()
            time.sleep(wait)
            steps += 1

    def sparkle_effect(self, background: Tuple[int, int, int], sparkle_color: Tuple[int, int, int],
                      wait: float = 0.05, duration: float = 5.0) -> None:
        """
        Effet d'étincelle aléatoire sur fond coloré.

        Args:
            background: Tuple RGB (r, g, b) pour la couleur de fond
            sparkle_color: Tuple RGB (r, g, b) pour la couleur des étincelles
            wait: Temps d'attente entre les mises à jour (en secondes)
            duration: Durée de l'animation en secondes
        """
        import random

        bg_r, bg_g, bg_b = background
        bg_color = Color(bg_r, bg_g, bg_b)

        sp_r, sp_g, sp_b = sparkle_color
        sp_color = Color(sp_r, sp_g, sp_b)

        # Définir la couleur d'arrière-plan
        for i in range(self.num_pixels):
            self.pixels.setPixelColor(i, bg_color)
        self.pixels.show()

        start_time = time.time()
        while self._running and (time.time() - start_time < duration):
            # Choisir aléatoirement quelques LEDs pour briller
            sparkle_positions = set()
            for k in range(5):  # 5 étincelles à la fois
                sparkle_positions.add(random.randint(0, self.num_pixels - 1))

            # Allumer les étincelles
            for pos in sparkle_positions:
                self.pixels.setPixelColor(pos, sp_color)
            self.pixels.show()
            time.sleep(wait)

            # Restaurer la couleur d'arrière-plan pour ces LEDs
            for pos in sparkle_positions:
                self.pixels.setPixelColor(pos, bg_color)

    def start_animation(self, animation_name: str, **kwargs) -> None:
        """
        Démarre une animation en continu dans un thread séparé.

        Args:
            animation_name: Nom de l'animation à exécuter
            **kwargs: Paramètres spécifiques à l'animation
        """
        self.stop_animation()
        self._current_animation = animation_name
        self._animation_params = kwargs
        self._running = True

        # Démarrer l'animation dans un thread séparé
        self._animation_thread = threading.Thread(
            target=self._run_animation,
            args=(animation_name, kwargs),
            daemon=True
        )
        self._animation_thread.start()
        logger.log(LogLevel.INFO, f"Started animation '{animation_name}' with params {kwargs}")

    def _run_animation(self, animation_name: str, kwargs: dict) -> None:
        """
        Exécute l'animation spécifiée dans un thread séparé.

        Args:
            animation_name: Nom de l'animation à exécuter
            kwargs: Paramètres spécifiques à l'animation
        """
        try:
            if animation_name == "rainbow_cycle":
                self.rainbow_cycle(**kwargs)
            elif animation_name == "color_wipe":
                self.color_wipe(**kwargs)
            elif animation_name == "theater_chase":
                self.theater_chase(**kwargs)
            elif animation_name == "pulse":
                self.pulse(**kwargs)
            elif animation_name == "rotating_circle":
                self.rotating_circle(**kwargs)
            elif animation_name == "breathing_effect":
                self.breathing_effect(**kwargs)
            elif animation_name == "circular_sweep":
                self.circular_sweep(**kwargs)
            elif animation_name == "sparkle_effect":
                self.sparkle_effect(**kwargs)
            else:
                logger.log(LogLevel.WARNING, f"Animation inconnue: {animation_name}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Erreur dans l'animation {animation_name}: {e}")
        finally:
            # Réinitialiser l'état si l'animation se termine
            if self._current_animation == animation_name:
                self._running = False
                self._current_animation = None
                self._animation_params = {}

    def stop_animation(self) -> None:
        """Arrête l'animation en cours."""
        self._running = False
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=1.0)  # Attendre que le thread se termine
        self._current_animation = None
        self._animation_params = {}
        self._animation_thread = None

    def close(self) -> None:
        """Nettoie et libère les ressources."""
        try:
            logger.log(LogLevel.INFO, "Cleaning up LED hat resources")
            self.stop_animation()
            self.clear()
            # Forcer l'affichage des LEDs éteintes
            self.pixels.show()
            logger.log(LogLevel.INFO, "LED hat resources cleaned up successfully")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during LED hat cleanup: {e}")

    def cleanup(self) -> None:
        """Alias pour close() pour compatibilité avec le container."""
        self.close()

    def _wheel(self, pos: int) -> int:
        """
        Fonction d'aide pour l'animation arc-en-ciel.

        Args:
            pos: Position dans la roue des couleurs (0-255)

        Returns:
            Valeur de couleur au format Color
        """
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    @property
    def current_animation(self) -> Optional[str]:
        """Retourne le nom de l'animation en cours, ou None si aucune animation n'est en cours."""
        return self._current_animation

    @property
    def animation_params(self) -> Dict[str, Any]:
        """Retourne les paramètres de l'animation en cours."""
        return self._animation_params