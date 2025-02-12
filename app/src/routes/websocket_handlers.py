# app/src/routes/websocket_handlers.py

from flask import request
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class WebSocketHandlers:
    def __init__(self, socketio):
        self.socketio = socketio

    def register(self):
        @self.socketio.on('connect')
        def handle_connect():
            logger.log(LogLevel.INFO, f"Client connected: {request.sid}")
            self.socketio.emit('connection_status', {'status': 'connected', 'sid': request.sid})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.log(LogLevel.INFO, f"Client disconnected: {request.sid}")