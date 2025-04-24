# app/src/services/playlist_service.py

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import uuid4
from datetime import datetime, timezone
import threading

from src.config import Config
from src.data.playlist_repository import PlaylistRepository
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.model.playlist import Playlist
from src.model.track import Track

logger = ImprovedLogger(__name__)

class PlaylistService:
    """
    Service pour la gestion des playlists avec logique métier.

    Ce service sert d'intermédiaire entre la couche présentation
    et la couche d'accès aux données pour les opérations liées aux playlists.
    """

    # Extensions de fichiers audio supportées
    SUPPORTED_AUDIO_EXTENSIONS = {'.mp3', '.ogg', '.wav', '.m4a', '.flac', '.aac'}

    # Timeouts pour la synchronisation (en secondes)
    SYNC_TOTAL_TIMEOUT = 10.0
    SYNC_FOLDER_TIMEOUT = 1.0
    SYNC_OPERATION_TIMEOUT = 2.0

    def __init__(self, config: Config):
        """
        Initialise le service de playlists.

        Args:
            config: Configuration de l'application
        """
        self.config = config
        self.repository = PlaylistRepository(config)
        self.upload_folder = Path(config.upload_folder)
        self._sync_lock = threading.RLock()

    def get_all_playlists(self, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère toutes les playlists.

        Returns:
            Liste de dictionnaires représentant les playlists
        """
        offset = (page - 1) * page_size
        return self.repository.get_all_playlists(limit=page_size, offset=offset)

    def get_playlist_by_id(self, playlist_id: str, track_page: int = 1, track_page_size: int = 1000) -> Optional[Dict[str, Any]]:
        """
        Récupère une playlist par son ID.

        Args:
            playlist_id: ID de la playlist

        Returns:
            Dictionnaire représentant la playlist ou None si non trouvée
        """
        track_offset = (track_page - 1) * track_page_size
        return self.repository.get_playlist_by_id(playlist_id, track_limit=track_page_size, track_offset=track_offset)

    def get_playlist_by_nfc_tag(self, nfc_tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une playlist par son tag NFC.

        Args:
            nfc_tag_id: ID du tag NFC

        Returns:
            Dictionnaire représentant la playlist ou None si non trouvée
        """
        return self.repository.get_playlist_by_nfc_tag(nfc_tag_id)

    def associate_nfc_tag(self, playlist_id: str, nfc_tag_id: str) -> bool:
        """
        Associe un tag NFC à une playlist.

        Args:
            playlist_id: ID de la playlist
            nfc_tag_id: ID du tag NFC

        Returns:
            True si l'association a réussi, False sinon
        """
        return self.repository.associate_nfc_tag(playlist_id, nfc_tag_id)

    def disassociate_nfc_tag(self, playlist_id: str) -> bool:
        """
        Supprime l'association d'un tag NFC avec une playlist.

        Args:
            playlist_id: ID de la playlist

        Returns:
            True si la dissociation a réussi, False sinon
        """
        return self.repository.disassociate_nfc_tag(playlist_id)

    def create_playlist_from_folder(self, folder_path: Path, title: Optional[str] = None) -> Optional[str]:
        """
        Crée une playlist à partir d'un dossier de fichiers audio.

        Args:
            folder_path: Chemin vers le dossier
            title: Titre optionnel pour la playlist (par défaut: nom du dossier)

        Returns:
            ID de la playlist créée ou None en cas d'erreur
        """
        try:
            if not folder_path.exists() or not folder_path.is_dir():
                logger.log(LogLevel.ERROR, f"Folder does not exist: {folder_path}")
                return None

            # Récupérer les fichiers audio dans le dossier
            audio_files = [
                f for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_AUDIO_EXTENSIONS
            ]

            if not audio_files:
                logger.log(LogLevel.WARNING, f"No audio files found in folder: {folder_path}")
                return None

            # Déterminer le chemin relatif par rapport au dossier d'uploads
            rel_path = folder_path.relative_to(self.upload_folder.parent)

            # Créer la playlist
            playlist_data = {
                'id': str(uuid4()),
                'type': 'playlist',
                'title': title or folder_path.name,
                'path': str(rel_path),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'tracks': []
            }

            # Ajouter les pistes
            for i, file_path in enumerate(sorted(audio_files), 1):
                track = {
                    'number': i,
                    'title': file_path.stem,
                    'filename': file_path.name,
                    'duration': '',
                    'artist': 'Unknown',
                    'album': 'Unknown',
                    'play_counter': 0
                }
                playlist_data['tracks'].append(track)

            # Enregistrer la playlist
            return self.repository.create_playlist(playlist_data)

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error creating playlist from folder: {str(e)}")
            return None

    def update_playlist_tracks(self, playlist_id: str, folder_path: Path) -> Tuple[bool, Dict[str, int]]:
        """
        Met à jour les pistes d'une playlist à partir du contenu d'un dossier.

        Args:
            playlist_id: ID de la playlist
            folder_path: Chemin vers le dossier

        Returns:
            Tuple (succès, statistiques)
        """
        stats = {'added': 0, 'removed': 0}

        try:
            # Récupérer la playlist existante
            playlist = self.repository.get_playlist_by_id(playlist_id)
            if not playlist:
                logger.log(LogLevel.WARNING, f"Playlist not found: {playlist_id}")
                return False, stats

            # Récupérer les fichiers audio dans le dossier
            audio_files = [
                f for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_AUDIO_EXTENSIONS
            ]

            # Créer des dictionnaires pour la comparaison
            existing_tracks = {t['filename']: t for t in playlist.get('tracks', [])}
            disk_files_map = {f.name: f for f in audio_files}

            # Identifier les modifications
            to_remove = set(existing_tracks.keys()) - set(disk_files_map.keys())
            to_add = set(disk_files_map.keys()) - set(existing_tracks.keys())

            # Préparer les nouvelles pistes
            new_tracks = []
            track_number = 1

            # Conserver les pistes existantes qui sont toujours présentes
            for filename, track in existing_tracks.items():
                if filename not in to_remove:
                    track_copy = dict(track)
                    track_copy['number'] = track_number
                    new_tracks.append(track_copy)
                    track_number += 1

            # Ajouter les nouvelles pistes
            for filename in sorted(to_add):
                file_path = disk_files_map[filename]
                new_track = {
                    'number': track_number,
                    'title': file_path.stem,
                    'filename': filename,
                    'duration': '',
                    'artist': 'Unknown',
                    'album': 'Unknown',
                    'play_counter': 0
                }
                new_tracks.append(new_track)
                track_number += 1

            # Mettre à jour la playlist
            if self.repository.replace_tracks(playlist_id, new_tracks):
                stats['added'] = len(to_add)
                stats['removed'] = len(to_remove)
                logger.log(LogLevel.INFO, f"Updated playlist {playlist_id}: added {stats['added']}, removed {stats['removed']} tracks")
                return True, stats

            return False, stats

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error updating playlist tracks: {str(e)}")
            return False, stats

    def sync_with_filesystem(self) -> Dict[str, int]:
        """
        Synchronise les playlists en base de données avec le système de fichiers.

        Returns:
            Statistiques de synchronisation
        """
        with self._sync_lock:  # Éviter les synchronisations concurrentes
            start_time = time.time()
            stats = {
                'playlists_scanned': 0,
                'playlists_added': 0,
                'playlists_updated': 0,
                'tracks_added': 0,
                'tracks_removed': 0
            }

            try:
                logger.log(LogLevel.INFO, f"Starting playlist synchronization with {self.upload_folder}")

                # 1. Vérifier que le dossier d'uploads existe
                if not self.upload_folder.exists():
                    self.upload_folder.mkdir(parents=True, exist_ok=True)
                    logger.log(LogLevel.INFO, f"Created upload folder: {self.upload_folder}")

                # 2. Récupérer les playlists existantes
                db_playlists = self.repository.get_all_playlists()
                db_playlists_by_path = {p.get('path', ''): p for p in db_playlists}

                # 3. Scanner le système de fichiers avec timeout
                disk_playlists = self._scan_filesystem_with_timeout()

                # 4. Parcourir les playlists existantes pour les mettre à jour
                self._update_existing_playlists(db_playlists, disk_playlists, stats)

                # 5. Ajouter les nouvelles playlists
                if time.time() - start_time < self.SYNC_TOTAL_TIMEOUT:
                    self._add_new_playlists(disk_playlists, db_playlists_by_path, stats)
                else:
                    logger.log(LogLevel.WARNING, "Skipping new playlists due to timeout")

                elapsed = time.time() - start_time
                logger.log(LogLevel.INFO, f"Playlist sync completed in {elapsed:.2f}s", extra=stats)
                return stats

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error during playlist synchronization: {str(e)}")
                import traceback
                logger.log(LogLevel.DEBUG, f"Sync error details: {traceback.format_exc()}")
                return stats

    def _scan_filesystem_with_timeout(self) -> Dict[str, List[Path]]:
        """
        Scanne le système de fichiers avec une protection contre les timeouts.

        Returns:
            Dictionnaire associant les chemins des playlists aux fichiers audio
        """
        result = {}
        scan_start = time.time()

        try:
            for item in self.upload_folder.iterdir():
                # Vérifier le timeout global
                if time.time() - scan_start > self.SYNC_FOLDER_TIMEOUT:
                    logger.log(LogLevel.WARNING, "Folder scan timeout, processing items scanned so far")
                    break

                if item.is_dir():
                    # Chemin relatif par rapport au dossier parent du dossier d'uploads
                    rel_path = str(item.relative_to(self.upload_folder.parent))
                    audio_files = []

                    try:
                        folder_scan_start = time.time()
                        for f in item.iterdir():
                            # Timeout par dossier
                            if time.time() - folder_scan_start > self.SYNC_OPERATION_TIMEOUT:
                                logger.log(LogLevel.WARNING, f"Partial scan of {rel_path} due to timeout")
                                break

                            if f.is_file() and f.suffix.lower() in self.SUPPORTED_AUDIO_EXTENSIONS:
                                audio_files.append(f)

                        if audio_files:
                            result[rel_path] = audio_files
                    except Exception as e:
                        logger.log(LogLevel.ERROR, f"Error scanning folder {rel_path}: {str(e)}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error scanning filesystem: {str(e)}")

        return result

    def _update_existing_playlists(self, db_playlists: List[Dict[str, Any]],
                                  disk_playlists: Dict[str, List[Path]],
                                  stats: Dict[str, int]) -> None:
        """
        Met à jour les playlists existantes avec les fichiers du disque.

        Args:
            db_playlists: Liste des playlists en base de données
            disk_playlists: Dictionnaire des fichiers trouvés sur le disque
            stats: Dictionnaire des statistiques à mettre à jour
        """
        start_time = time.time()

        for db_playlist in db_playlists:
            if time.time() - start_time > self.SYNC_TOTAL_TIMEOUT:
                logger.log(LogLevel.WARNING, "Update timeout reached, stopping updates")
                break

            stats['playlists_scanned'] += 1
            path = db_playlist.get('path', '')

            # Si le dossier n'existe plus ou est vide, pas besoin de mettre à jour
            if path not in disk_playlists:
                continue

            # Mettre à jour avec les fichiers trouvés
            disk_files = disk_playlists.get(path, [])
            if disk_files:
                try:
                    success, update_stats = self.update_playlist_tracks(db_playlist['id'], Path(self.upload_folder.parent / path))
                    if success:
                        stats['playlists_updated'] += 1
                        stats['tracks_added'] += update_stats['added']
                        stats['tracks_removed'] += update_stats['removed']
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"Error updating playlist {db_playlist['id']}: {str(e)}")

    def _add_new_playlists(self, disk_playlists: Dict[str, List[Path]],
                           db_playlists_by_path: Dict[str, Dict[str, Any]],
                           stats: Dict[str, int]) -> None:
        """
        Ajoute les nouvelles playlists trouvées sur le disque.

        Args:
            disk_playlists: Dictionnaire des fichiers trouvés sur le disque
            db_playlists_by_path: Dictionnaire des playlists existantes par chemin
            stats: Dictionnaire des statistiques à mettre à jour
        """
        start_time = time.time()

        for path, files in disk_playlists.items():
            if time.time() - start_time > self.SYNC_TOTAL_TIMEOUT:
                logger.log(LogLevel.WARNING, "New playlists timeout reached, stopping adds")
                break

            # Si la playlist existe déjà, passer à la suivante
            if path in db_playlists_by_path or not files:
                continue

            try:
                folder_path = Path(self.upload_folder.parent / path)
                playlist_id = self.create_playlist_from_folder(folder_path)
                if playlist_id:
                    stats['playlists_added'] += 1
                    stats['tracks_added'] += len(files)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error creating playlist from {path}: {str(e)}")

    # === Méthodes de conversion ===

    def to_model(self, playlist_data: Dict[str, Any]) -> Playlist:
        """
        Convertit les données de playlist en objet modèle Playlist.

        Args:
            playlist_data: Données de playlist au format dictionnaire

        Returns:
            Objet Playlist
        """
        tracks = []
        for track_data in playlist_data.get('tracks', []):
            file_path = Path(self.upload_folder.parent / playlist_data['path'] / track_data['filename'])
            track = Track(
                number=track_data['number'],
                title=track_data.get('title', f"Track {track_data['number']}"),
                filename=track_data['filename'],
                path=file_path,
                duration=track_data.get('duration'),
                artist=track_data.get('artist'),
                album=track_data.get('album'),
                id=track_data.get('id')
            )
            tracks.append(track)

        return Playlist(
            name=playlist_data['title'],
            tracks=tracks,
            description=playlist_data.get('description'),
            id=playlist_data['id'],
            nfc_tag_id=playlist_data.get('nfc_tag_id')
        )

    def from_model(self, playlist: Playlist) -> Dict[str, Any]:
        """
        Convertit un objet modèle Playlist en dictionnaire.

        Args:
            playlist: Objet Playlist

        Returns:
            Dictionnaire représentant la playlist
        """
        # Déterminer le chemin relatif par rapport au dossier d'uploads
        if playlist.tracks and playlist.tracks[0].path:
            folder_path = playlist.tracks[0].path.parent
            try:
                rel_path = folder_path.relative_to(self.upload_folder.parent)
            except ValueError:
                # En cas d'échec, utiliser le nom de la playlist comme chemin relatif
                rel_path = Path('uploads') / playlist.name.lower().replace(' ', '_')
        else:
            rel_path = Path('uploads') / playlist.name.lower().replace(' ', '_')

        # Créer le dictionnaire de playlist
        playlist_data = {
            'id': playlist.id or str(uuid4()),
            'type': 'playlist',
            'title': playlist.name,
            'path': str(rel_path),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'nfc_tag_id': playlist.nfc_tag_id,
            'tracks': []
        }

        # Ajouter les pistes
        for track in playlist.tracks:
            track_data = {
                'number': track.number,
                'title': track.title,
                'filename': track.filename,
                'duration': track.duration,
                'artist': track.artist,
                'album': track.album,
                'play_counter': 0
            }
            playlist_data['tracks'].append(track_data)

        return playlist_data