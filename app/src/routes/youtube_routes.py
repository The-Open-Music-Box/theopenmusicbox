# app/src/routes/youtube_routes.py

from flask import Blueprint, current_app, request, jsonify

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services import YouTubeService

logger = ImprovedLogger(__name__)

class YouTubeRoutes:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.api = Blueprint('youtube_api', __name__)

    def register(self):
        self._init_routes()
        self.app.register_blueprint(self.api, url_prefix='/api')

    def _init_routes(self):
        @self.api.route('/youtube/download', methods=['POST'])
        def download_youtube():
            logger.log(LogLevel.INFO, "Received YouTube download request")
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400

            url = request.json.get('url')
            if not url:
                return jsonify({"error": "Invalid YouTube URL"}), 400

            try:
                service = YouTubeService(self.socketio, current_app.container.config)
                result = service.process_download(url)
                return jsonify(result)

            except Exception as e:
                error_msg = str(e)
                logger.log(LogLevel.ERROR, f"Download failed: {error_msg}")
                return jsonify({"error": error_msg}), 500