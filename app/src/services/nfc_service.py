from typing import Optional, Dict, Any, List
from flask_socketio import SocketIO
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class NFCService:
    def __init__(self, socketio: SocketIO):
        """
        Initialize the NFC service.

        Args:
            socketio: SocketIO instance for emitting events
        """
        self.socketio = socketio
        self.waiting_for_tag = False
        self.current_playlist_id: Optional[str] = None
        self._playlists: List[Dict[str, Any]] = []

    def load_mapping(self, mapping: List[Dict[str, Any]]) -> None:
        """
        Load the playlist mapping.

        Args:
            mapping: List of playlist dictionaries
        """
        self._playlists = mapping

    def start_listening(self, playlist_id: str) -> None:
        """
        Start listening for NFC tag association.

        Args:
            playlist_id: ID of the playlist to associate with scanned tag
        """
        self.waiting_for_tag = True
        self.current_playlist_id = playlist_id
        self.socketio.emit('nfc_status', {
            'type': 'nfc_status',
            'status': 'waiting',
            'message': 'Waiting for NFC tag...'
        })
        logger.log(LogLevel.INFO, f"Started NFC listening for playlist {playlist_id}")

    def stop_listening(self) -> None:
        """Stop listening for NFC tags"""
        self.waiting_for_tag = False
        self.current_playlist_id = None
        self.socketio.emit('nfc_status', {
            'type': 'nfc_status',
            'status': 'stopped',
            'message': 'NFC reading stopped'
        })
        logger.log(LogLevel.INFO, "Stopped NFC listening")

    def handle_tag_detected(self, tag_id: str) -> bool:
        """
        Handle detected NFC tag.

        Args:
            tag_id: Detected NFC tag ID

        Returns:
            True if tag was successfully processed
        """
        if not self.waiting_for_tag:
            return False

        # Check if tag is already associated
        for item in self._playlists:
            if item.get('nfc_tag') == tag_id:
                self.socketio.emit('nfc_status', {
                    'type': 'nfc_status',
                    'status': 'error',
                    'message': 'Tag already associated with another playlist',
                    'tag_id': tag_id
                })
                logger.log(LogLevel.WARNING, f"Tag {tag_id} already associated")
                return False

        # If tag is free, associate it
        if self.current_playlist_id:
            # Find playlist in the mapping
            playlist = next((p for p in self._playlists if p['id'] == self.current_playlist_id), None)
            if playlist:
                playlist['nfc_tag'] = tag_id
                self.socketio.emit('nfc_status', {
                    'type': 'nfc_status',
                    'status': 'success',
                    'message': f'Tag {tag_id} successfully associated',
                    'tag_id': tag_id,
                    'playlist_id': self.current_playlist_id
                })
                logger.log(LogLevel.INFO, f"Tag {tag_id} associated with playlist {self.current_playlist_id}")
                self.stop_listening()
                return True

        return False

    def is_listening(self) -> bool:
        """
        Check if service is currently listening for NFC tags.

        Returns:
            True if in listening mode
        """
        return self.waiting_for_tag