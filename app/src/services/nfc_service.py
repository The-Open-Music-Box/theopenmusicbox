from typing import Optional, Dict, Any, List
import asyncio
from socketio import AsyncServer
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.module.nfc.nfc_handler import NFCHandler

logger = ImprovedLogger(__name__)

class NFCService:
    def __init__(self, socketio: Optional[AsyncServer] = None, nfc_handler: Optional[NFCHandler] = None):
        """
        Initialize the NFC service.

        Args:
            socketio: SocketIO instance for emitting events
            nfc_handler: Optional NFCHandler instance for NFC operations
        """
        self.socketio = socketio
        self.waiting_for_tag = False
        self.current_playlist_id: Optional[str] = None
        self._playlists: List[Dict[str, Any]] = []
        self._nfc_handler = nfc_handler

        # Abonnement au tag_subject pour déclencher la détection de tag
        if self._nfc_handler and hasattr(self._nfc_handler, "tag_subject"):
            self._nfc_handler.tag_subject.subscribe(self._on_tag_subject)

    def _on_tag_subject(self, tag_data):
        tag_id = tag_data['uid'] if isinstance(tag_data, dict) and 'uid' in tag_data else tag_data
        # Lancer la coroutine dans l'event loop
        asyncio.create_task(self.handle_tag_detected(tag_id))

    def load_mapping(self, mapping: List[Dict[str, Any]]) -> None:
        """
        Load the playlist mapping.

        Args:
            mapping: List of playlist dictionaries
        """
        self._playlists = mapping

    async def start_observe(self, playlist_id: Optional[str] = None) -> dict:
        """
        Start observation mode for NFC tag detection without a specific playlist.
        Used for the 'observe' route in the NFC API.
        
        Args:
            playlist_id: Optional ID of the playlist to associate with scanned tag
            
        Returns:
            Dictionary with operation status
        """
        try:
            # Start the hardware first
            if self._nfc_handler:
                await self._nfc_handler.start_nfc_reader()
                logger.log(LogLevel.INFO, "NFC hardware reader started in observation mode")
                
                # Set waiting status
                self.waiting_for_tag = True
                self.current_playlist_id = playlist_id
                
                if self.socketio:
                    await self.socketio.emit('nfc_status', {
                        'type': 'nfc_status',
                        'status': 'observing',
                        'message': 'Observing NFC tags...'
                    })
                
                return {"status": "ok"}
            else:
                logger.log(LogLevel.ERROR, "NFC reader not available for observation mode")
                return {"status": "error", "message": "NFC reader not available"}
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error starting NFC observation: {e}")
            return {"status": "error", "message": str(e)}
            
    async def start_nfc_reader(self) -> None:
        """
        Start the NFC reader hardware (called by the routes).
        This delegates to start_listening with the current playlist ID.
        """
        if not self.current_playlist_id:
            # If there's no current playlist ID, just start the hardware
            if self._nfc_handler:
                try:
                    await self._nfc_handler.start_nfc_reader()
                    logger.log(LogLevel.INFO, "NFC hardware reader started without playlist")
                    return True
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"Error starting NFC hardware: {e}")
                    if self.socketio:
                        await self.socketio.emit('nfc_status', {
                            'type': 'nfc_status',
                            'status': 'error',
                            'message': 'NFC hardware not available'
                        })
                    return False
            return False
        else:
            # Use the existing method if we have a playlist ID
            return await self.start_listening(self.current_playlist_id)
    
    async def start_listening(self, playlist_id: str) -> None:
        """
        Start listening for NFC tag association.

        Args:
            playlist_id: ID of the playlist to associate with scanned tag
        """
        self.waiting_for_tag = True
        self.current_playlist_id = playlist_id
        
        # Start the physical NFC reader if available
        if self._nfc_handler:
            try:
                await self._nfc_handler.start_nfc_reader()
                logger.log(LogLevel.INFO, "NFC hardware reader started")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error starting NFC hardware: {e}")
                if self.socketio:
                    await self.socketio.emit('nfc_status', {
                        'type': 'nfc_status',
                        'status': 'error',
                        'message': 'NFC hardware not available'
                    })
                return
                
        if self.socketio:
            await self.socketio.emit('nfc_status', {
                'type': 'nfc_status',
                'status': 'waiting',
                'message': 'Waiting for NFC tag...'
            })
        logger.log(LogLevel.INFO, f"Started NFC listening for playlist {playlist_id}")

    async def stop_listening(self) -> None:
        """Stop listening for NFC tags"""
        self.waiting_for_tag = False
        self.current_playlist_id = None
        
        # Stop the physical NFC reader if available
        if self._nfc_handler:
            try:
                await self._nfc_handler.stop_nfc_reader()
                logger.log(LogLevel.INFO, "NFC hardware reader stopped")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error stopping NFC hardware: {e}")
                
        if self.socketio:
            await self.socketio.emit('nfc_status', {
                'type': 'nfc_status',
                'status': 'stopped',
                'message': 'NFC reading stopped'
            })
        logger.log(LogLevel.INFO, "Stopped NFC listening")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current NFC service status.
        
        Returns:
            A dictionary with the current NFC status information
        """
        status = {
            "hardware_available": self._nfc_handler is not None,
            "listening": self.waiting_for_tag,
            "current_playlist_id": self.current_playlist_id
        }
        return status
        
    async def handle_tag_detected(self, tag_id: str) -> bool:
        """
        Handle detected NFC tag.

        Args:
            tag_id: Detected NFC tag ID

        Returns:
            True if tag was successfully processed
        """
        logger.log(LogLevel.INFO, f"Tag NFC détecté: {tag_id}")
        if not self.waiting_for_tag:
            return False

        # Check if tag is already associated
        for item in self._playlists:
            if item.get('nfc_tag') == tag_id:
                if self.socketio:
                    await self.socketio.emit('nfc_status', {
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
                if self.socketio:
                    await self.socketio.emit('nfc_status', {
                        'type': 'nfc_status',
                        'status': 'success',
                        'message': f'Tag {tag_id} successfully associated',
                        'tag_id': tag_id,
                        'playlist_id': self.current_playlist_id
                    })
                logger.log(LogLevel.INFO, f"Tag {tag_id} associated with playlist {self.current_playlist_id}")
                # Créer une tâche pour stop_listening car nous ne pouvons pas await directement ici
                asyncio.create_task(self.stop_listening())
                return True

        return False

    def is_listening(self) -> bool:
        """
        Check if service is currently listening for NFC tags.

        Returns:
            True if in listening mode
        """
        return self.waiting_for_tag
        
    @property
    def tag_subject(self):
        """
        Expose the tag_subject from the underlying NFCHandler.
        
        Returns:
            The tag_subject from the NFCHandler, or None if no handler is available
        """
        if self._nfc_handler and hasattr(self._nfc_handler, 'tag_subject'):
            return self._nfc_handler.tag_subject
        return None