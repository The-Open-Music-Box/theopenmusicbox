# app/src/routes/api_routes.py

from flask import Blueprint, jsonify, current_app
from flask_socketio import emit
from pathlib import Path

from ..monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class APIRoutes:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.api = Blueprint('api', __name__)
        self.web = Blueprint('web', __name__)

    def init_routes(self):
        self._init_socket_handlers()
        self._init_api_routes()
        self.app.register_blueprint(self.api, url_prefix='/api')
        self.app.register_blueprint(self.web)

    def _init_socket_handlers(self):
        @self.socketio.on('connect')
        def handle_connect():
            emit('connection_status', {'status': 'connected'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            emit('connection_status', {'status': 'disconnected'})

    def _init_api_routes(self):
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

        @self.api.route('/system/health')
        def health_check():
            return jsonify({
                "status": "ok"
            })

def init_routes(app, socketio):
    routes = APIRoutes(app, socketio)
    routes.init_routes()
    return routes