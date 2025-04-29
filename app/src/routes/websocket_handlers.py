# app/src/routes/websocket_handlers.py

from flask import request, current_app
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

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
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error setting up progress subscription: {str(e)}")

    def register(self):
        @self.socketio.on('start_nfc_link')
        def handle_start_nfc_link(data):
            sid = request.sid
            playlist_id = data.get('playlist_id') if data else None
            if not playlist_id:
                self.socketio.emit('nfc_error', {'message': 'playlist_id missing'}, room=sid)
                return
            try:
                if self.nfc_service.is_listening():
                    self.socketio.emit('nfc_error', {'message': 'NFC already listening'}, room=sid)
                    return
                # Start listening for NFC tag for the playlist
                self.nfc_service.start_listening(playlist_id)
                self.socketio.emit('nfc_status', {'status': 'waiting'}, room=sid)
                # Patch: Register a callback for tag detection (mock or real)
                # For demo, simulate immediate tag detection
                # In real use, NFCService should call this when tag is detected
                def on_tag_detected():
                    self.socketio.emit('nfc_linked', {'playlist_id': playlist_id}, room=sid)
                # You must wire this to your NFCService logic, e.g.:
                # self.nfc_service.set_tag_detected_callback(on_tag_detected)
                # For now, simulate after a short delay
                import threading
                threading.Timer(2.0, on_tag_detected).start()
            except Exception as e:
                self.socketio.emit('nfc_error', {'message': str(e)}, room=sid)

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