# app/src/routes/api_routes.py

import uuid
from flask import Blueprint, jsonify, current_app, request
from flask_socketio import emit
from pathlib import Path

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.helpers.system_dependency_checker import SystemDependencyChecker
from src.services import (
    YouTubeDownloader,
    validate_youtube_url,
    NFCMappingService
)

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
            logger.log(LogLevel.INFO, f"Client connected: {request.sid}")
            emit('connection_status', {'status': 'connected', 'sid': request.sid})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.log(LogLevel.INFO, f"Client disconnected: {request.sid}")

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

        @self.api.route('/health')
        def health_check():
            try:
                app = current_app
                container = app.container
                status = {
                    "status": "ok",
                    "components": {
                        "websocket": bool(app.socketio),
                        "gpio": bool(container.gpio),
                        "nfc": bool(container.nfc)
                    }
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.api.route('/nfc_mapping')
        def get_nfc_mapping():
            try:
                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()
                return jsonify(mapping)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error reading NFC mapping: {str(e)}")
                return jsonify({"error": "Failed to read NFC mapping"}), 500

        @self.api.route('/nfc_mapping', methods=['POST'])
        def update_nfc_mapping():
            try:
                data = request.json
                if not data or not isinstance(data, list):
                    return jsonify({"error": "Invalid data format"}), 400

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                nfc_service.save_mapping(data)
                return jsonify({"status": "success"})
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error updating NFC mapping: {str(e)}")
                return jsonify({"error": "Failed to update NFC mapping"}), 500

        @self.api.route('/youtube/download', methods=['POST'])
        def download_youtube():
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400

            url = request.json.get('url')
            if not url or not validate_youtube_url(url):
                return jsonify({"error": "Invalid YouTube URL"}), 400

            download_id = str(uuid.uuid4())
            try:
                downloader = YouTubeDownloader(self.socketio, download_id)
                result = downloader.download(
                    url,
                    current_app.container.config.upload_folder,
                    current_app.container.config.nfc_mapping_file
                )

                return jsonify({
                    "status": "success",
                    "download_id": download_id,
                    "folder": result['folder']
                })

            except Exception as e:
                error_msg = str(e)
                logger.log(LogLevel.ERROR, f"Download failed: {error_msg}")
                return jsonify({"error": error_msg}), 500

def init_routes(app, socketio):
    routes = APIRoutes(app, socketio)
    routes.init_routes()
    return routes