# app/src/model/playlist.py

from dataclasses import dataclass, field
from typing import List, Optional
from .track import Track

@dataclass
class Playlist:
    name: str
    tracks: List[Track] = field(default_factory=list)
    description: Optional[str] = None

    @classmethod
    def from_files(cls, name: str, file_paths: List[str]) -> 'Playlist':
        tracks = [
            Track.from_file(file_path, idx + 1)
            for idx, file_path in enumerate(file_paths)
        ]
        return cls(name=name, tracks=tracks)

    def get_track(self, number: int) -> Optional[Track]:
        """Get track by number (1-based index)"""
        try:
            return self.tracks[number - 1]
        except IndexError:
            return None

    def __len__(self) -> int:
        return len(self.tracks)