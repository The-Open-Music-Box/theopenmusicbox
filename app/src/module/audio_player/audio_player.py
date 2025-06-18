"""Audio Player Abstraction Module.

This module defines the AudioPlayer wrapper class, which acts as the unified entry point for all audio playback operations in the application.
It delegates all playback actions to the underlying hardware implementation (real or mock), ensuring that routes, controllers, and services interact only with this abstraction.

Business Logic and Architectural Notes:
- The AudioPlayer class enforces strict separation between hardware-specific logic and business/application logic.
- All backend routes and controllers must use the AudioPlayer interface, never the hardware implementations directly.
- The wrapper ensures that the application can transparently switch between real and mock hardware for development, testing, or production.
- This promotes maintainability, testability, and platform independence.
"""

from typing import Generic, TypeVar

from .audio_hardware import AudioPlayerHardware

T = TypeVar("T", bound=AudioPlayerHardware)


class AudioPlayer(Generic[T]):
    """High-level Audio Player wrapper.

    Delegates all playback operations to the underlying hardware implementation (real or mock).
    This class is the ONLY entry point for audio playback in the backend and should be used by all controllers, routes, and services.

    State detection:
    - Use `is_playing` and `is_paused` for all playback state checks.
    - Do not rely on private attributes for playback state.

    Business Logic:
    - Ensures architectural consistency and prevents direct hardware access from business logic layers.
    - Enables seamless switching between mock and real hardware based on environment/configuration.
    - Guarantees that only the methods defined in the AudioPlayerHardware Protocol are exposed.
    """

    def __init__(self, hardware: T):
        """Initialize the audio player abstraction with a specific hardware
        implementation.

        Args:
            hardware: An implementation of AudioPlayerHardware (real or mock)
        """
        self._hardware = hardware

    def play(self, track: str) -> None:
        """Play a specific track by filename or path.

        Delegates to the hardware implementation.
        """
        self._hardware.play(track)

    def pause(self) -> None:
        """Pause playback.

        Delegates to the hardware implementation.
        """
        # Execute pause without blocking on notifications
        self._hardware.pause()

    def resume(self) -> None:
        """Resume playback.

        Delegates to the hardware implementation.
        """
        # Execute resume without blocking on notifications
        self._hardware.resume()

    def stop(self) -> None:
        """Stop playback.

        Delegates to the hardware implementation.
        """
        # Execute stop without blocking on notifications
        self._hardware.stop()

    def set_volume(self, volume: float) -> None:
        """Set the playback volume (0.0-100.0).

        Delegates to the hardware implementation.
        """
        # Execute set_volume without blocking on notifications
        self._hardware.set_volume(volume)

    def cleanup(self) -> None:
        """Release hardware resources and perform any necessary cleanup.

        Delegates to the hardware implementation.
        """
        self._hardware.cleanup()

    def set_playlist(self, playlist) -> bool:
        """Set the current playlist and start playback.

        Delegates to the hardware implementation. Returns True if the
        playlist was set and playback started, False otherwise.
        """
        return self._hardware.set_playlist(playlist)

    def next_track(self) -> None:
        """Advance to the next track in the playlist.

        Delegates to the hardware implementation.
        """
        # Execute next_track without blocking on notifications
        self._hardware.next_track()

    def previous_track(self) -> None:
        """Return to the previous track in the playlist.

        Delegates to the hardware implementation.
        """
        # Execute previous_track without blocking on notifications
        self._hardware.previous_track()

    def play_track(self, track_number: int) -> bool:
        """Play a specific track in the playlist by its number.

        Delegates to the hardware implementation. Returns True if the
        track was played successfully, False otherwise.
        """
        return self._hardware.play_track(track_number)

    @property
    def is_playing(self) -> bool:
        """Check if the player is currently playing audio.

        Delegates to the hardware implementation. Returns True if audio
        is playing, False otherwise.
        """
        return self._hardware.is_playing

    def is_finished(self) -> bool:
        """Check if the current playlist has finished playing.

        Delegates to the hardware implementation. Returns True if the
        playlist has finished, False otherwise.
        """
        return self._hardware.is_finished()

    @property
    def is_paused(self) -> bool:
        """Return True if the player is paused (not playing, but a track is
        loaded).

        Delegates to the hardware implementation.
        """
        return self._hardware.is_paused
