"""
Audio Player Protocol Definition

Defines the interface (Protocol) for all audio player hardware implementations.
This abstraction ensures that both real and mock audio players provide a consistent set of methods for playback control, playlist management, and resource cleanup.

Business Logic and Architectural Notes:
- All hardware-specific audio logic must be implemented in a class conforming to this Protocol.
- The Protocol is used by the AudioPlayer wrapper to enforce architectural boundaries and allow seamless switching between real and mock hardware.
- Only methods required by the application's business logic are included here.
- Any new method required by business logic must be added to this Protocol and implemented in all hardware classes.
"""

from typing import Protocol

class AudioPlayerHardware(Protocol):
    """
    Protocol for audio player hardware implementations.

    This interface defines the contract for all audio player backends (real or mock).
    All methods here must be implemented by any concrete audio player class.
    Used by the AudioPlayer wrapper to ensure consistent and safe audio control.
    """
    def play(self, track: str) -> None:
        """
        Play a specific track by filename or path.
        Args:
            track: The filename or path of the audio track to play.
        """
        pass

    def pause(self) -> None:
        """
        Pause playback.
        """
        pass

    def resume(self) -> None:
        """
        Resume playback from a paused state.
        """
        pass

    def stop(self) -> None:
        """
        Stop playback immediately.
        """
        pass

    def set_volume(self, volume: float) -> None:
        """
        Set the playback volume.
        Args:
            volume: A float in the range 0.0 to 100.0 representing the desired volume.
        """
        pass

    def cleanup(self) -> None:
        """
        Release hardware resources and perform any necessary cleanup.
        """
        pass

    def set_playlist(self, playlist) -> bool:
        """
        Set the current playlist and start playback.
        Args:
            playlist: The playlist object to set for playback.
        Returns:
            True if the playlist was set and playback started, False otherwise.
        """
        pass

    def next_track(self) -> None:
        """
        Advance to the next track in the current playlist.
        """
        pass

    def previous_track(self) -> None:
        """
        Return to the previous track in the current playlist.
        """
        pass

    def play_track(self, track_number: int) -> bool:
        """
        Play a specific track in the playlist by its number.
        Args:
            track_number: The 1-based index of the track to play.
        Returns:
            True if the track was played successfully, False otherwise.
        """
        pass

