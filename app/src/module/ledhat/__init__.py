# app/src/module/ledhat/__init__.py

"""
Module pour contrôler un ruban de LED pour l'application.
Fournit une interface abstraite et des implémentations spécifiques à la plateforme.

Ce module offre:
- Une interface unifiée pour les opérations LED
- Deux implémentations: une réelle pour Raspberry Pi et une mock pour les tests/développement
- Une détection automatique de la plateforme
- Un composant optionnel qui ne bloque pas le démarrage de l'application

Le composant est conçu pour être optionnel et son statut peut être remonté dans la route health.
"""

from .ledhat_interface import LedHatInterface
from .ledhat_factory import get_led_hat

__all__ = [
    'LedHatInterface',
    'get_led_hat'
]