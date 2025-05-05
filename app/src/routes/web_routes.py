from pathlib import Path
from flask import Blueprint, current_app, jsonify

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class WebRoutes:
    def __init__(self, app):
        self.app = app
        self.web = Blueprint('web', __name__)

    def register(self):
        self._init_routes()
        self.app.register_blueprint(self.web)

    def _init_routes(self):
        @self.web.route('/', defaults={'path': ''})
        @self.web.route('/<path:path>')
        def serve(path):
            try:
                if path and Path(current_app.static_folder / path).exists():
                    return current_app.send_static_file(path)
                return current_app.send_static_file('index.html')
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error serving static file: {str(e)}")
                return jsonify({"error": "File not found"}), 404

        @self.web.route('/health')
        def health_check():
            try:
                container = current_app.container
                status = {
                    "status": "ok",
                    "components": {
                        "websocket": bool(current_app.socketio),
                        "gpio": bool(container.gpio),
                        "nfc": bool(container.nfc),
                        "audio": bool(container.audio),
                        "led_hat": bool(container.led_hat)
                    }
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500