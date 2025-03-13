# app/src/model/track.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Track:
    number: int
    title: str
    filename: str
    path: Path
    duration: Optional[float] = None  # Duration in seconds

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @classmethod
    def from_file(cls, file_path: str, number: int = 1) -> 'Track':
        path = Path(file_path)
        return cls(
            number=number,
            title=path.stem,
            filename=path.name,
            path=path
        )