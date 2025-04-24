# app/src/data/playlist_repository.py

import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.config import Config

logger = ImprovedLogger(__name__)

class PlaylistRepository:
    """
    Repository pour l'accès aux données des playlists et pistes en base de données.
    Responsable uniquement des opérations CRUD de bas niveau sans logique métier.
    """

    def __init__(self, config: Config):
        """
        Initialise le repository avec le chemin de la base de données depuis la configuration.

        Args:
            config: Instance de configuration de l'application
        """
        self.db_path = Path(config.db_file)
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self) -> None:
        """Assure que le répertoire parent de la DB existe."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_db(self) -> None:
        """Initialise la structure de la base de données si nécessaire."""
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
        """Convertit une ligne SQLite en dictionnaire."""
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    def get_all_playlists(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Récupère toutes les playlists avec leurs pistes.

        Returns:
            Liste de dictionnaires représentant les playlists
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
        Récupère les pistes d'une playlist.

        Args:
            conn: Connexion SQLite
            playlist_id: ID de la playlist

        Returns:
            Liste de dictionnaires représentant les pistes
        """
        return conn.execute(
            "SELECT * FROM tracks WHERE playlist_id = ? ORDER BY number LIMIT ? OFFSET ?",
            (playlist_id, limit, offset)
        ).fetchall()

    def get_playlist_by_id(self, playlist_id: str, track_limit: int = 1000, track_offset: int = 0) -> Optional[Dict[str, Any]]:
        """
        Récupère une playlist par son ID.

        Args:
            playlist_id: ID de la playlist

        Returns:
            Dictionnaire représentant la playlist ou None si non trouvée
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
        Récupère une playlist par son tag NFC.

        Args:
            nfc_tag_id: ID du tag NFC

        Returns:
            Dictionnaire représentant la playlist ou None si non trouvée
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
        Crée une nouvelle playlist.

        Args:
            playlist_data: Données de la playlist à créer

        Returns:
            ID de la playlist créée ou None en cas d'erreur
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
        Insère une piste dans la base de données.

        Args:
            conn: Connexion SQLite
            playlist_id: ID de la playlist
            track_data: Données de la piste
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
        Met à jour les informations d'une playlist.

        Args:
            playlist_id: ID de la playlist
            updated_data: Données à mettre à jour

        Returns:
            True si la mise à jour a réussi, False sinon
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Vérifier que la playlist existe
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
        Remplace toutes les pistes d'une playlist.

        Args:
            playlist_id: ID de la playlist
            tracks: Liste des nouvelles pistes

        Returns:
            True si le remplacement a réussi, False sinon
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Vérifier que la playlist existe
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
        Supprime une playlist et toutes ses pistes.

        Args:
            playlist_id: ID de la playlist

        Returns:
            True si la suppression a réussi, False sinon
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Vérifier que la playlist existe
                playlist = conn.execute(
                    "SELECT id FROM playlists WHERE id = ?",
                    (playlist_id,)
                ).fetchone()

                if not playlist:
                    logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
                    return False

                # Supprimer la playlist (la suppression en cascade supprimera les pistes)
                conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
                conn.commit()
                logger.log(LogLevel.INFO, f"Deleted playlist: {playlist_id}")
                return True
        except sqlite3.Error as e:
            logger.log(LogLevel.ERROR, f"Error deleting playlist {playlist_id}: {str(e)}")
            return False

    def update_track_counter(self, playlist_id: str, track_number: int) -> bool:
        """
        Incrémente le compteur de lectures d'une piste.

        Args:
            playlist_id: ID de la playlist
            track_number: Numéro de la piste

        Returns:
            True si la mise à jour a réussi, False sinon
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
        Associe un tag NFC à une playlist.

        Args:
            playlist_id: ID de la playlist
            nfc_tag_id: ID du tag NFC

        Returns:
            True si l'association a réussi, False sinon
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Vérifier si le tag est déjà associé à une autre playlist
                existing = conn.execute(
                    "SELECT id FROM playlists WHERE nfc_tag_id = ? AND id != ?",
                    (nfc_tag_id, playlist_id)
                ).fetchone()

                if existing:
                    logger.log(LogLevel.WARNING, f"NFC tag {nfc_tag_id} already associated with playlist {existing[0]}")
                    return False

                # Associer le tag à la playlist
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
        Supprime l'association d'un tag NFC avec une playlist.

        Args:
            playlist_id: ID de la playlist

        Returns:
            True si la dissociation a réussi, False sinon
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