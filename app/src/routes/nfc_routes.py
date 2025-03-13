# app/src/routes/nfc_routes.py

from flask import Blueprint, current_app, request, jsonify
from src.services.nfc_service import NFCService
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.services import NFCMappingService
from http import HTTPStatus

logger = ImprovedLogger(__name__)

class NFCRoutes:
    def __init__(self, app, nfc_service: NFCService):
        self.app = app
        self.api = Blueprint('nfc_api', __name__)
        self.nfc_service = nfc_service
        self._register_routes()  # Register routes but don't register blueprint yet

    def register(self):
        """Enregistre le blueprint avec le préfixe /api"""
        self.app.register_blueprint(self.api, url_prefix='/api')

    def _register_routes(self):
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

        @self.api.route('/nfc_mapping/associate', methods=['POST'])
        def associate_nfc_tag():
            """Associate a NFC tag with a playlist"""
            try:
                if not request.is_json:
                    return jsonify({"error": "Content-Type must be application/json"}), 400

                data = request.json
                if not data.get('playlist_id') or not data.get('nfc_tag'):
                    return jsonify({"error": "playlist_id and nfc_tag are required"}), 400

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                # Vérifier si le tag est déjà associé
                existing_playlist = next(
                    (p for p in mapping if p.get('nfc_tag') == data['nfc_tag']),
                    None
                )
                if existing_playlist:
                    return jsonify({
                        "error": f"NFC tag already associated with playlist: {existing_playlist['title']}"
                    }), 409

                # Trouver la playlist à associer
                playlist = next((p for p in mapping if p['id'] == data['playlist_id']), None)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                # Associer le tag
                playlist['nfc_tag'] = data['nfc_tag']
                nfc_service.save_mapping(mapping)

                return jsonify({
                    "status": "success",
                    "playlist": playlist
                })

            except Exception as e:
                logger.log(LogLevel.ERROR, f"NFC tag association error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/nfc_mapping/dissociate', methods=['POST'])
        def dissociate_nfc_tag():
            """Remove NFC tag association from a playlist"""
            try:
                if not request.is_json:
                    return jsonify({"error": "Content-Type must be application/json"}), 400

                data = request.json
                if not data.get('playlist_id'):
                    return jsonify({"error": "playlist_id is required"}), 400

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                # Trouver la playlist
                playlist = next((p for p in mapping if p['id'] == data['playlist_id']), None)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                if not playlist.get('nfc_tag'):
                    return jsonify({"error": "Playlist has no NFC tag associated"}), 400

                # Supprimer l'association
                playlist['nfc_tag'] = None
                nfc_service.save_mapping(mapping)

                return jsonify({
                    "status": "success",
                    "playlist": playlist
                })

            except Exception as e:
                logger.log(LogLevel.ERROR, f"NFC tag dissociation error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Route pour démarrer l'écoute NFC
        @self.api.route('/nfc/listen/<playlist_id>', methods=['POST'])
        def start_nfc_listening(playlist_id):
            """Démarre l'écoute NFC pour une playlist donnée"""
            try:
                if self.nfc_service.is_listening():
                    return jsonify({
                        'status': 'error',
                        'message': 'Une session d\'écoute NFC est déjà en cours'
                    }), HTTPStatus.CONFLICT

                # Vérifier que la playlist existe
                nfc_mapping_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_mapping_service.read_mapping()
                playlist = next((p for p in mapping if p['id'] == playlist_id), None)

                if not playlist:
                    return jsonify({
                        'status': 'error',
                        'message': 'Playlist non trouvée'
                    }), HTTPStatus.NOT_FOUND

                self.nfc_service.load_mapping(mapping)  # Charge le mapping actuel
                self.nfc_service.start_listening(playlist_id)
                return jsonify({
                    'status': 'success',
                    'message': 'Écoute NFC démarrée'
                }), HTTPStatus.OK

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Erreur lors du démarrage de l'écoute NFC: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Erreur interne du serveur'
                }), HTTPStatus.INTERNAL_SERVER_ERROR

        # Route pour arrêter l'écoute NFC
        @self.api.route('/nfc/stop', methods=['POST'])
        def stop_nfc_listening():
            """Arrête l'écoute NFC en cours"""
            try:
                self.nfc_service.stop_listening()
                return jsonify({
                    'status': 'success',
                    'message': 'Écoute NFC arrêtée'
                }), HTTPStatus.OK

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Erreur lors de l'arrêt de l'écoute NFC: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Erreur interne du serveur'
                }), HTTPStatus.INTERNAL_SERVER_ERROR

        # Route pour simuler la détection d'un tag (utile pour les tests)
        @self.api.route('/nfc/simulate_tag', methods=['POST'])
        def simulate_tag_detection():
            """Simule la détection d'un tag NFC (pour les tests)"""
            try:
                data = request.get_json()
                if not data or 'tag_id' not in data:
                    return jsonify({
                        'status': 'error',
                        'message': 'tag_id manquant'
                    }), HTTPStatus.BAD_REQUEST

                tag_id = data['tag_id']
                success = self.nfc_service.handle_tag_detected(tag_id)

                if success:
                    return jsonify({
                        'status': 'success',
                        'message': f'Tag {tag_id} traité avec succès'
                    }), HTTPStatus.OK
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Tag non traité ou déjà associé'
                    }), HTTPStatus.CONFLICT

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Erreur lors de la simulation de détection NFC: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Erreur interne du serveur'
                }), HTTPStatus.INTERNAL_SERVER_ERROR