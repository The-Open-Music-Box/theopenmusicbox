# app/src/server.py

import signal
import sys
import socket
import subprocess
import contextlib
from pathlib import Path
import eventlet
eventlet.monkey_patch(os=False)

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

from .config import Config
from .monitoring.improved_logger import ImprovedLogger, LogLevel
from .core import Application, Container
from .routes.api_routes import init_routes

logger = ImprovedLogger(__name__)

class Server:
    def __init__(self, config: Config):
        self.config = config
        self.initialized = False
        self._port_retry_count = 0
        self._max_port_retries = 3
        self._port_check_timeout = 1  # seconds

        static_folder = Path(__file__).resolve().parent.parent / 'static'
        static_folder.mkdir(parents=True, exist_ok=True)

        self.app = Flask(__name__,
                    static_folder=str(static_folder),
                    static_url_path='')

        CORS(self.app, origins=self.config.cors_allowed_origins)

        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins=self.config.cors_allowed_origins,
            async_mode='eventlet',
            logger=self.config.debug,
            engineio_logger=self.config.debug
        )

        self.container = None
        self.application = None

        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, *_):
        logger.log(LogLevel.INFO, "Shutdown signal received")
        self.cleanup()
        sys.exit(0)

    def force_release_port(self, port: int) -> bool:
        """Attempt to forcefully release a port using lsof command"""
        try:
            # Run lsof to get process information
            result = subprocess.run(['lsof', '-ti', f':{port}'],
                                 capture_output=True,
                                 text=True)

            if result.returncode == 0 and result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        # Try to kill the process
                        subprocess.run(['kill', '-9', pid], check=True)
                        logger.log(LogLevel.INFO, f"Killed process {pid} using port {port}")
                    except subprocess.CalledProcessError as e:
                        logger.log(LogLevel.ERROR, f"Failed to kill process {pid}: {str(e)}")
                        continue
                return True
            return False
        except subprocess.CalledProcessError as e:
            logger.log(LogLevel.ERROR, f"Error checking port {port}: {str(e)}")
            return False

    def check_port(self, port: int) -> bool:
        """Check if a port is available"""
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.settimeout(self._port_check_timeout)
                sock.bind(('0.0.0.0', port))
                return True
            except OSError:
                return False

    def initialize(self):
        try:
            if self.initialized:
                self.cleanup()

            self.container = Container(self.config)
            self.app.container = self.container
            self.app.socketio = self.socketio
            self.application = Application(self.container)
            self.app.application = self.application

            init_routes(self.app, self.socketio)

            self.initialized = True
            logger.log(LogLevel.INFO, "Server initialized successfully")
            return self.app, self.socketio

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Server initialization failed: {str(e)}")
            self.cleanup()
            raise

    def cleanup(self):
        if not hasattr(self, 'initialized') or not self.initialized:
            return

        logger.log(LogLevel.INFO, "Starting server cleanup")
        try:
            if self.socketio:
                self.socketio.stop()
            if self.container:
                self.container.cleanup()
                self.container = None
                self.application = None
            self.initialized = False
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Cleanup error: {str(e)}")

    def run(self):
        try:
            port = self.config.socketio_port

            while self._port_retry_count < self._max_port_retries:
                if self.check_port(port):
                    break

                self._port_retry_count += 1
                logger.log(LogLevel.WARNING,
                    f"Port {port} is busy, attempt {self._port_retry_count}/{self._max_port_retries}")

                # Try to force release the port
                if self.force_release_port(port):
                    logger.log(LogLevel.INFO, f"Attempting to release port {port}")
                    eventlet.sleep(2)  # Give the port more time to fully release
                    if self.check_port(port):
                        break

                if self._port_retry_count < self._max_port_retries:
                    wait_time = 2 ** self._port_retry_count
                    logger.log(LogLevel.INFO, f"Waiting {wait_time} seconds before retry...")
                    eventlet.sleep(wait_time)

            if self._port_retry_count >= self._max_port_retries:
                raise OSError(f"Port {port} is still in use after {self._max_port_retries} attempts")

            logger.log(LogLevel.INFO, f"Starting server on port {port}")
            self.socketio.run(
                self.app,
                host=self.config.socketio_host,
                port=port,
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
    server.run(0)