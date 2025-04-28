# app/src/routes/websocket_handlers.py

from flask import request, current_app
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class WebSocketHandlers:
    def __init__(self, socketio, app):
        self.socketio = socketio
        self.app = app
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