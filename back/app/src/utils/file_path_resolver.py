"""
File path resolution utility for audio tracks and playlists.

This module provides centralized logic for resolving file paths across the application,
ensuring consistent path handling and separation of concerns.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from app.src.config import Config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class FilePathResolver:
    """Utility class for resolving file paths for tracks and playlists."""
    
    def __init__(self, config: Config):
        """Initialize the file path resolver with configuration."""
        self.config = config
        self.upload_folder = Path(config.upload_folder)
    
    def resolve_track_file_path(self, track: Dict[str, Any], playlist: Dict[str, Any]) -> Optional[Path]:
        """
        Resolve the full file path for a track.
        
        Args:
            track: Track dictionary containing filename and optional path
            playlist: Playlist dictionary containing path information
            
        Returns:
            Path object if resolved successfully, None otherwise
        """
        try:
            # Method 1: Direct path in track
            if "path" in track and track["path"]:
                file_path = Path(track["path"])
                if file_path.is_absolute():
                    return file_path
                return self.upload_folder / file_path
            
            # Method 2: Track filename with playlist folder
            if "filename" in track and "folder" in playlist:
                return Path(playlist["folder"]) / track["filename"]
            
            # Method 3: Track filename with playlist path
            if "filename" in track and "path" in playlist:
                playlist_relative_path = Path(playlist["path"])
                
                # Normalize playlist path - remove 'uploads/' prefix if present
                # since upload_folder already points to uploads directory
                playlist_relative_path = self._normalize_playlist_path(playlist_relative_path)
                
                return self.upload_folder / playlist_relative_path / track["filename"]
            
            logger.log(
                LogLevel.WARNING,
                f"Unable to resolve file path for track: {track.get('filename', 'unknown')}"
            )
            return None
            
        except (ValueError, OSError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Error resolving file path for track {track.get('filename', 'unknown')}: {e}"
            )
            return None
    
    def _normalize_playlist_path(self, playlist_path: Path) -> Path:
        """
        Normalize playlist path by removing redundant 'uploads/' prefix.
        
        Args:
            playlist_path: Raw playlist path from database
            
        Returns:
            Normalized path relative to upload folder
        """
        # Remove 'uploads/' prefix if present since upload_folder already points to uploads
        if playlist_path.parts and playlist_path.parts[0] == "uploads":
            return Path(*playlist_path.parts[1:])
        return playlist_path
    
    def resolve_playlist_folder_path(self, playlist: Dict[str, Any]) -> Optional[Path]:
        """
        Resolve the full folder path for a playlist.
        
        Args:
            playlist: Playlist dictionary containing path information
            
        Returns:
            Path object if resolved successfully, None otherwise
        """
        try:
            if "path" in playlist:
                playlist_relative_path = Path(playlist["path"])
                playlist_relative_path = self._normalize_playlist_path(playlist_relative_path)
                return self.upload_folder / playlist_relative_path
            
            if "folder" in playlist:
                folder_path = Path(playlist["folder"])
                if folder_path.is_absolute():
                    return folder_path
                return self.upload_folder / folder_path
            
            logger.log(
                LogLevel.WARNING,
                f"Unable to resolve folder path for playlist: {playlist.get('name', 'unknown')}"
            )
            return None
            
        except (ValueError, OSError) as e:
            logger.log(
                LogLevel.ERROR,
                f"Error resolving folder path for playlist {playlist.get('name', 'unknown')}: {e}"
            )
            return None
