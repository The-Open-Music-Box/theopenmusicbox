# app/src/server.py

import signal
import sys
import eventlet
import atexit
from pathlib import Path

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
from .routes.spotify_routes import init_spotify_routes

logger = ImprovedLogger(__name__)

def create_server(config: Config):
    # Check system dependencies at startup
    dependency_errors = SystemDependencyChecker.check_dependencies()
    if (dependency_errors):
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

    # Initialize routes
    init_routes(app, socketio)

    # Initialize Spotify routes if enabled
    if config.spotify_enabled:
        init_spotify_routes(app, socketio)
        logger.log(LogLevel.INFO, "Spotify routes initialized")

    def shutdown_handler(signum, frame):
        logger.log(LogLevel.INFO, f"Shutdown signal received: {signal.Signals(signum).name}")
        try:
            # Close all active socket connections
            if hasattr(app, 'socketio'):
                app.socketio.server.disconnect()
                logger.log(LogLevel.INFO, "All socket connections closed")

            # Cleanup container resources
            if hasattr(app, 'container'):
                app.container.cleanup()
                logger.log(LogLevel.INFO, "Container cleanup completed")

            # Give a short grace period for resources to be released
            eventlet.sleep(1)

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during shutdown: {e}")
        finally:
            sys.exit(0)

    def reload_handler(signum, frame):
        logger.log(LogLevel.INFO, "Reload signal (SIGUSR1) received")
        try:
            if hasattr(app, 'socketio'):
                app.socketio.server.disconnect()
            if hasattr(app, 'container'):
                app.container.cleanup()
            # Don't exit - systemd will restart the service
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during reload: {e}")

    # Function to be called at exit (registered with atexit)
    def exit_handler():
        logger.log(LogLevel.INFO, "Application exit handler called")
        try:
            if hasattr(app, 'container') and hasattr(app.container, '_led_hat') and app.container._led_hat:
                # Ensure LEDs are turned off
                app.container._led_hat.stop_animation()
                app.container._led_hat.clear()
                logger.log(LogLevel.INFO, "LEDs turned off at exit")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error turning off LEDs at exit: {e}")

    # Register signal handlers
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGUSR1, reload_handler)
    signal.signal(signal.SIGHUP, shutdown_handler)  # Add SIGHUP handler

    # Register exit handler
    atexit.register(exit_handler)

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
        try:
            if hasattr(app, 'socketio'):
                app.socketio.server.disconnect()
            if hasattr(app, 'container'):
                app.container.cleanup()
        except Exception as cleanup_error:
            logger.log(LogLevel.ERROR, f"Error during cleanup after server error: {cleanup_error}")
        raise