# app/src/hardware/motor/motor_interface.py

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Callable

class MotorDirection(Enum):
    CLOCKWISE = "clockwise"
    COUNTERCLOCKWISE = "counterclockwise"

@dataclass
class MotorStatus:
    steps: int
    is_running: bool
    direction: MotorDirection
    speed: int

class MotorInterface(ABC):
    @abstractmethod
    def start(self, direction: MotorDirection, speed: int) -> None:
        """
        Démarre le moteur.
        Args:
            direction: Sens de rotation
            speed: Vitesse en pas/seconde (1-1000)
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Arrête le moteur."""
        pass
    
    @abstractmethod
    def subscribe_position(self, callback: Callable[[int], None]) -> None:
        """Subscribe aux changements de position."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Nettoie les ressources."""
        pass
