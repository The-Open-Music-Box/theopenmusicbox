# app/src/module/audio_player/audio_player.py
from typing import Generic, TypeVar
from .audio_hardware import AudioPlayerHardware

T = TypeVar('T', bound=AudioPlayerHardware)

class AudioPlayer(Generic[T]):
    def __init__(self, hardware: T):
        self._hardware = hardware

    def play(self, track: str) -> None:
        self._hardware.play(track)

    def pause(self) -> None:
        self._hardware.pause()

    def stop(self) -> None:
        self._hardware.stop()

    def set_volume(self, volume: float) -> None:
        self._hardware.set_volume(volume)

    def cleanup(self) -> None:
        self._hardware.cleanup()
