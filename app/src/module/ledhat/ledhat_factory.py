# app/src/module/ledhat/ledhat_factory.py

import sys
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .ledhat_interface import LedHatInterface

logger = ImprovedLogger(__name__)

def get_led_hat(num_pixels: int = 36, brightness: float = 0.2) -> LedHatInterface:
    """
    Retourne l'implémentation appropriée du contrôleur LED en fonction de la plateforme.
    Si l'implémentation réelle échoue, aucun fallback n'est effectué et une exception est levée.

    Le composant est optionnel et ne doit pas empêcher l'application de démarrer.
    Son statut peut être remonté dans la route health.

    Args:
        num_pixels: Nombre de LEDs sur le ruban
        brightness: Luminosité des LEDs (0.0 à 1.0)

    Returns:
        Une instance de LedHatInterface

    Raises:
        ImportError: Si les bibliothèques nécessaires ne sont pas disponibles
        Exception: Si l'initialisation du matériel échoue
    """
    if sys.platform == 'darwin' or sys.platform == 'win32':
        # Utiliser l'implémentation mock pour macOS et Windows
        from .ledhat_mock import MockLedHat
        logger.log(LogLevel.INFO, f"Creating mock LED hat with {num_pixels} pixels")
        return MockLedHat(num_pixels=num_pixels, brightness=brightness)
    else:
        # Utiliser l'implémentation réelle pour Raspberry Pi (Linux)
        # Pas de fallback automatique, si ça échoue, le composant sera en erreur
        from .ledhat_rpi_ws281x import RpiWs281xLedHat
        logger.log(LogLevel.INFO, f"Creating Raspberry Pi LED hat with {num_pixels} pixels")
        return RpiWs281xLedHat(num_pixels=num_pixels, brightness=brightness)