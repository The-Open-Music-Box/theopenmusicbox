# app/src/core/playlist_controller.py

import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.module.audio_player.audio_interface import AudioPlayerInterface
from src.services.playlist_service import PlaylistService
from src.model.playlist import Playlist
from src.model.track import Track
from src.config import Config

logger = ImprovedLogger(__name__)

class PlaylistController:
    """
    Contrôleur pour gérer l'interaction entre les tags NFC et la lecture des playlists.

    Cette classe fait le lien entre la détection des tags NFC et le système audio pour
    jouer les playlists associées.
    """

    def __init__(self, audio_player: AudioPlayerInterface, playlist_service: PlaylistService, config: Config):
        """
        Initialise le contrôleur de playlists.

        Args:
            audio_player: Interface du lecteur audio
            playlist_service: Service de gestion des playlists
            config: Configuration de l'application
        """
        self._audio = audio_player
        self._playlist_service = playlist_service
        self._current_tag = None
        self._tag_last_seen = 0
        self._pause_threshold = 1.0  # secondes
        self._monitor_thread = None
        self._start_tag_monitor()

    def handle_tag_scanned(self, tag_uid: str) -> None:
        """
        Gère un événement de scan de tag NFC.

        Args:
            tag_uid: Identifiant unique du tag NFC scanné
        """
        try:
            # Mettre à jour le timestamp de dernière détection
            self._tag_last_seen = time.time()

            if tag_uid != self._current_tag or (hasattr(self._audio, 'is_finished') and self._audio.is_finished()):
                # Nouveau tag ou la playlist précédente est terminée
                self._current_tag = tag_uid
                logger.log(LogLevel.INFO, f"Processing tag: {tag_uid}")
                self._process_new_tag(tag_uid)
            elif not self._audio.is_playing and (not hasattr(self._audio, 'is_finished') or not self._audio.is_finished()):
                # Même tag, mais lecture en pause - reprendre
                self._audio.resume()
                logger.log(LogLevel.INFO, f"Resumed playback for tag: {tag_uid}")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error handling tag: {str(e)}")
            import traceback
            logger.log(LogLevel.DEBUG, f"Tag handling error details: {traceback.format_exc()}")

    def _process_new_tag(self, tag_uid: str) -> None:
        """
        Traite un nouveau tag NFC détecté.

        Args:
            tag_uid: Identifiant unique du tag NFC
        """
        try:
            # Récupérer la playlist associée au tag
            playlist_data = self._playlist_service.get_playlist_by_nfc_tag(tag_uid)

            if playlist_data:
                # Jouer la playlist
                self._play_playlist(playlist_data)
                logger.log(LogLevel.INFO, f"Playing playlist for tag: {tag_uid}")
            else:
                logger.log(LogLevel.WARNING, f"No playlist found for tag: {tag_uid}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error processing tag: {str(e)}")

    def _play_playlist(self, playlist_data: Dict[str, Any]) -> None:
        """
        Joue une playlist.

        Args:
            playlist_data: Données de la playlist à jouer
        """
        try:
            # Convertir les données en objet modèle Playlist
            playlist_obj = self._playlist_service.to_model(playlist_data)

            # Vérifier que la playlist contient des pistes valides
            if not playlist_obj.tracks:
                logger.log(LogLevel.WARNING, f"No valid tracks in playlist: {playlist_data['title']}")
                return

            # Filtrer les pistes pour ne garder que celles dont le fichier existe
            valid_tracks = [track for track in playlist_obj.tracks if track.exists]

            if not valid_tracks:
                logger.log(LogLevel.WARNING, f"No accessible tracks in playlist: {playlist_data['title']}")
                return

            # Mettre à jour la liste des pistes avec seulement les pistes valides
            playlist_obj.tracks = valid_tracks

            # Envoyer la playlist au lecteur audio
            result = self._audio.set_playlist(playlist_obj)

            if result:
                logger.log(LogLevel.INFO, f"Started playlist: {playlist_obj.name} with {len(valid_tracks)} tracks")

                # Mettre à jour la date de dernière lecture
                self._playlist_service.repository.update_playlist(
                    playlist_data['id'],
                    {'last_played': time.strftime('%Y-%m-%dT%H:%M:%SZ')}
                )
            else:
                logger.log(LogLevel.WARNING, f"Failed to start playlist: {playlist_obj.name}")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error playing playlist: {str(e)}")
            import traceback
            logger.log(LogLevel.DEBUG, f"Playlist error details: {traceback.format_exc()}")

    def _start_tag_monitor(self) -> None:
        """
        Démarre un thread de surveillance pour détecter le retrait des tags NFC.
        """
        def monitor_tags():
            while True:
                try:
                    if self._current_tag and self._audio and self._audio.is_playing:
                        # Si le tag n'a pas été vu récemment, mettre en pause
                        if time.time() - self._tag_last_seen > self._pause_threshold:
                            self._audio.pause()
                            logger.log(LogLevel.INFO, f"Paused playback for tag: {self._current_tag} (removed)")
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"Error in tag monitoring: {str(e)}")

                # Attendre avant la prochaine vérification
                time.sleep(0.2)

        self._monitor_thread = threading.Thread(target=monitor_tags)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        logger.log(LogLevel.INFO, "Tag monitor thread started")

    def update_playback_status_callback(self, track: Optional[Track] = None, status: str = 'unknown') -> None:
        """
        Callback pour les mises à jour de statut de lecture.

        Args:
            track: Piste en cours de lecture
            status: Statut de lecture (playing, paused, stopped)
        """
        if track and track.id and status == 'playing':
            # Mettre à jour le compteur de lecture
            playlist_id = None

            # Si la piste est dans la playlist actuelle, récupérer l'ID de la playlist
            if self._current_tag:
                playlist_data = self._playlist_service.get_playlist_by_nfc_tag(self._current_tag)
                if playlist_data:
                    playlist_id = playlist_data['id']

            if playlist_id:
                self._playlist_service.repository.update_track_counter(playlist_id, track.number)
                logger.log(LogLevel.DEBUG, f"Updated play counter for track {track.number} in playlist {playlist_id}")