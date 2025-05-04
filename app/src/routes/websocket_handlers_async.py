import socketio
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

# Import du PlaybackSubject pour accès direct
from app.src.services.notification_service import PlaybackSubject

logger = ImprovedLogger(__name__)

class WebSocketHandlersAsync:
    def __init__(self, sio: socketio.AsyncServer, app, nfc_service=None):
        self.sio = sio
        self.app = app
        self.nfc_service = nfc_service
        
        # Fournir l'instance de socketio au PlaybackSubject pour la communication directe
        # C'est la seule chose nécessaire maintenant - les événements seront envoyés directement
        PlaybackSubject.set_socketio(self.sio)
        logger.log(LogLevel.INFO, "[WebSocketHandlersAsync] SocketIO instance provided to PlaybackSubject")



    def register(self):
        @self.sio.event
        async def connect(sid, environ):
            logger.log(LogLevel.INFO, f"Client connected: {sid}")
            await self.sio.emit('connection_status', {'status': 'connected', 'sid': sid}, room=sid)
            
            # Utiliser le singleton PlaybackSubject
            playback_subject = PlaybackSubject.get_instance()
            logger.log(LogLevel.INFO, f"[SOCKET.IO] Connect: using PlaybackSubject singleton (id: {id(playback_subject)})")
            
            try:
                # Récupérer et envoyer les derniers événements au client qui vient de se connecter
                status_event = playback_subject.get_last_status_event()
                progress_event = playback_subject.get_last_progress_event()
                
                if status_event:
                    logger.log(LogLevel.INFO, f"[SOCKET.IO] Sending last status to new client: {status_event.data['status']}")
                    # Utiliser await avec les méthodes asynchrones pour s'assurer qu'elles sont exécutées
                    await self.sio.emit('playback_status', status_event.data, room=sid)
                
                if progress_event:
                    current_time = progress_event.data.get('current_time', 0)
                    duration = progress_event.data.get('duration', 0)
                    logger.log(LogLevel.INFO, f"[SOCKET.IO] Sending last progress to new client: {current_time:.1f}/{duration:.1f}")
                    # Utiliser await avec les méthodes asynchrones pour s'assurer qu'elles sont exécutées
                    await self.sio.emit('track_progress', progress_event.data, room=sid)
                    
                # Log de confirmation que les événements ont bien été envoyés
                logger.log(LogLevel.INFO, f"[SOCKET.IO] Initial events sent to client {sid}")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"[SOCKET.IO] Error sending last events to client: {e}")

        @self.sio.event
        async def disconnect(sid):
            logger.log(LogLevel.INFO, f"Client disconnected: {sid}")

        @self.sio.on('set_playlist')
        async def handle_set_playlist(sid, data):
            try:
                logger.log(LogLevel.INFO, f"[SOCKET.IO] set_playlist received: {data}")
                # Reconstruire la playlist mock à partir des données reçues
                from app.src.model.playlist import Playlist
                from app.src.model.track import Track
                playlist = Playlist(
                    id=data.get('id'),
                    name=data.get('name'),
                    tracks=[Track(
                        number=track.get('number'),
                        title=track.get('title'),
                        filename=track.get('filename'),
                        path=track.get('filename'),
                        duration=track.get('duration')
                    ) for track in data.get('tracks', [])]
                )
                # Affecter la playlist au player du container
                player = getattr(self.app.container, 'audio', None)
                if player:
                    player.set_playlist(playlist)
                    await self.sio.emit('playlist_set', {'status': 'ok', 'playlist_id': playlist.id}, room=sid)
                    logger.log(LogLevel.INFO, f"[SOCKET.IO] Playlist set for player: {playlist}")
                else:
                    await self.sio.emit('playlist_set', {'status': 'error', 'message': 'No audio player found'}, room=sid)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"[SOCKET.IO] Error in set_playlist: {str(e)}")
                await self.sio.emit('playlist_set', {'status': 'error', 'message': str(e)}, room=sid)

        @self.sio.on('play_track')
        async def handle_play_track(sid, data):
            try:
                playlist_id = data.get('playlist_id')
                track_number = data.get('track_number')
                logger.log(LogLevel.INFO, f"[SOCKET.IO] play_track received: playlist_id={playlist_id}, track_number={track_number}")
                player = getattr(self.app.container, 'audio', None)
                if player and hasattr(player, 'play_track'):
                    player.play_track(track_number)
                    await self.sio.emit('track_played', {'status': 'ok', 'track_number': track_number}, room=sid)
                    logger.log(LogLevel.INFO, f"[SOCKET.IO] Started playback for track {track_number}")
                else:
                    await self.sio.emit('track_played', {'status': 'error', 'message': 'No audio player or play_track method'}, room=sid)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"[SOCKET.IO] Error in play_track: {str(e)}")
                await self.sio.emit('track_played', {'status': 'error', 'message': str(e)}, room=sid)

        @self.sio.on('start_nfc_link')
        async def handle_start_nfc_link(sid, data):
            playlist_id = data.get('playlist_id') if data else None
            if not playlist_id:
                await self.sio.emit('nfc_error', {'message': 'playlist_id missing'}, room=sid)
                return
            try:
                if self.nfc_service.is_listening():
                    await self.sio.emit('nfc_error', {'message': 'NFC already listening'}, room=sid)
                    return
                self.nfc_service.start_listening(playlist_id)
                await self.sio.emit('nfc_status', {'status': 'waiting'}, room=sid)
                # Simulate NFC detection (replace with real callback in prod)
                import asyncio
                async def on_tag_detected():
                    await asyncio.sleep(2)
                    await self.sio.emit('nfc_linked', {'playlist_id': playlist_id}, room=sid)
                self.sio.start_background_task(on_tag_detected)
            except Exception as e:
                await self.sio.emit('nfc_error', {'message': str(e)}, room=sid)
