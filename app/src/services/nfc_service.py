# app/src/services/nfc_service.py

from typing import Optional, Dict, Any
from flask_socketio import SocketIO
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class NFCService:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.waiting_for_tag = False
        self.current_playlist_id: Optional[str] = None
        self._playlists: Dict[str, Any] = {}

    def load_mapping(self, mapping: Dict[str, Any]) -> None:
        """Charge le mapping NFC existant"""
        self._playlists = mapping

    def start_listening(self, playlist_id: str) -> None:
        """Démarre l'écoute pour l'association d'un tag NFC"""
        self.waiting_for_tag = True
        self.current_playlist_id = playlist_id
        self.socketio.emit('nfc_status', {
            'type': 'nfc_status',
            'status': 'waiting',
            'message': 'En attente d\'un tag NFC...'
        })
        logger.log(LogLevel.INFO, f"Démarrage de l'écoute NFC pour la playlist {playlist_id}")

    def stop_listening(self) -> None:
        """Arrête l'écoute NFC"""
        self.waiting_for_tag = False
        self.current_playlist_id = None
        self.socketio.emit('nfc_status', {
            'type': 'nfc_status',
            'status': 'stopped',
            'message': 'Lecture NFC arrêtée'
        })
        logger.log(LogLevel.INFO, "Arrêt de l'écoute NFC")

    def handle_tag_detected(self, tag_id: str) -> bool:
        """Gère la détection d'un tag NFC"""
        if not self.waiting_for_tag:
            return False

        # Vérifie si le tag est déjà associé
        for item in self._playlists:
            if item.get('nfc_tag') == tag_id:
                self.socketio.emit('nfc_status', {
                    'type': 'nfc_status',
                    'status': 'error',
                    'message': f'Tag déjà associé à une autre playlist',
                    'tag_id': tag_id
                })
                logger.log(LogLevel.WARNING, f"Tag {tag_id} déjà associé")
                return False

        # Si le tag est libre, on l'associe
        if self.current_playlist_id:
            # Trouve la playlist dans le mapping
            playlist = next((p for p in self._playlists if p['id'] == self.current_playlist_id), None)
            if playlist:
                playlist['nfc_tag'] = tag_id
                self.socketio.emit('nfc_status', {
                    'type': 'nfc_status',
                    'status': 'success',
                    'message': f'Tag {tag_id} associé avec succès',
                    'tag_id': tag_id,
                    'playlist_id': self.current_playlist_id
                })
                logger.log(LogLevel.INFO, f"Tag {tag_id} associé à la playlist {self.current_playlist_id}")
                self.stop_listening()
                return True

        return False

    def is_listening(self) -> bool:
        """Retourne l'état de l'écoute NFC"""
        return self.waiting_for_tag