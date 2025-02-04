# app/src/server.py

import signal
import sys

import eventlet
eventlet.monkey_patch(os=False)
from eventlet.event import Event

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

from .config import Config
from .monitoring.improved_logger import ImprovedLogger, LogLevel
from .helpers.exceptions import AppError
from .core import Application, Container
from .routes.api_routes import init_routes



logger = ImprovedLogger(__name__)

class Server:
    def __init__(self, config: Config):
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
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self):
        self.cleanup()
        sys.exit(0)

    def initialize(self):
        try:
            self.container = Container(self.config)
            self.app.container = self.container
            self.application = Application(self.container)
            self.app.application = self.application
            logger.log(LogLevel.INFO, "Server initialized successfully")
            return self.app, self.socketio
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Server initialization failed: {str(e)}")
            self.cleanup()
            raise

    def cleanup(self):
        logger.log(LogLevel.INFO, "Starting server cleanup")
        if self.container:
            try:
                self.container.cleanup()
            except (AppError, RuntimeError, ValueError) as e:
                logger.log(LogLevel.ERROR, f"Cleanup error: {str(e)}")
            finally:
                self.container = None
                self.application = None
        self.stop_event.send(True)

    def run(self):
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
    server = Server(config)
    return server.initialize()

def run_server(app, socketio, config: Config):
    server = Server(config)
    server.app = app
    server.socketio = socketio
    server.run()
