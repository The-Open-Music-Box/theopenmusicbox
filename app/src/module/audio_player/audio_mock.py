# app/src/module/audio_player/audio_mock.py

from pathlib import Path
from typing import List, Optional
import threading
import time
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.audio_player.audio_hardware import AudioPlayerHardware
from app.src.services.notification_service import PlaybackSubject
from app.src.model.track import Track
from app.src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class MockAudioPlayer(AudioPlayerHardware):
    """
    Mock implementation of AudioPlayerHardware for testing and non-hardware environments.
    Simulates playback state and notifies observers as needed.

    Cette implémentation est conçue pour être facilement exploitable dans
    l'environnement de développement et pour les tests unitaires.
    """
    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        super().__init__(playback_subject)
        # Always set _playback_subject for compatibility with AudioPlayer interface
        self._playback_subject = playback_subject
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        self._volume = 50
        self._progress_thread = None
        self._stop_progress = False
        self._track_duration = 180.0  # Durée simulée en secondes (3 minutes)
        self._track_position = 0.0
        self._track_start_time = 0.0
        logger.log(LogLevel.INFO, "Mock Audio Player initialized")

        # Démarrer le thread de suivi de progression si un playback_subject est fourni
        if playback_subject:
            self._start_progress_thread()

    def load_playlist(self, playlist_path: str) -> bool:
        """Charge une playlist à partir d'un chemin"""
        logger.log(LogLevel.INFO, f"Mock: Loading playlist from {playlist_path}")

        # Simuler le chargement d'une playlist vide
        self._playlist = Playlist(name=Path(playlist_path).stem, tracks=[])
        return True

    def set_playlist(self, playlist: Playlist) -> bool:
        """Définit la playlist courante et démarre la lecture"""
        try:
            self.stop()
            self._playlist = playlist

            if self._playlist and self._playlist.tracks:
                logger.log(LogLevel.INFO, f"Mock: Set playlist with {len(self._playlist.tracks)} tracks")
                return self.play_track(1)  # Jouer la première piste

            logger.log(LogLevel.WARNING, "Mock: Empty playlist or no tracks")
            return False

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Mock: Error setting playlist: {str(e)}")
            return False

    def play_track(self, track_number: int) -> bool:
        """Joue une piste spécifique de la playlist"""
        # Arrêter la lecture en cours sans effacer la playlist
        self.stop(clear_playlist=False)

        if not self._playlist or not self._playlist.tracks:
            logger.log(LogLevel.WARNING, "Mock: No playlist or empty playlist")
            return False

        # Trouver la piste dans la playlist
        track = next((t for t in self._playlist.tracks if t.number == track_number), None)

        # Si on ne trouve pas la piste, créer une piste simulée
        if not track:
            if track_number <= len(self._playlist.tracks):
                track = self._playlist.tracks[track_number-1]
            else:
                logger.log(LogLevel.WARNING, f"Mock: Track number {track_number} not found in playlist")
                # Créer une piste mock pour les tests
                track = Track(
                    number=track_number,
                    title=f"Mock Track {track_number}",
                    filename=f"mock_{track_number}.mp3",
                    path=Path(f"/tmp/mock_{track_number}.mp3")
                )

        self._current_track = track
        self._is_playing = True
        self._track_position = 0.0
        self._track_start_time = time.time()

        # Notifier du changement d'état
        self._notify_playback_status('playing')
        logger.log(LogLevel.INFO, f"Mock: Playing track: {track.title}")

        return True

    def pause(self) -> None:
        """Met en pause la lecture"""
        if self._is_playing:
            self._is_playing = False
            # Stocker la position actuelle pour une reprise ultérieure
            self._track_position = time.time() - self._track_start_time

            # Notifier de la pause
            self._notify_playback_status('paused')
            logger.log(LogLevel.INFO, "Mock: Playback paused")

    def resume(self) -> None:
        """Reprend la lecture"""
        if not self._is_playing and self._current_track:
            self._is_playing = True
            # Ajuster le temps de démarrage pour tenir compte de la position actuelle
            self._track_start_time = time.time() - self._track_position

            # Notifier de la reprise
            self._notify_playback_status('playing')
            logger.log(LogLevel.INFO, "Mock: Playback resumed")

    def stop(self, clear_playlist: bool = True) -> None:
        """Arrête la lecture"""
        was_playing = self._is_playing
        self._is_playing = False
        self._current_track = None
        self._track_position = 0.0

        if clear_playlist:
            self._playlist = None

        if was_playing:
            self._notify_playback_status('stopped')
            logger.log(LogLevel.INFO, "Mock: Playback stopped")

    def next_track(self) -> None:
        """Passe à la piste suivante"""
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "Mock: No current track or playlist")
            return

        next_number = self._current_track.number + 1
        if next_number <= len(self._playlist.tracks):
            logger.log(LogLevel.INFO, f"Mock: Moving to next track: {next_number}")
            self.play_track(next_number)
        else:
            logger.log(LogLevel.INFO, "Mock: Reached end of playlist")
            # Simuler la fin de la playlist
            self.stop()

    def previous_track(self) -> None:
        """Passe à la piste précédente"""
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "Mock: No current track or playlist")
            return

        prev_number = self._current_track.number - 1
        if prev_number > 0:
            logger.log(LogLevel.INFO, f"Mock: Moving to previous track: {prev_number}")
            self.play_track(prev_number)
        else:
            logger.log(LogLevel.INFO, "Mock: Already at first track")

    def set_volume(self, volume: int) -> bool:
        """Règle le volume (0-100)"""
        try:
            self._volume = max(0, min(100, volume))
            logger.log(LogLevel.INFO, f"Mock: Volume set to {self._volume}%")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Mock: Error setting volume: {str(e)}")
            return False

    def get_volume(self) -> int:
        """Retourne le volume actuel"""
        return self._volume

    def get_current_track(self) -> Optional[Track]:
        """Retourne la piste en cours de lecture"""
        return self._current_track

    def get_playlist(self) -> Optional[Playlist]:
        """Retourne la playlist courante"""
        return self._playlist

    @property
    def is_playing(self) -> bool:
        """Retourne True si en cours de lecture"""
        return self._is_playing

    def is_finished(self) -> bool:
        """Retourne True si la playlist est terminée"""
        # Considérer que la playlist est terminée si on n'est plus en train de jouer
        # et qu'on était sur la dernière piste
        if not self._is_playing and self._current_track and self._playlist:
            return self._current_track.number >= len(self._playlist.tracks)
        return False

    def cleanup(self) -> None:
        """Nettoie les ressources"""
        try:
            # Arrêter le thread de progression
            if self._progress_thread:
                self._stop_progress = True
                try:
                    self._progress_thread.join(timeout=2.0)
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Mock: Error stopping progress thread: {str(e)}")

            # Arrêter la lecture
            self.stop()
            logger.log(LogLevel.INFO, "Mock: Resources cleaned up")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Mock: Error during cleanup: {str(e)}")
        finally:
            self._is_playing = False
            self._current_track = None
            self._playlist = None
            self._progress_thread = None

    def _notify_playback_status(self, status: str) -> None:
        """Notifie du changement d'état de lecture"""
        if self._playback_subject:
            playlist_info = None
            track_info = None

            if status != 'stopped':
                if self._playlist:
                    playlist_info = {
                        'name': self._playlist.name,
                        'track_count': len(self._playlist.tracks) if self._playlist.tracks else 0
                    }

                if self._current_track:
                    track_info = {
                        'number': self._current_track.number,
                        'title': self._current_track.title or f'Track {self._current_track.number}',
                        'filename': self._current_track.filename,
                        'duration': self._track_duration
                    }

            self._playback_subject.notify_playback_status(status, playlist_info, track_info)
            logger.log(LogLevel.INFO, "Mock: Playback status update", extra={
                'status': status,
                'playlist': playlist_info,
                'current_track': track_info
            })

    def _start_progress_thread(self) -> None:
        """Démarre le thread de suivi de progression"""
        if self._progress_thread:
            self._stop_progress = True
            self._progress_thread.join(timeout=1.0)

        self._stop_progress = False
        self._progress_thread = threading.Thread(target=self._progress_loop)
        self._progress_thread.daemon = True
        self._progress_thread.start()

    def _progress_loop(self) -> None:
        """Boucle de suivi de progression"""
        last_update_time = 0

        while not self._stop_progress:
            if self._is_playing and self._playback_subject and self._current_track:
                current_time = time.time()

                # Mettre à jour la progression toutes les 500ms
                if current_time - last_update_time >= 0.5:
                    last_update_time = current_time

                    # Calculer la position actuelle
                    elapsed = current_time - self._track_start_time

                    # Si on atteint la fin de la piste, passer à la suivante
                    if elapsed >= self._track_duration:
                        # Simuler la fin de la piste
                        self._handle_track_end()
                    else:
                        # Envoyer la mise à jour
                        self._playback_subject.notify_track_progress(
                            elapsed=elapsed,
                            total=self._track_duration,
                            track_number=self._current_track.number,
                            track_info=track_info,
                            playlist_info=playlist_info,
                            is_playing=self._is_playing
                        )

            # Pause pour éviter de surcharger le CPU
            time.sleep(0.1)

    def _handle_track_end(self) -> None:
        """Gère la fin d'une piste"""
        if self._is_playing and self._current_track and self._playlist:
            next_number = self._current_track.number + 1
            if next_number <= len(self._playlist.tracks):
                logger.log(LogLevel.INFO, f"Mock: Track ended, playing next: {next_number}")
                self.play_track(next_number)
            else:
                logger.log(LogLevel.INFO, "Mock: Playlist ended")
                self.stop()