from dataclasses import dataclass, field
from typing import List, Optional

from .track import Track


@dataclass
class Playlist:
    """Represents a playlist of audio tracks.

    Attributes:
        name: Name of the playlist
        tracks: List of tracks in the playlist
        description: Optional description of the playlist
        id: Optional unique identifier
        nfc_tag_id: Optional NFC tag associated with the playlist
    """

    name: str
    tracks: List[Track] = field(default_factory=list)
    description: Optional[str] = None
    id: Optional[str] = None
    nfc_tag_id: Optional[str] = None

    @classmethod
    def from_files(cls, name: str, file_paths: List[str], **kwargs) -> "Playlist":
        """Create a playlist from a list of file paths.

        Args:
            name: Name of the playlist
            file_paths: List of file paths to create tracks from
            **kwargs: Additional attributes to set on the playlist

        Returns:
            A new Playlist instance
        """
        tracks = [
            Track.from_file(file_path, idx + 1)
            for idx, file_path in enumerate(file_paths)
        ]
        return cls(name=name, tracks=tracks, **kwargs)

    def get_track(self, number: int) -> Optional[Track]:
        """Get track by number (1-based index).

        Args:
            number: Track number to retrieve

        Returns:
            The track or None if not found
        """
        try:
            return next(t for t in self.tracks if t.number == number)
        except StopIteration:
            return None

    def add_track(self, track: Track) -> None:
        """Add a track to the playlist.

        Args:
            track: Track to add
        """
        # Auto-assign track number if not set
        if track.number <= 0:
            max_number = max([t.number for t in self.tracks], default=0)
            track.number = max_number + 1

        self.tracks.append(track)
        # Sort tracks by number
        self.tracks.sort(key=lambda t: t.number)

    def remove_track(self, track_number: int) -> Optional[Track]:
        """Remove a track by number and return it.

        Args:
            track_number: Number of the track to remove

        Returns:
            The removed track or None if not found
        """
        track = self.get_track(track_number)
        if track:
            self.tracks.remove(track)
            # Reindex remaining tracks
            for i, t in enumerate(sorted(self.tracks, key=lambda x: x.number), 1):
                t.number = i
        return track

    def __len__(self) -> int:
        """Return the number of tracks in the playlist."""
        return len(self.tracks)
