# app/src/server.py

import signal
import sys

import eventlet

from eventlet.event import Event

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

from config import Config
from monitoring.improved_logger import ImprovedLogger, LogLevel
from helpers.exceptions import AppError
eventlet.monkey_patch(os=False)

logger = ImprovedLogger(__name__)

class Server:
    """
    Server class handling Flask and SocketIO initialization and lifecycle.

    Manages the web server setup, configuration, signal handling,
    and cleanup operations.
    """

    def __init__(self, config: Config):
        """
        Initialize server with configuration.

        Args:
            config: Application configuration instance
        """
        self._setup_signal_handlers()
        self.config = config
        self.app = Flask(__name__)
        CORS(self.app, origins=self.config.cors_allowed_origins)
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins=self.config.cors_allowed_origins,
            async_mode='eventlet',
            logger=self.config.debug,
            engineio_logger=self.config.debug
        )
        self.stop_event = Event()
        self.container = None
        self.application = None

    def _setup_signal_handlers(self):
        """Setup handlers for SIGTERM and SIGINT signals."""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self):
        """Handle server shutdown when receiving termination signals."""
        self.cleanup()
        sys.exit(0)

    def initialize(self):
        """
        Initialize the server components.

        Returns:
            tuple: Flask app and SocketIO instances

        Raises:
            AppError: If initialization fails
        """
        try:
            logger.log(LogLevel.INFO, "Server initialized successfully")
            return self.app, self.socketio

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Server initialization failed: {str(e)}")
            self.cleanup()
            raise

    def cleanup(self):
        """Clean up server resources and stop running components."""
        logger.log(LogLevel.INFO, "Starting server cleanup")
        if self.container:
            try:
                with self.app.app_context():
                    self.container.cleanup()
            except (AppError, RuntimeError, ValueError) as e:
                logger.log(LogLevel.ERROR, f"Cleanup error: {str(e)}")
            finally:
                self.container = None
                self.application = None
        self.stop_event.send(True)

    def run(self):
        """
        Run the server.

        Raises:
            AppError: If server fails to start or runtime error occurs
        """
        try:
            self.socketio.run(
                self.app,
                host=self.config.socketio_host,
                port=self.config.socketio_port,
                debug=self.config.debug,
                allow_unsafe_werkzeug=True,
                use_reloader=self.config.use_reloader
            )
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Server runtime error: {str(e)}")
            self.cleanup()
            raise

def create_server(config: Config):
    """
    Create and initialize a new server instance.

    Args:
        config: Application configuration

    Returns:
        tuple: Initialized Flask app and SocketIO instances
    """
    server = Server(config)
    return server.initialize()

def run_server(app, socketio, config: Config):
    """
    Run an existing server with provided app and socketio instances.

    Args:
        app: Flask application instance
        socketio: SocketIO instance
        config: Application configuration
    """
    server = Server(config)
    server.app = app
    server.socketio = socketio
    server.run()
