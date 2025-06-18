"""
playlist_service.py

Service layer for playlist management in TheMusicBox backend.
Provides business logic for playlist CRUD, NFC association, filesystem sync,
and integration with YouTube downloads and audio playback.
"""

import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.src.data.playlist_repository import PlaylistRepository
from app.src.model.playlist import Playlist
from app.src.model.track import Track
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class PlaylistService:
    """
    Service for managing playlists with business logic.

    This service acts as an intermediary between the presentation layer
    (such as API routes or UI) and the data access layer for playlist-related operations.
    It provides methods for playlist CRUD, NFC tag association, filesystem synchronization,
    and integration with YouTube downloads and audio playback.
    """

    # Supported audio file extensions
    SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".m4a", ".flac", ".aac"}

    # Synchronization timeouts (in seconds)
    SYNC_TOTAL_TIMEOUT = 10.0
    SYNC_FOLDER_TIMEOUT = 1.0
    SYNC_OPERATION_TIMEOUT = 2.0

    def __init__(self, config_obj=None):
        """
        Initialize the PlaylistService instance.

        Args:
            config_obj: Optional configuration object. If not provided, uses the global config.
        """
        from app.src.config import config as global_config

        self.config = config_obj or global_config
        self.repository = PlaylistRepository(self.config)
        self.upload_folder = Path(self.config.upload_folder)
        self._sync_lock = threading.RLock()

    def create_playlist(self, title: str) -> dict:
        """
        Create a new empty playlist with the given title.

        Args:
            title: The title of the new playlist.
        Returns:
            Dictionary representing the created playlist.
        """
        playlist_data = {
            "id": str(uuid4()),
            "type": "playlist",
            "title": title,
            "path": title.replace(" ", "_"),  # or generate a unique path
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tracks": [],
        }
        self.repository.create_playlist(playlist_data)
        return playlist_data

    def delete_playlist(self, playlist_id: str) -> dict:
        """
        Delete a playlist by its ID.

        Args:
            playlist_id: The ID of the playlist to delete.
        Returns:
            Dictionary with deletion status.
        Raises:
            ValueError: If the playlist is not found.
        """
        deleted = self.repository.delete_playlist(playlist_id)
        if not deleted:
            raise ValueError(f"Playlist with id {playlist_id} not found")
        return {"id": playlist_id, "deleted": True}

    def get_all_playlists(self, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve all playlists with pagination support.

        Args:
            page: Page number (1-based).
            page_size: Number of playlists per page.
        Returns:
            List of dictionaries representing playlists.
        """
        offset = (page - 1) * page_size
        return self.repository.get_all_playlists(limit=page_size, offset=offset)

    def get_playlist_by_id(
        self, playlist_id: str, track_page: int = 1, track_page_size: int = 1000
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a playlist by its ID with optional track pagination.

        Args:
            playlist_id: Playlist ID.
            track_page: Page number for tracks (1-based).
            track_page_size: Number of tracks per page.
        Returns:
            Dictionary representing the playlist or None if not found.
        """
        track_offset = (track_page - 1) * track_page_size
        return self.repository.get_playlist_by_id(
            playlist_id, track_limit=track_page_size, track_offset=track_offset
        )

    def get_playlist_by_nfc_tag(self, nfc_tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a playlist by its associated NFC tag ID.

        Args:
            nfc_tag_id: NFC tag ID.
        Returns:
            Dictionary representing the playlist or None if not found.
        """
        return self.repository.get_playlist_by_nfc_tag(nfc_tag_id)

    def associate_nfc_tag(self, playlist_id: str, nfc_tag_id: str) -> bool:
        """
        Associate an NFC tag with a playlist.

        Args:
            playlist_id: Playlist ID.
            nfc_tag_id: NFC tag ID to associate.
        Returns:
            True if the association succeeded, False otherwise.
        """
        return self.repository.associate_nfc_tag(playlist_id, nfc_tag_id)

    def disassociate_nfc_tag(self, playlist_id: str) -> bool:
        """
        Remove the association of an NFC tag from a playlist.

        Args:
            playlist_id: Playlist ID.
        Returns:
            True if the dissociation succeeded, False otherwise.
        """
        return self.repository.disassociate_nfc_tag(playlist_id)

    def create_playlist_from_folder(
        self, folder_path: Path, title: Optional[str] = None
    ) -> Optional[str]:
        """Create a playlist from a folder of audio files.

        This scans the specified folder for supported audio files
        and creates a new playlist entry in the database, with each file as a track.
        The playlist's relative path is determined with respect to the uploads folder.

        Args:
            folder_path: Path to the folder
            title: Optional title for the playlist (default: folder name)

        Returns:
            ID of the created playlist or None if an error occurred
        """
        try:
            # Check if the folder exists and is a directory
            if not folder_path.exists() or not folder_path.is_dir():
                logger.log(LogLevel.ERROR, f"Folder does not exist: {folder_path}")
                return None

            # Retrieve audio files in the folder
            audio_files = [
                f
                for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_AUDIO_EXTENSIONS
            ]

            # Check if there are any audio files
            if not audio_files:
                logger.log(LogLevel.WARNING, f"No audio files found in folder: {folder_path}")
                return None

            # Determine the relative path with respect to the parent of the uploads
            # folder
            rel_path = folder_path.relative_to(self.upload_folder.parent)

            # Initialize the playlist data
            playlist_data = {
                "id": str(uuid4()),
                "type": "playlist",
                "title": title or folder_path.name,
                "path": str(rel_path),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "tracks": [],
            }

            # Use UploadService to extract metadata for each audio file
            from app.src.services.upload_service import UploadService

            upload_service = UploadService(str(self.upload_folder))

            for i, file_path in enumerate(sorted(audio_files), 1):
                metadata = upload_service.extract_metadata(file_path)
                track = {
                    "number": i,
                    "title": metadata.get("title", file_path.stem),
                    "filename": file_path.name,
                    "duration": metadata.get("duration", 0),
                    "artist": metadata.get("artist", "Unknown"),
                    "album": metadata.get("album", "Unknown"),
                    "play_counter": 0,
                }
                playlist_data["tracks"].append(track)

            # Create the playlist in the repository
            return self.repository.create_playlist(playlist_data)

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error creating playlist from folder: {str(e)}")
            return None

    def update_playlist_tracks(
        self, playlist_id: str, folder_path: Path
    ) -> Tuple[bool, Dict[str, int]]:
        """Update the tracks of a playlist from the contents of a folder.

        This method compares the current tracks in the playlist with the audio files
        present in the specified folder. It adds new tracks for new files,
        removes tracks for missing files, and keeps existing tracks that are still present.
        The playlist is then updated in the repository.

        Args:
            playlist_id: Playlist ID
            folder_path: Path to the folder

        Returns:
            Tuple (success, statistics)
        """
        stats = {"added": 0, "removed": 0}

        try:
            # Retrieve the existing playlist
            playlist = self.repository.get_playlist_by_id(playlist_id)
            if not playlist:
                logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
                return False, stats

            # Retrieve audio files in the folder
            audio_files = [
                f
                for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_AUDIO_EXTENSIONS
            ]

            # Create dictionaries for comparison
            existing_tracks = {t["filename"]: t for t in playlist.get("tracks", [])}
            disk_files_map = {f.name: f for f in audio_files}

            # Identify modifications
            to_remove = set(existing_tracks.keys()) - set(disk_files_map.keys())
            to_add = set(disk_files_map.keys()) - set(existing_tracks.keys())

            # Prepare new tracks
            new_tracks = []
            track_number = 1

            # (Line 274 intentionally left blank for separation)

            # Keep existing tracks that are still present
            for filename, track in existing_tracks.items():
                if filename not in to_remove:
                    track_copy = dict(track)
                    track_copy["number"] = track_number
                    new_tracks.append(track_copy)
                    track_number += 1

            # Add new tracks
            for filename in sorted(to_add):
                file_path = disk_files_map[filename]
                new_track = {
                    "number": track_number,
                    "title": file_path.stem,
                    "filename": filename,
                    "duration": "",
                    "artist": "Unknown",
                    "album": "Unknown",
                    "play_counter": 0,
                }
                new_tracks.append(new_track)
                track_number += 1

            # Update the playlist
            if self.repository.replace_tracks(playlist_id, new_tracks):
                stats["added"] = len(to_add)
                stats["removed"] = len(to_remove)
                logger.log(
                    LogLevel.INFO,
                    (
                        f"Updated playlist {playlist_id}: added {stats['added']}, "
                        f"removed {stats['removed']} tracks"
                    ),
                )
                return True, stats

            return False, stats

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error updating playlist tracks: {str(e)}")
            return False, stats

    def sync_with_filesystem(self) -> Dict[str, int]:
        """Synchronize playlists in the database with the filesystem.

        Returns:
            Synchronization statistics
        """
        with self._sync_lock:  # Prevent concurrent synchronizations
            start_time = time.time()
            stats = {
                "playlists_scanned": 0,
                "playlists_added": 0,
                "playlists_updated": 0,
                "tracks_added": 0,
                "tracks_removed": 0,
            }

            try:
                logger.log(
                    LogLevel.INFO,
                    f"Starting playlist synchronization with {self.upload_folder}",
                )

                # 1. Check that the uploads folder exists
                if not self.upload_folder.exists():
                    self.upload_folder.mkdir(parents=True, exist_ok=True)
                    logger.log(LogLevel.INFO, f"Created upload folder: {self.upload_folder}")

                # 2. Retrieve existing playlists
                db_playlists = self.repository.get_all_playlists()
                db_playlists_by_path = {p.get("path", ""): p for p in db_playlists}

                # 3. Scan the filesystem with timeout
                disk_playlists = self._scan_filesystem_with_timeout()

                # 4. Iterate through existing playlists to update them
                self._update_existing_playlists(db_playlists, disk_playlists, stats)

                # 5. Add new playlists
                if time.time() - start_time < self.SYNC_TOTAL_TIMEOUT:
                    self._add_new_playlists(disk_playlists, db_playlists_by_path, stats)
                else:
                    logger.log(LogLevel.WARNING, "Skipping new playlists due to timeout")

                elapsed = time.time() - start_time
                logger.log(
                    LogLevel.INFO,
                    f"Playlist sync completed in {elapsed:.2f}s",
                    extra=stats,
                )
                return stats

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error during playlist synchronization: {str(e)}")
                import traceback

                logger.log(LogLevel.DEBUG, f"Sync error details: {traceback.format_exc()}")
                return stats

    def _scan_filesystem_with_timeout(self) -> Dict[str, List[Path]]:
        """Scan the filesystem with protection against timeouts.

        Returns:
            Dictionary mapping playlist paths to audio files
        """
        result = {}
        scan_start = time.time()

        try:
            for item in self.upload_folder.iterdir():
                # Check global timeout
                if time.time() - scan_start > self.SYNC_FOLDER_TIMEOUT:
                    logger.log(
                        LogLevel.WARNING,
                        "Folder scan timeout, processing items scanned so far",
                    )
                    break

                if item.is_dir():
                    # Relative path with respect to the parent of the uploads folder
                    rel_path = str(item.relative_to(self.upload_folder.parent))
                    audio_files = []

                    try:
                        folder_scan_start = time.time()
                        for f in item.iterdir():
                            # Timeout per folder
                            if time.time() - folder_scan_start > self.SYNC_OPERATION_TIMEOUT:
                                logger.log(
                                    LogLevel.WARNING,
                                    f"Partial scan of {rel_path} due to timeout",
                                )
                                break

                            if f.is_file() and f.suffix.lower() in self.SUPPORTED_AUDIO_EXTENSIONS:
                                audio_files.append(f)

                        if audio_files:
                            result[rel_path] = audio_files
                    except Exception as e:
                        logger.log(
                            LogLevel.ERROR,
                            f"Error scanning folder {rel_path}: {str(e)}",
                        )
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error scanning filesystem: {str(e)}")

        return result

    def _update_existing_playlists(
        self,
        db_playlists: List[Dict[str, Any]],
        disk_playlists: Dict[str, List[Path]],
        stats: Dict[str, int],
    ) -> None:
        """Update existing playlists with files from disk.

        Args:
            db_playlists: List of playlists in the database
            disk_playlists: Dictionary of files found on disk
            stats: Dictionary of statistics to update
        """
        start_time = time.time()

        for db_playlist in db_playlists:
            if time.time() - start_time > self.SYNC_TOTAL_TIMEOUT:
                logger.log(LogLevel.WARNING, "Update timeout reached, stopping updates")
                break

            stats["playlists_scanned"] += 1
            path = db_playlist.get("path", "")

            # If the folder no longer exists or is empty, no need to update
            if path not in disk_playlists:
                continue

            # Update with the files found
            disk_files = disk_playlists.get(path, [])
            if disk_files:
                try:
                    success, update_stats = self.update_playlist_tracks(
                        db_playlist["id"], Path(self.upload_folder.parent / path)
                    )
                    if success:
                        stats["playlists_updated"] += 1
                        stats["tracks_added"] += update_stats["added"]
                        stats["tracks_removed"] += update_stats["removed"]
                except Exception as e:
                    logger.log(
                        LogLevel.ERROR,
                        f"Error updating playlist {db_playlist['id']}: {str(e)}",
                    )

    def _add_new_playlists(
        self,
        disk_playlists: Dict[str, List[Path]],
        db_playlists_by_path: Dict[str, Dict[str, Any]],
        stats: Dict[str, int],
    ) -> None:
        """Add new playlists found on disk.

        Args:
            disk_playlists: Dictionary of files found on disk
            db_playlists_by_path: Dictionary of existing playlists by path
            stats: Dictionary of statistics to update
        """
        start_time = time.time()

        for path, files in disk_playlists.items():
            if time.time() - start_time > self.SYNC_TOTAL_TIMEOUT:
                logger.log(LogLevel.WARNING, "New playlists timeout reached, stopping adds")
                break

            # If the playlist already exists, skip to the next
            if path in db_playlists_by_path or not files:
                continue

            try:
                folder_path = Path(self.upload_folder.parent / path)
                playlist_id = self.create_playlist_from_folder(folder_path)
                if playlist_id:
                    stats["playlists_added"] += 1
                    stats["tracks_added"] += len(files)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error creating playlist from {path}: {str(e)}")

    # === Conversion methods ===

    def to_model(self, playlist_data: Dict[str, Any]) -> Playlist:
        """Convert playlist data to a Playlist model object.

        Args:
            playlist_data: Playlist data as a dictionary

        Returns:
            Playlist object
        """
        tracks = []
        for track_data in playlist_data.get("tracks", []):
            file_path = Path(
                self.upload_folder.parent, playlist_data["path"], track_data["filename"]
            )
            track = Track(
                number=track_data["number"],
                title=track_data.get("title", f"Track {track_data['number']}"),
                filename=track_data["filename"],
                path=file_path,
                duration=track_data.get("duration"),
                artist=track_data.get("artist"),
                album=track_data.get("album"),
                id=track_data.get("id"),
            )
            tracks.append(track)

        return Playlist(
            name=playlist_data["title"],
            tracks=tracks,
            description=playlist_data.get("description"),
            id=playlist_data["id"],
            nfc_tag_id=playlist_data.get("nfc_tag_id"),
        )

    def from_model(self, playlist: Playlist) -> Dict[str, Any]:
        """Convert a Playlist model object to a dictionary for storage.

        This function prepares a dictionary representation of the Playlist model,
        suitable for saving to the database. It determines the playlist's
        relative path and serializes all tracks.

        Args:
            playlist (Playlist): The playlist object to convert.

        Returns:
            dict: Dictionary representing the playlist
        """
        # Compute the relative path for the playlist based on the first track's
        # path; fallback to the playlist name if unavailable
        if playlist.tracks and playlist.tracks[0].path:
            folder_path = playlist.tracks[0].path.parent
            try:
                rel_path = folder_path.relative_to(self.upload_folder.parent)
            except ValueError:
                # If failed, use the playlist name as the relative path
                rel_path = Path(self.config.upload_folder) / playlist.name.lower().replace(" ", "_")
        else:
            rel_path = Path(self.config.upload_folder) / playlist.name.lower().replace(" ", "_")

        # Build the playlist dictionary to match the repository format
        playlist_data = {
            "id": playlist.id or str(uuid4()),
            "type": "playlist",
            "title": playlist.name,
            "path": str(rel_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "nfc_tag_id": playlist.nfc_tag_id,
            "tracks": [],
        }

        # Add all tracks from the Playlist model to the dictionary
        for track in playlist.tracks:
            track_data = {
                "number": track.number,
                "title": track.title,
                "filename": track.filename,
                "duration": track.duration,
                "artist": track.artist,
                "album": track.album,
                "play_counter": 0,
            }
            playlist_data["tracks"].append(track_data)

        return playlist_data

    def play_playlist_with_validation(self, playlist_data: Dict[str, Any], audio) -> bool:
        """Play a playlist using the audio player, with validation and metadata
        update.

        Args:
            playlist_data: Dictionary containing playlist data to play.
            audio: Audio player instance.
        Returns:
            True if playback started successfully, False otherwise.
        """
        try:
            playlist_obj = self.to_model(playlist_data)
            if not playlist_obj.tracks:
                logger.log(
                    LogLevel.WARNING,
                    (
                        f"No valid tracks in playlist: "
                        f"{playlist_data.get('title', playlist_data.get('id'))}"
                    )  # This is manually split to stay under 100 chars

                )
                return False
            valid_tracks = [track for track in playlist_obj.tracks if track.path.exists()]
            if not valid_tracks:
                logger.log(
                    LogLevel.WARNING,
                    (
                        f"No accessible tracks in playlist: "
                        f"{playlist_data.get('title', playlist_data.get('id'))}"
                    ),
                )
                return False
            playlist_obj.tracks = valid_tracks
            result = audio.set_playlist(playlist_obj)
            if result:
                logger.log(
                    LogLevel.INFO,
                    f"Started playlist: {playlist_obj.name} with {len(valid_tracks)} tracks",
                )
                self.repository.update_playlist(
                    playlist_data["id"],
                    {"last_played": time.strftime("%Y-%m-%dT%H:%M:%SZ")},
                )
                return True
            else:
                logger.log(LogLevel.WARNING, f"Failed to start playlist: {playlist_obj.name}")
                return False
        except Exception as e:
            import traceback

            logger.log(LogLevel.ERROR, f"Error playing playlist: {str(e)}")
            logger.log(LogLevel.DEBUG, f"Playlist error details: {traceback.format_exc()}")
            return False

    def start_playlist(self, playlist_id: str, audio) -> bool:
        """Start playback of the specified playlist using the provided audio
        system, with validation.

        Args:
            playlist_id: ID of the playlist to play.
            audio: Audio player instance.
        Returns:
            True if playback started successfully, False otherwise.
        """
        playlist_data = self.get_playlist_by_id(playlist_id)
        if not playlist_data:
            logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
            return False
        return self.play_playlist_with_validation(playlist_data, audio)

    def play_track(self, playlist_id: str, track_number: int, audio) -> bool:
        """Play a specific track from a playlist.

        Args:
            playlist_id: ID of the playlist
            track_number: Track number to play
            audio: Audio player instance
        Returns:
            True if playback started successfully, False otherwise.
        """
        playlist_data = self.get_playlist_by_id(playlist_id)
        if not playlist_data or not playlist_data.get("tracks"):
            logger.log(LogLevel.WARNING, f"Playlist or tracks not found for id: {playlist_id}")
            return False
        track = next((t for t in playlist_data["tracks"] if t["number"] == track_number), None)
        if not track:
            logger.log(
                LogLevel.WARNING,
                f"Track {track_number} not found in playlist {playlist_id}",
            )
            return False
        audio.play_track(track_number)
        # Optionnel: mettre à jour le play_counter ou autre info
        return True

    def add_playlist(self, playlist_data: Dict[str, Any]) -> str:
        """Add a new playlist with the provided data.

        This method is used by the YouTube service to create playlists from downloaded content.

        Args:
            playlist_data: Dictionary containing playlist information
                - title: Title of the playlist
                - folder: Path to the folder containing the tracks
                - tracks: List of track information

        Returns:
            ID of the created playlist
        """
        try:
            # Create a basic playlist structure
            playlist_id = str(uuid4())

            # Prepare the playlist data for storage
            formatted_playlist = {
                "id": playlist_id,
                "type": "playlist",
                "title": playlist_data.get("title", "YouTube Download"),
                "path": playlist_data.get("folder", ""),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "youtube_id": playlist_data.get("youtube_id"),
                "tracks": [],
            }

            # Process tracks if available
            tracks = playlist_data.get("tracks", [])
            for i, track_data in enumerate(tracks, 1):
                track = {
                    "number": i,
                    "title": track_data.get("title", f"Track {i}"),
                    "filename": track_data.get("filename", ""),
                    "duration": track_data.get("duration", 0),
                    "artist": track_data.get("artist", "YouTube"),
                    "album": track_data.get("album", formatted_playlist["title"]),
                    "play_counter": 0,
                }
                formatted_playlist["tracks"].append(track)

            # Create the playlist in the repository
            self.repository.create_playlist(formatted_playlist)
            logger.log(
                LogLevel.INFO,
                f"Created playlist from YouTube download: {formatted_playlist['title']}",
            )
            return playlist_id

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error adding playlist from YouTube data: {str(e)}")
            import traceback

            logger.log(LogLevel.DEBUG, f"Add playlist error details: {traceback.format_exc()}")
            raise
