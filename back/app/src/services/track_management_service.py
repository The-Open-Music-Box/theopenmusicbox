# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Track management service for playlist track operations.

This service handles track-specific operations within playlists including
reordering, deletion, and track metadata management.
"""

from pathlib import Path
from typing import List

from app.src.data.playlist_repository import get_playlist_repository
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class TrackManagementService:
    """Service for managing tracks within playlists.

    Handles track reordering, deletion, and other track-specific operations
    while maintaining playlist integrity.
    """

    def __init__(self, config_obj=None):
        """Initialize the TrackManagementService.

        Args:
            config_obj: Optional configuration object. If not provided, uses global config.
        """
        from app.src.config import config as global_config

        self.config = config_obj or global_config
        self.repository = get_playlist_repository()

    def reorder_tracks(self, playlist_id: str, track_order: List[int]) -> bool:
        """Reorder tracks in a playlist based on the provided order.

        Args:
            playlist_id: ID of the playlist to reorder tracks in.
            track_order: List of track numbers in the desired order.

        Returns:
            True if the reordering was successful, False otherwise.
        """
        try:
            playlist = self.repository.get_playlist_by_id(playlist_id)
            if not playlist:
                logger.log(
                    LogLevel.ERROR,
                    f"Failed to reorder tracks: playlist {playlist_id} not found",
                )
                return False

            # Validate that all track numbers exist in the playlist
            current_track_numbers = {track["number"] for track in playlist["tracks"]}
            if set(track_order) != current_track_numbers:
                logger.log(
                    LogLevel.ERROR,
                    f"Invalid track order: provided numbers {track_order} "
                    f"don't match existing tracks {current_track_numbers}",
                )
                return False

            # Create a mapping of track number to track data
            tracks_by_number = {track["number"]: track for track in playlist["tracks"]}

            # Create new ordered list of tracks
            reordered_tracks = []
            for i, track_number in enumerate(track_order, 1):
                track = tracks_by_number[track_number].copy()
                # Update track number to reflect new position
                track["number"] = i
                reordered_tracks.append(track)

            playlist["tracks"] = reordered_tracks

            # Update the playlist in the repository
            playlist_id_to_update = playlist["id"]
            updated_data = dict(playlist)
            success = self.repository.update_playlist(
                playlist_id_to_update, updated_data
            )
            if success:
                logger.log(
                    LogLevel.INFO,
                    f"Successfully reordered tracks in playlist: {playlist_id}",
                )
            else:
                logger.log(
                    LogLevel.ERROR,
                    f"Failed to reorder tracks in playlist: {playlist_id}",
                )

            return success
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Error reordering tracks in playlist {playlist_id}: {str(e)}",
            )
            return False

    def delete_tracks(self, playlist_id: str, track_numbers: List[int]) -> bool:
        """Delete tracks from a playlist by their track numbers.

        Args:
            playlist_id: ID of the playlist containing the tracks to delete.
            track_numbers: List of track numbers to delete.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        try:
            playlist = self.repository.get_playlist_by_id(playlist_id)
            if not playlist:
                logger.log(
                    LogLevel.ERROR,
                    f"Failed to delete tracks: playlist {playlist_id} not found",
                )
                return False

            # Remove the specified tracks and collect deleted tracks
            original_track_count = len(playlist["tracks"])
            deleted_tracks = [
                t for t in playlist["tracks"] if t["number"] in track_numbers
            ]
            playlist["tracks"] = [
                t for t in playlist["tracks"] if t["number"] not in track_numbers
            ]

            # Delete corresponding audio files from disk
            for track in deleted_tracks:
                try:
                    # Try to resolve the full path to the audio file
                    file_path = None
                    if "path" in track and track["path"]:
                        file_path = Path(track["path"])
                    elif "filename" in track and "folder" in playlist:
                        file_path = Path(playlist["folder"]) / track["filename"]
                    elif "filename" in track and "path" in playlist:
                        file_path = Path(playlist["path"]) / track["filename"]
                    if file_path and file_path.exists():
                        file_path.unlink()
                        logger.log(LogLevel.INFO, f"Deleted audio file: {file_path}")
                    else:
                        logger.log(
                            LogLevel.WARNING,
                            f"Audio file not found for deleted track: "
                            f"{track.get('filename')}",
                        )
                except (OSError, IOError, PermissionError) as fe:
                    logger.log(
                        LogLevel.ERROR,
                        f"Failed to delete audio file for track "
                        f"{track.get('filename')}: {fe}",
                    )

            # If nothing was removed, return false
            if len(playlist["tracks"]) == original_track_count:
                logger.log(
                    LogLevel.WARNING,
                    f"No tracks deleted from playlist {playlist_id} - "
                    f"track numbers not found",
                )
                return False

            # Renumber remaining tracks
            for i, track in enumerate(playlist["tracks"], 1):
                track["number"] = i

            # Save the updated playlist
            playlist_id_to_update = playlist["id"]
            updated_data = dict(playlist)
            success = self.repository.update_playlist(
                playlist_id_to_update, updated_data
            )
            if success:
                deleted_count = original_track_count - len(playlist["tracks"])
                logger.log(
                    LogLevel.INFO,
                    f"Successfully deleted {deleted_count} tracks from "
                    f"playlist: {playlist_id}",
                )
            else:
                logger.log(
                    LogLevel.ERROR,
                    f"Failed to update playlist after deleting tracks: "
                    f"{playlist_id}",
                )

            return success
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Error deleting tracks from playlist {playlist_id}: {str(e)}",
            )
            return False

    def get_tracks_by_playlist(self, playlist_id: str) -> List[dict]:
        """Get all tracks for a specific playlist.

        Args:
            playlist_id: ID of the playlist.

        Returns:
            List of track dictionaries.
        """
        try:
            playlist = self.repository.get_playlist_by_id(playlist_id)
            if not playlist:
                return []
            return playlist.get("tracks", [])
        except Exception as e:
            logger.log(
                LogLevel.ERROR,
                f"Error getting tracks for playlist {playlist_id}: {str(e)}"
            )
            return []

    def get_track_count(self, playlist_id: str) -> int:
        """Get the number of tracks in a playlist.

        Args:
            playlist_id: ID of the playlist.

        Returns:
            Number of tracks in the playlist.
        """
        tracks = self.get_tracks_by_playlist(playlist_id)
        return len(tracks)

    def _validate_track_numbers(self, track_numbers: List[int], playlist_id: str) -> bool:
        """Validate track numbers for a playlist.

        Args:
            track_numbers: List of track numbers to validate.
            playlist_id: ID of the playlist.

        Returns:
            True if all track numbers are valid.

        Raises:
            ValueError: If track numbers are invalid.
        """
        if not track_numbers:
            raise ValueError("Track numbers list cannot be empty")

        tracks = self.get_tracks_by_playlist(playlist_id)
        max_track_number = len(tracks)

        for track_num in track_numbers:
            if track_num <= 0:
                raise ValueError(f"Track number {track_num} must be positive")
            if track_num > max_track_number:
                raise ValueError(
                    f"Track number {track_num} is out of range "
                    f"(max: {max_track_number})"
                )

        return True

    def move_track_up(self, playlist_id: str, track_number: int) -> bool:
        """Move a track up in the playlist order.

        Args:
            playlist_id: ID of the playlist.
            track_number: Number of the track to move up.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if track_number <= 1:
                logger.log(LogLevel.INFO, f"Track {track_number} is already at the top")
                return True

            tracks = self.get_tracks_by_playlist(playlist_id)
            if track_number > len(tracks):
                raise ValueError(f"Track number {track_number} is out of range")

            # Swap with previous track
            new_order = list(range(1, len(tracks) + 1))
            new_order[track_number - 1], new_order[track_number - 2] = (
                new_order[track_number - 2],
                new_order[track_number - 1]
            )
            
            return self.reorder_tracks(playlist_id, new_order)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error moving track up: {str(e)}")
            return False

    def move_track_down(self, playlist_id: str, track_number: int) -> bool:
        """Move a track down in the playlist order.

        Args:
            playlist_id: ID of the playlist.
            track_number: Number of the track to move down.

        Returns:
            True if successful, False otherwise.
        """
        try:
            tracks = self.get_tracks_by_playlist(playlist_id)
            if track_number >= len(tracks):
                logger.log(
                    LogLevel.INFO,
                    f"Track {track_number} is already at the bottom"
                )
                return True

            if track_number < 1:
                raise ValueError(f"Track number {track_number} is invalid")

            # Swap with next track
            new_order = list(range(1, len(tracks) + 1))
            new_order[track_number - 1], new_order[track_number] = (
                new_order[track_number],
                new_order[track_number - 1]
            )
            
            return self.reorder_tracks(playlist_id, new_order)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error moving track down: {str(e)}")
            return False
