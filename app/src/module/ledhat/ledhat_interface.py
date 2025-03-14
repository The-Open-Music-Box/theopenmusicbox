# app/src/module/ledhat/ledhat_interface.py

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any

class LedHatInterface(ABC):
    """
    Interface abstraite pour contrôler un ruban de LED RGB.
    """

    @abstractmethod
    def set_pixel(self, i: int, color: Tuple[int, int, int]) -> None:
        """
        Définit la couleur d'un pixel spécifique.

        Args:
            i: Index du pixel
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
        """
        pass

    @abstractmethod
    def set_all_pixels(self, color: Tuple[int, int, int]) -> None:
        """
        Définit tous les pixels à la même couleur.

        Args:
            color: Tuple RGB (r, g, b) avec des valeurs de 0 à 255
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Éteint tous les pixels."""
        pass

    @abstractmethod
    def start_animation(self, animation_name: str, **kwargs) -> None:
        """
        Démarre une animation en continu dans un thread séparé.

        Args:
            animation_name: Nom de l'animation à exécuter
            **kwargs: Paramètres spécifiques à l'animation
        """
        pass

    @abstractmethod
    def stop_animation(self) -> None:
        """Arrête l'animation en cours."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Nettoie et libère les ressources."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Alias pour close() pour compatibilité avec le container."""
        pass

    @property
    @abstractmethod
    def current_animation(self) -> Optional[str]:
        """Retourne le nom de l'animation en cours, ou None si aucune animation n'est en cours."""
        pass

    @property
    @abstractmethod
    def animation_params(self) -> Dict[str, Any]:
        """Retourne les paramètres de l'animation en cours."""
        pass