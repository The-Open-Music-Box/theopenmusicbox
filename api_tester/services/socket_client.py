# app/tests/api/services/socket_client.py

import socketio
from typing import Callable, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SocketClient:
    """Client for handling WebSocket connections and events."""

    def __init__(self, url: str = "http://localhost:5000"):
        self.url = url
        self.sio = socketio.Client()
        self.connected = False
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up default event handlers."""
        @self.sio.event
        def connect():
            logger.info("Connected to WebSocket server")
            self.connected = True

        @self.sio.event
        def disconnect():
            logger.info("Disconnected from WebSocket server")
            self.connected = False

        @self.sio.event
        def connect_error(data):
            logger.error(f"Connection error: {data}")
            self.connected = False

    def connect(self):
        """Connect to the WebSocket server."""
        try:
            if not self.connected:
                self.sio.connect(self.url)
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")

    def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.connected:
            self.sio.disconnect()

    def on(self, event: str, handler: Callable[[Dict[str, Any]], None]):
        """Register an event handler."""
        self.sio.on(event, handler)

    def emit(self, event: str, data: Dict[str, Any]):
        """Emit an event to the server."""
        if self.connected:
            try:
                self.sio.emit(event, data)
            except Exception as e:
                logger.error(f"Failed to emit event: {str(e)}")

    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self.connected