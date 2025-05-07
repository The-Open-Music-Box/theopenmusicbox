from flask import request
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class WebSocketHandlers:
    def __init__(self, socketio, app, nfc_service=None):
        self.socketio = socketio
        self.app = app
        self.nfc_service = nfc_service
        self._setup_progress_subscription()

    def _setup_progress_subscription(self):
        """Setup subscription to track progress events"""
        def handle_track_progress(event):
            """Handle track progress events and emit them to all connected clients"""
            logger.log(LogLevel.INFO, f"Track progress event: {event.data}")
            self.socketio.emit('track_progress', event.data)

        # Subscribe to progress events
        with self.app.app_context():
            try:
                if hasattr(self.app, 'container') and self.app.container.playback_subject:
                    logger.log(LogLevel.INFO, "Subscribing to track progress events")
                    self.app.container.playback_subject.progress_stream.subscribe(handle_track_progress)
                else:
                    logger.log(LogLevel.WARNING, "No playback subject available for subscription")
            except (RuntimeError, ConnectionError, TimeoutError) as e:
                logger.log(LogLevel.ERROR, f"Error setting up progress subscription: {str(e)}")

    def register(self):
        @self.socketio.on('start_nfc_link')
        async def handle_start_nfc_link(data):
            sid = request.sid
            playlist_id = data.get('playlist_id') if data else None
            
            # Validate playlist_id
            if not playlist_id:
                await self.socketio.emit('nfc_error', {
                    'message': 'playlist_id missing',
                    'type': 'error'
                }, room=sid)
                return
                
            # Check if already listening
            try:
                if self.nfc_service.is_listening():
                    await self.socketio.emit('nfc_error', {
                        'message': 'NFC already listening for another request',
                        'type': 'error'
                    }, room=sid)
                    return
                    
                # Start listening for NFC tag with the sid for directing callbacks
                await self.nfc_service.start_listening(playlist_id, sid)
                
                # Initial status update
                await self.socketio.emit('nfc_status', {
                    'type': 'nfc_status',
                    'status': 'waiting',
                    'message': 'Waiting for NFC tag...',
                    'playlist_id': playlist_id
                }, room=sid)
                
            except (RuntimeError, ConnectionError, TimeoutError) as e:
                logger.log(LogLevel.ERROR, f"Error in start_nfc_link: {str(e)}")
                await self.socketio.emit('nfc_error', {
                    'message': str(e),
                    'type': 'error'
                }, room=sid)
                
        @self.socketio.on('stop_nfc_link')
        async def handle_stop_nfc_link():
            sid = request.sid
            try:
                if self.nfc_service.is_listening():
                    await self.nfc_service.stop_listening()
                    await self.socketio.emit('nfc_status', {
                        'type': 'nfc_status',
                        'status': 'stopped',
                        'message': 'NFC tag association stopped by user'
                    }, room=sid)
                else:
                    await self.socketio.emit('nfc_status', {
                        'type': 'nfc_status',
                        'status': 'not_listening',
                        'message': 'No active NFC tag association to stop'
                    }, room=sid)
            except (RuntimeError, ConnectionError, TimeoutError) as e:
                logger.log(LogLevel.ERROR, f"Error in stop_nfc_link: {str(e)}")
                await self.socketio.emit('nfc_error', {
                    'message': str(e),
                    'type': 'error'
                }, room=sid)
                
        @self.socketio.on('override_nfc_tag')
        async def handle_override_tag():
            sid = request.sid
            try:
                if not self.nfc_service.is_listening():
                    await self.socketio.emit('nfc_error', {
                        'message': 'Not in NFC association mode',
                        'type': 'error'
                    }, room=sid)
                    return
                    
                # Set override mode to true and process last tag again
                await self.nfc_service.set_override_mode(True)
                
                await self.socketio.emit('nfc_status', {
                    'type': 'nfc_status',
                    'status': 'override_mode',
                    'message': 'Override mode enabled. Processing tag...'
                }, room=sid)
                
            except (RuntimeError, ConnectionError, TimeoutError) as e:
                logger.log(LogLevel.ERROR, f"Error in override_nfc_tag: {str(e)}")
                await self.socketio.emit('nfc_error', {
                    'message': str(e),
                    'type': 'error'
                }, room=sid)

        @self.socketio.on('connect')
        def handle_connect():
            logger.log(LogLevel.INFO, f"Client connected: {request.sid}")
            self.socketio.emit('connection_status', {'status': 'connected', 'sid': request.sid}, room=request.sid)
            # Emit current playback status and progress to the newly connected client
            playback_subject = None
            if hasattr(self.app, 'container') and hasattr(self.app.container, 'playback_subject'):
                playback_subject = self.app.container.playback_subject
            if playback_subject:
                status_event = playback_subject.get_last_status_event()
                progress_event = playback_subject.get_last_progress_event()
                if status_event:
                    self.socketio.emit('playback_status', status_event.data, room=request.sid)
                if progress_event:
                    self.socketio.emit('track_progress', progress_event.data, room=request.sid)

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.log(LogLevel.INFO, f"Client disconnected: {request.sid}")