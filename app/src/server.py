# app/src/server.py

import signal
import sys
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
from .helpers.system_dependency_checker import SystemDependencyChecker
from .helpers.exceptions import AppError
from .core.container import SocketIOPublisher

logger = ImprovedLogger(__name__)

def create_server(config: Config):
    # Vérifier les dépendances système au démarrage
    dependency_errors = SystemDependencyChecker.check_dependencies()
    if dependency_errors:
        for error in dependency_errors:
            logger.log(LogLevel.ERROR, f"System dependency error: {error.message}")
        raise AppError.configuration_error(
            message="Missing required system dependencies",
            config_key="dependencies",
            details={"errors": [e.message for e in dependency_errors]}
        )

    static_folder = Path(__file__).resolve().parent.parent / 'static'
    static_folder.mkdir(parents=True, exist_ok=True)

    app = Flask(__name__,
                static_folder=str(static_folder),
                static_url_path='')

    CORS(app, origins=config.cors_allowed_origins)

    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=config.debug,
        engineio_logger=config.debug,
        ping_timeout=60,
        ping_interval=25,
        async_handlers=True,
        allow_upgrades=True,
        transports=['websocket', 'polling']
    )

    # Create event publisher and container
    event_publisher = SocketIOPublisher(socketio)
    container = Container(config, event_publisher)
    app.container = container
    app.socketio = socketio

    application = Application(container)
    app.application = application

    init_routes(app, socketio)

    def shutdown_handler(signum, frame):
        logger.log(LogLevel.INFO, "Shutdown signal received")
        if hasattr(app, 'container'):
            app.container.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    return app, socketio

def run_server(app, socketio, config: Config):
    try:
        logger.log(LogLevel.INFO, f"Starting server on port {config.socketio_port}")
        socketio.run(
            app,
            host=config.socketio_host,
            port=config.socketio_port,
            debug=config.debug,
            allow_unsafe_werkzeug=True,
            use_reloader=config.use_reloader
        )
    except Exception as e:
        logger.log(LogLevel.ERROR, f"Server error: {str(e)}")
        if hasattr(app, 'container'):
            app.container.cleanup()
        raise