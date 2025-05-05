from typing import Dict, Any
import threading
import asyncio
from rx.subject import Subject
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class DownloadNotifier:
    def __init__(self, socketio, download_id: str):
        self.socketio = socketio
        self.download_id = download_id

    def notify(self, status: str, **data):
        self.socketio.emit('download_progress', {
            'download_id': self.download_id,
            'status': status,
            **data
        })
        # await asyncio.sleep(0)  # Optionnel en async, peut être retiré si inutile

class PlaybackEvent:
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data

class PlaybackSubject:
    # Instance statique globale pour référence directe
    _instance = None
    _lock = threading.Lock()
    _socketio = None

    @classmethod
    def set_socketio(cls, socketio):
        cls._socketio = socketio

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = PlaybackSubject()
            return cls._instance

    def __init__(self):
        # RxPy subjects - maintenus pour compatibilité arrière
        # La communication directe Socket.IO est désormais la méthode principale
        self._status_subject = Subject()
        self._progress_subject = Subject()
        self._last_status_event = None
        self._last_progress_event = None
        # Enregistrer cette instance comme instance statique si c'est la première
        with PlaybackSubject._lock:
            if PlaybackSubject._instance is None:
                PlaybackSubject._instance = self

    @property
    def status_stream(self) -> Subject:
        """Stream of playback status events (playing, paused, stopped)"""
        return self._status_subject

    @property
    def progress_stream(self) -> Subject:
        """Stream of track progress events"""
        return self._progress_subject

    def notify_playback_status(self, status: str, playlist_info: Dict = None, track_info: Dict = None):
        """
        Emit a playback status event
        status: 'playing', 'paused', 'stopped'
        playlist_info: information about current playlist
        track_info: information about current track
        """
        try:
            event_data = {
                'status': status,
                'playlist': playlist_info,
                'current_track': track_info
            }
            event = PlaybackEvent('status', event_data)
            self._last_status_event = event

            # 1. Maintenir la compatibilité avec RxPy (pour les composants existants)
            self._status_subject.on_next(event)

            # 2. Méthode principale: Émettre directement via Socket.IO (plus fiable)
            if PlaybackSubject._socketio:
                try:
                    # Émission via Socket.IO en créant une tâche asyncio
                    self._emit_socketio_event('playback_status', event_data)
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"[PlaybackSubject] Error emitting Socket.IO event: {e}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"[PlaybackSubject] Error in notify_playback_status: {e}")

    def notify_track_progress(self, elapsed: float, total: float, track_number: int, track_info: dict = None, playlist_info: dict = None, is_playing: bool = True):
        """
        Emit a track progress event with full info for the frontend
        elapsed: elapsed time in seconds
        total: total duration in seconds
        track_number: track number in playlist
        track_info: dict with track metadata (title, filename, duration, etc.)
        playlist_info: dict with playlist metadata (optional)
        is_playing: bool, if playback is active
        """
        try:
            # Compose frontend-compatible payload (snake_case for frontend)
            event_data = {
                'track': track_info,
                'playlist': playlist_info,
                'current_time': elapsed,
                'duration': total,
                'is_playing': is_playing
            }
            event = PlaybackEvent('progress', event_data)
            self._last_progress_event = event

            # 1. Maintenir la compatibilité avec RxPy (pour les composants existants)
            self._progress_subject.on_next(event)

            # 2. Méthode principale: Émettre directement via Socket.IO (plus fiable)
            if PlaybackSubject._socketio:
                try:
                    # Émission via Socket.IO en créant une tâche asyncio
                    self._emit_socketio_event('track_progress', event_data)
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"[PlaybackSubject] Error emitting Socket.IO event: {e}")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"[PlaybackSubject] Error in notify_track_progress: {e}")

    def get_last_status_event(self):
        return self._last_status_event

    def get_last_progress_event(self):
        return self._last_progress_event

    def _emit_socketio_event(self, event_name, event_data):
        """
        Émet un événement Socket.IO de manière asynchrone sans bloquer.
        Crée une tâche asyncio pour gérer l'émission de l'événement.
        Gère les émissions depuis des threads secondaires sans boucle asyncio.
        """
        if not PlaybackSubject._socketio:
            return

        # Identifier le thread actuel
        current_thread = threading.current_thread()
        thread_name = current_thread.name

        # Dict pour stocker une référence aux données à traiter
        event_to_emit = {
            "name": event_name,
            "data": event_data
        }

        # Méthode auxiliaire pour l'émission asynchrone
        async def async_emit():
            try:
                await PlaybackSubject._socketio.emit(event_to_emit["name"], event_to_emit["data"])
            except Exception as e:
                logger.log(LogLevel.ERROR, f"[PlaybackSubject] Async Socket.IO emit failed: {e}")

        # Gérer selon si thread principal ou secondaire
        try:
            try:
                # Essayer d'obtenir la boucle courante (peut échouer dans thread secondaire)
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si dans une boucle asyncio en cours d'exécution, créer simplement la tâche
                    loop.create_task(async_emit())
                else:
                    # Boucle existante mais pas active (rare)
                    loop.run_until_complete(async_emit())
            except RuntimeError as e:
                # Pas de boucle d'événements dans ce thread, on en crée une nouvelle
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    # Exécuter l'émission avec la nouvelle boucle
                    new_loop.run_until_complete(async_emit())
                finally:
                    # Fermer proprement la boucle
                    new_loop.close()
                    asyncio.set_event_loop(None)
        except Exception as e:
            logger.log(LogLevel.ERROR, f"[PlaybackSubject] Failed to emit Socket.IO event: {e}")
            # Contournement: essayer une émission non-async en dernier recours
            try:
                # Essayer une émission synchrone (non recommandé mais peut fonctionner)
                PlaybackSubject._socketio.emit(event_name, event_data, callback=None)
            except Exception as fallback_error:
                logger.log(LogLevel.ERROR, f"[PlaybackSubject] Even sync emit failed: {fallback_error}")