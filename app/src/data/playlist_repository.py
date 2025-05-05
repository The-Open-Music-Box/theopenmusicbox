import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.config import Config

logger = ImprovedLogger(__name__)

class PlaylistRepository:
    """
    Repository for accessing playlist and track data in the database.
    Responsible only for low-level CRUD operations without business logic.
    """

    def __init__(self, config: Config):
        """
        Initializes the repository with the database path from the configuration.

        Args:
            config: Application configuration instance with a 'db_file' attribute.
        Raises:
            AttributeError: If 'db_file' is not found in the config object.
        """
        if not hasattr(config, 'db_file'):
            raise AttributeError("Config object must have a 'db_file' attribute.")
        self.db_path = Path(config.db_file)
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self) -> None:
        """Ensures that the parent directory of the DB exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_db(self) -> None:
        """Initializes the database structure if necessary."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    nfc_tag_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_played TEXT
                )
                ''')

                conn.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id TEXT NOT NULL,
                    number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    duration TEXT,
                    artist TEXT,
                    album TEXT,
                    play_counter INTEGER DEFAULT 0,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
                )
                ''')

                conn.execute('CREATE INDEX IF NOT EXISTS idx_playlists_nfc_tag ON playlists(nfc_tag_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_tracks_playlist ON tracks(playlist_id)')

                conn.commit()
                logger.log(LogLevel.INFO, f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Database initialization failed: {str(e)}")
            raise

    def _dict_factory(self, cursor, row):
        """Converts a SQLite row to a dictionary."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def get_all_playlists(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieves all playlists with their tracks.

        Returns:
            List of dictionaries representing the playlists
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = self._dict_factory
                playlists = conn.execute(
                    "SELECT * FROM playlists LIMIT ? OFFSET ?",
                    (limit, offset)
                ).fetchall()

                for playlist in playlists:
                    playlist['tracks'] = self._get_tracks_for_playlist(conn, playlist['id'], limit, offset)

                return playlists
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error fetching playlists: {str(e)}")
            return []

    def _get_tracks_for_playlist(self, conn, playlist_id: str, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieves the tracks of a playlist.

        Args:
            conn: SQLite connection
            playlist_id: Playlist ID

        Returns:
            List of dictionaries representing the tracks
        """
        return conn.execute(
            "SELECT * FROM tracks WHERE playlist_id = ? ORDER BY number LIMIT ? OFFSET ?",
            (playlist_id, limit, offset)
        ).fetchall()

    def get_playlist_by_id(self, playlist_id: str, track_limit: int = 1000, track_offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Retrieves a playlist by its ID.

        Args:
            playlist_id: Playlist ID

        Returns:
            Dictionary representing the playlist or None if not found
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = self._dict_factory

                playlist = conn.execute(
                    "SELECT * FROM playlists WHERE id = ?",
                    (playlist_id,)
                ).fetchone()

                if not playlist:
                    return None

                playlist['tracks'] = self._get_tracks_for_playlist(conn, playlist_id, limit=track_limit, offset=track_offset)
                return playlist
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error fetching playlist {playlist_id}: {str(e)}")
            return None

    def get_playlist_by_nfc_tag(self, nfc_tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a playlist by its NFC tag.

        Args:
            nfc_tag_id: NFC tag ID

        Returns:
            Dictionary representing the playlist or None if not found
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = self._dict_factory

                playlist = conn.execute(
                    "SELECT * FROM playlists WHERE nfc_tag_id = ?",
                    (nfc_tag_id,)
                ).fetchone()

                if not playlist:
                    return None

                playlist['tracks'] = self._get_tracks_for_playlist(conn, playlist['id'])
                return playlist
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error fetching playlist by NFC tag {nfc_tag_id}: {str(e)}")
            return None

    def create_playlist(self, playlist_data: Dict[str, Any]) -> Optional[str]:
        """
        Creates a new playlist.

        Args:
            playlist_data: Data of the playlist to create

        Returns:
            ID of the created playlist or None in case of error
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Insertion de la playlist
                playlist_id = playlist_data.get('id') or str(uuid4())

                conn.execute(
                    '''
                    INSERT INTO playlists (id, type, nfc_tag_id, title, path, created_at, last_played)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        playlist_id,
                        playlist_data.get('type', 'playlist'),
                        playlist_data.get('nfc_tag_id'),
                        playlist_data['title'],
                        playlist_data['path'],
                        playlist_data.get('created_at', datetime.now(timezone.utc).isoformat()),
                        playlist_data.get('last_played')
                    )
                )

                # Insertion des pistes
                if 'tracks' in playlist_data and playlist_data['tracks']:
                    for track in playlist_data['tracks']:
                        self._insert_track(conn, playlist_id, track)

                conn.commit()
                logger.log(LogLevel.INFO, f"Created playlist: {playlist_data['title']} (ID: {playlist_id})")
                return playlist_id
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error creating playlist: {str(e)}")
            return None

    def _insert_track(self, conn, playlist_id: str, track_data: Dict[str, Any]) -> None:
        """
        Inserts a track into the database.

        Args:
            conn: SQLite connection
            playlist_id: Playlist ID
            track_data: Data of the track
        """
        conn.execute(
            '''
            INSERT INTO tracks (playlist_id, number, title, filename, duration, artist, album, play_counter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                playlist_id,
                track_data['number'],
                track_data.get('title', f"Track {track_data['number']}"),
                track_data['filename'],
                track_data.get('duration', ''),
                track_data.get('artist', 'Unknown'),
                track_data.get('album', 'Unknown'),
                track_data.get('play_counter', 0)
            )
        )

    def update_playlist(self, playlist_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Updates the information of a playlist.

        Args:
            playlist_id: Playlist ID
            updated_data: Data to update

        Returns:
            True if the update succeeded, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Check that the playlist exists
                playlist = conn.execute(
                    "SELECT id FROM playlists WHERE id = ?",
                    (playlist_id,)
                ).fetchone()

                if not playlist:
                    logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
                    return False

                # Mise à jour des champs autorisés
                allowed_fields = ['title', 'nfc_tag_id', 'last_played']
                update_parts = []
                params = []

                for field in allowed_fields:
                    if field in updated_data:
                        update_parts.append(f"{field} = ?")
                        params.append(updated_data[field])

                if update_parts:
                    query = f"UPDATE playlists SET {', '.join(update_parts)} WHERE id = ?"
                    params.append(playlist_id)
                    conn.execute(query, params)
                    conn.commit()
                    logger.log(LogLevel.INFO, f"Updated playlist: {playlist_id}")
                    return True

                return False
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error updating playlist {playlist_id}: {str(e)}")
            return False

    def replace_tracks(self, playlist_id: str, tracks: List[Dict[str, Any]]) -> bool:
        """
        Replaces all tracks of a playlist.

        Args:
            playlist_id: Playlist ID
            tracks: List of new tracks

        Returns:
            True if the replacement succeeded, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Check that the playlist exists
                playlist = conn.execute(
                    "SELECT id FROM playlists WHERE id = ?",
                    (playlist_id,)
                ).fetchone()

                if not playlist:
                    logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
                    return False

                # Supprimer les pistes existantes
                conn.execute("DELETE FROM tracks WHERE playlist_id = ?", (playlist_id,))

                # Insérer les nouvelles pistes
                for track in tracks:
                    self._insert_track(conn, playlist_id, track)

                conn.commit()
                logger.log(LogLevel.INFO, f"Replaced tracks for playlist {playlist_id} ({len(tracks)} tracks)")
                return True
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error replacing tracks for playlist {playlist_id}: {str(e)}")
            return False

    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Deletes a playlist and all its tracks.

        Args:
            playlist_id: Playlist ID

        Returns:
            True if the deletion succeeded, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Check that the playlist exists
                playlist = conn.execute(
                    "SELECT id FROM playlists WHERE id = ?",
                    (playlist_id,)
                ).fetchone()

                if not playlist:
                    logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
                    return False

                # Delete the playlist (cascade deletion will remove the tracks)
                conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
                conn.commit()
                logger.log(LogLevel.INFO, f"Deleted playlist: {playlist_id}")
                return True
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error deleting playlist {playlist_id}: {str(e)}")
            return False

    def update_track_counter(self, playlist_id: str, track_number: int) -> bool:
        """
        Increments the play counter of a track.

        Args:
            playlist_id: Playlist ID
            track_number: Track number

        Returns:
            True if the update succeeded, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "UPDATE tracks SET play_counter = play_counter + 1 WHERE playlist_id = ? AND number = ?",
                    (playlist_id, track_number)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error updating track counter: {str(e)}")
            return False

    def associate_nfc_tag(self, playlist_id: str, nfc_tag_id: str) -> bool:
        """
        Associates an NFC tag with a playlist.

        Args:
            playlist_id: Playlist ID
            nfc_tag_id: NFC tag ID

        Returns:
            True if the association succeeded, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Check if the tag is already associated with another playlist
                existing = conn.execute(
                    "SELECT id FROM playlists WHERE nfc_tag_id = ? AND id != ?",
                    (nfc_tag_id, playlist_id)
                ).fetchone()

                if existing:
                    logger.log(LogLevel.WARNING, f"NFC tag {nfc_tag_id} already associated with playlist {existing[0]}")
                    return False

                # Associate the tag with the playlist
                conn.execute(
                    "UPDATE playlists SET nfc_tag_id = ? WHERE id = ?",
                    (nfc_tag_id, playlist_id)
                )
                conn.commit()
                logger.log(LogLevel.INFO, f"Associated NFC tag {nfc_tag_id} with playlist {playlist_id}")
                return True
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error associating NFC tag: {str(e)}")
            return False

    def disassociate_nfc_tag(self, playlist_id: str) -> bool:
        """
        Removes the association of an NFC tag with a playlist.

        Args:
            playlist_id: Playlist ID

        Returns:
            True if the disassociation succeeded, False otherwise
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    "UPDATE playlists SET nfc_tag_id = NULL WHERE id = ?",
                    (playlist_id,)
                )
                conn.commit()
                logger.log(LogLevel.INFO, f"Disassociated NFC tag from playlist {playlist_id}")
                return True
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error disassociating NFC tag: {str(e)}")
            return False