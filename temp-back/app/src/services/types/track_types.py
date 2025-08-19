"""
Type definitions for track management operations.

This module provides TypedDict definitions and type aliases for better
type safety and code documentation in track management operations.
"""

from typing import TypedDict, Optional, List, Union, Dict, Any
from pathlib import Path


class TrackDict(TypedDict):
    """Type definition for track dictionary."""
    number: int
    filename: str
    path: Optional[str]
    title: Optional[str]
    artist: Optional[str]
    duration: Optional[float]
    file_size: Optional[int]


class PlaylistDict(TypedDict):
    """Type definition for playlist dictionary."""
    id: str
    name: str
    path: str
    tracks: List[TrackDict]
    created_at: Optional[str]
    updated_at: Optional[str]
    last_played: Optional[str]
    nfc_tag_id: Optional[str]


class TrackOperationResult(TypedDict):
    """Type definition for track operation results."""
    success: bool
    message: str
    affected_tracks: Optional[List[int]]
    playlist_id: Optional[str]
    operation_id: Optional[str]


class FileOperationResult(TypedDict):
    """Type definition for file operation results."""
    success: bool
    file_path: Optional[Path]
    error_message: Optional[str]
    track_info: Optional[TrackDict]


# Type aliases for better readability
TrackNumber = int
PlaylistId = str
TrackNumbers = List[TrackNumber]
TrackOrder = List[TrackNumber]

# Union types for operation results
OperationResult = Union[bool, TrackOperationResult]
ValidationResult = Union[bool, str]
