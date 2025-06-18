from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Track:
    """Represents an audio track in a playlist.

    Attributes:
        number: Position in the playlist (1-based)
        title: Title of the track
        filename: Filename of the track
        path: Path to the track file
        duration: Optional duration in seconds
        artist: Optional artist name
        album: Optional album name
    """

    number: int
    title: str
    filename: str
    path: Path
    duration: Optional[float] = None  # Duration in seconds
    artist: Optional[str] = None
    album: Optional[str] = None
    id: Optional[int] = None

    @property
    def exists(self) -> bool:
        """Check if the track file exists."""
        return self.path.exists()

    @classmethod
    def from_file(cls, file_path: str, number: int = 1) -> "Track":
        """Create a track from a file path.

        Args:
            file_path: Path to the audio file
            number: Position in the playlist (default: 1)

        Returns:
            A new Track instance
        """
        path = Path(file_path)
        return cls(number=number, title=path.stem, filename=path.name, path=path)

    def __str__(self) -> str:
        """Return a string representation of the track."""
        return f"{self.number}. {self.title}"
