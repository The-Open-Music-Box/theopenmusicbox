# app/src/module/light_sensor/light_sensor_interface.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from rx.subject import Subject

@dataclass
class LightLevel:
    lux: float

class LightSensorInterface(ABC):
    @property
    @abstractmethod
    def light_level_stream(self) -> Subject:
        """Get observable stream of light level updates."""

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
