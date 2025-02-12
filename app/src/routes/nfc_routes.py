# app/src/routes/nfc_routes.py

from flask import Blueprint, current_app, request, jsonify

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.services import NFCMappingService

logger = ImprovedLogger(__name__)

class NFCRoutes:
    def __init__(self, app):
        self.app = app
        self.api = Blueprint('nfc_api', __name__)

    def register(self):
        self._init_routes()
        self.app.register_blueprint(self.api, url_prefix='/api')

    def _init_routes(self):
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