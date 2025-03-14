# app/src/module/ledhat/ledhat_mock.py

import time
import threading
from typing import Tuple, Optional, Dict, Any, List
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .ledhat_interface import LedHatInterface

logger = ImprovedLogger(__name__)

class MockLedHat(LedHatInterface):
    """
    Implémentation mock du contrôleur de ruban LED pour les tests et le développement.
    """

    def __init__(self, num_pixels: int = 36, brightness: float = 0.2):
        """
        Initialise le contrôleur mock de ruban LED.

        Args:
            num_pixels: Nombre de LEDs sur le ruban
            brightness: Luminosité des LEDs (0.0 à 1.0)
        """
        self.num_pixels = num_pixels
        self.brightness = brightness
        self.pixels = [(0, 0, 0)] * num_pixels  # Simule un tableau de pixels
        self._running = False
        self._current_animation = None
        self._animation_params = {}
        self._animation_thread = None
        logger.log(LogLevel.INFO, f"Initialized Mock LED Hat with {num_pixels} pixels")

    def set_pixel(self, i: int, color: Tuple[int, int, int]) -> None:
        """
        Définit la couleur d'un pixel spécifique.

        Args:
            i: Index du pixel
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
        """
        if 0 <= i < self.num_pixels:
            self.pixels[i] = color
            logger.log(LogLevel.DEBUG, f"[MockLedHat] Set pixel {i} to color {color}")

    def set_all_pixels(self, color: Tuple[int, int, int]) -> None:
        """
        Définit tous les pixels à la même couleur.

        Args:
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
        """
        self.pixels = [color] * self.num_pixels
        logger.log(LogLevel.DEBUG, f"[MockLedHat] Set all pixels to color {color}")

    def clear(self) -> None:
        """Éteint tous les pixels."""
        self.pixels = [(0, 0, 0)] * self.num_pixels
        logger.log(LogLevel.DEBUG, "[MockLedHat] Cleared all pixels")

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
        logger.log(LogLevel.INFO, f"[MockLedHat] Started animation '{animation_name}' with params {kwargs}")

    def _run_animation(self, animation_name: str, kwargs: dict) -> None:
        """
        Simule l'exécution de l'animation spécifiée dans un thread séparé.

        Args:
            animation_name: Nom de l'animation à exécuter
            kwargs: Paramètres spécifiques à l'animation
        """
        try:
            # Simuler l'animation en cours pendant quelques secondes
            animation_duration = kwargs.get('duration', 10)
            start_time = time.time()

            while self._running and (time.time() - start_time < animation_duration):
                # Simuler une mise à jour de l'animation
                logger.log(LogLevel.DEBUG, f"[MockLedHat] Running animation '{animation_name}' (t={time.time() - start_time:.1f}s)")
                time.sleep(0.5)  # Réduire la fréquence des logs

            logger.log(LogLevel.INFO, f"[MockLedHat] Animation '{animation_name}' completed or stopped")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"[MockLedHat] Error in animation {animation_name}: {e}")
        finally:
            # Réinitialiser l'état si l'animation se termine
            if self._current_animation == animation_name:
                self._running = False
                self._current_animation = None
                self._animation_params = {}

    def stop_animation(self) -> None:
        """Arrête l'animation en cours."""
        if self._running:
            self._running = False
            if self._animation_thread and self._animation_thread.is_alive():
                self._animation_thread.join(timeout=1.0)  # Attendre que le thread se termine
            self._current_animation = None
            self._animation_params = {}
            self._animation_thread = None
            logger.log(LogLevel.INFO, "[MockLedHat] Animation stopped")

    def close(self) -> None:
        """Nettoie et libère les ressources."""
        try:
            logger.log(LogLevel.INFO, "Cleaning up mock LED hat resources")
            self.stop_animation()
            self.clear()
            logger.log(LogLevel.INFO, "Mock LED hat resources cleaned up successfully")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during mock LED hat cleanup: {e}")

    def cleanup(self) -> None:
        """Alias pour close() pour compatibilité avec le container."""
        self.close()

    @property
    def current_animation(self) -> Optional[str]:
        """Retourne le nom de l'animation en cours, ou None si aucune animation n'est en cours."""
        return self._current_animation

    @property
    def animation_params(self) -> Dict[str, Any]:
        """Retourne les paramètres de l'animation en cours."""
        return self._animation_params.copy()