# app/src/module/gpio/gpio_interface.py

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

class PinMode(Enum):
    INPUT = "input"
    OUTPUT = "output"
    PWM = "pwm"

class GPIOInterface(ABC):

    @abstractmethod
    def setup_pin(self, pin: int, mode: PinMode, initial: Optional[bool] = None, timeout: float = 0) -> None:
        """
        Configure un pin GPIO.

        Args:
            pin: Numéro du pin GPIO
            mode: Mode du pin (INPUT/OUTPUT/PWM)
            initial: État initial pour les pins en sortie
        """

    @abstractmethod
    def read_pin(self, pin: int) -> bool:
        """
        Lit l'état d'un pin GPIO.

        Args:
            pin: Numéro du pin GPIO

        Returns:
            bool: État logique du pin
        """

    @abstractmethod
    def write_pin(self, pin: int, value: bool) -> None:
        """
        Écrit une valeur sur un pin GPIO.

        Args:
            pin: Numéro du pin GPIO
            value: Valeur à écrire
        """

    @abstractmethod
    def setup_pwm(self, pin: int, frequency: int = 1000) -> Any:
        """
        Configure un pin en mode PWM.

        Args:
            pin: Numéro du pin GPIO
            frequency: Fréquence PWM en Hz

        Returns:
            Any: Instance PWM
        """

    @abstractmethod
    def cleanup_pin(self, pin: int) -> None:
        """
        Nettoie la configuration d'un pin GPIO.

        Args:
            pin: Numéro du pin GPIO
        """

    @abstractmethod
    def cleanup_all(self) -> None:
        """Nettoie tous les pins GPIO configurés."""

    @abstractmethod
    def add_event_detect(self, pin: int, callback: callable, bouncetime: int = 200) -> None:
        """
        Configure la détection d'événements sur un pin.

        Args:
            pin: Numéro du pin GPIO
            callback: Fonction de callback
            bouncetime: Délai anti-rebond en ms
        """

    @abstractmethod
    def remove_event_detect(self, pin: int) -> None:
        """
        Supprime la détection d'événements sur un pin.

        Args:
            pin: Numéro du pin GPIO
        """
