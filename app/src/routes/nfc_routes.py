# app/src/routes/nfc_routes.py

from flask import Blueprint, current_app, request, jsonify
from src.services.nfc_service import NFCService
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.services import PlaylistService
from http import HTTPStatus

logger = ImprovedLogger(__name__)

class NFCRoutes:
    def __init__(self, app, nfc_service: NFCService):
        self.app = app
        self.api = Blueprint('nfc_api', __name__)
        self.nfc_service = nfc_service
        self._register_routes()

    def register(self):
        """Register blueprint with prefix /api"""
        self.app.register_blueprint(self.api, url_prefix='/api')

    def _register_routes(self):
        @self.api.route('/playlists')
        def get_playlists():
            try:
                # Utiliser db_file au lieu de playlists_file
                playlist_service = PlaylistService(current_app.container.config.db_file)
                mapping = playlist_service.read_playlist_file()
                return jsonify(mapping)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error reading playlists: {str(e)}")
                return jsonify({"error": "Failed to read playlists"}), 500

        @self.api.route('/playlists', methods=['POST'])
        def update_playlists():
            try:
                data = request.json
                if not data or not isinstance(data, list):
                    return jsonify({"error": "Invalid data format"}), 400

                # Utiliser db_file au lieu de playlists_file
                playlist_service = PlaylistService(current_app.container.config.db_file)
                playlist_service.save_playlist_file(data)
                return jsonify({"status": "success"})
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error updating playlists: {str(e)}")
                return jsonify({"error": "Failed to update playlists"}), 500

        @self.api.route('/playlists/associate', methods=['POST'])
        def associate_nfc_tag():
            """Associate a NFC tag with a playlist"""
            try:
                if not request.is_json:
                    return jsonify({"error": "Content-Type must be application/json"}), 400

                data = request.json
                if not data.get('playlist_id') or not data.get('nfc_tag'):
                    return jsonify({"error": "playlist_id and nfc_tag are required"}), 400

                # Utiliser db_file au lieu de playlists_file
                playlist_service = PlaylistService(current_app.container.config.db_file)

                # Check if tag is already associated
                existing_playlist = playlist_service.get_playlist_by_tag(data['nfc_tag'])
                if existing_playlist:
                    return jsonify({
                        "error": f"NFC tag already associated with playlist: {existing_playlist['title']}"
                    }), 409

                # Find playlist to associate
                playlist = playlist_service.get_playlist_by_id(data['playlist_id'])
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                # Associate the tag
                if playlist_service.associate_tag(data['playlist_id'], data['nfc_tag']):
                    return jsonify({
                        "status": "success",
                        "playlist": playlist_service.get_playlist_by_id(data['playlist_id'])
                    })
                else:
                    return jsonify({"error": "Failed to associate tag"}), 500

            except Exception as e:
                logger.log(LogLevel.ERROR, f"NFC tag association error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlists/dissociate', methods=['POST'])
        def dissociate_nfc_tag():
            """Remove NFC tag association from a playlist"""
            try:
                if not request.is_json:
                    return jsonify({"error": "Content-Type must be application/json"}), 400

                data = request.json
                if not data.get('playlist_id'):
                    return jsonify({"error": "playlist_id is required"}), 400

                # Utiliser db_file au lieu de playlists_file
                playlist_service = PlaylistService(current_app.container.config.db_file)

                # Find the playlist
                playlist = playlist_service.get_playlist_by_id(data['playlist_id'])
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                if not playlist.get('nfc_tag'):
                    return jsonify({"error": "Playlist has no NFC tag associated"}), 400

                # Remove the association
                if playlist_service.dissociate_tag(data['playlist_id']):
                    return jsonify({
                        "status": "success",
                        "playlist": playlist_service.get_playlist_by_id(data['playlist_id'])
                    })
                else:
                    return jsonify({"error": "Failed to dissociate tag"}), 500

            except Exception as e:
                logger.log(LogLevel.ERROR, f"NFC tag dissociation error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Route to start NFC listening
        @self.api.route('/nfc/listen/<playlist_id>', methods=['POST'])
        def start_nfc_listening(playlist_id):
            """Start NFC listening for a given playlist"""
            try:
                if self.nfc_service.is_listening():
                    return jsonify({
                        'status': 'error',
                        'message': 'An NFC listening session is already active'
                    }), HTTPStatus.CONFLICT

                # Check that the playlist exists
                # Utiliser db_file au lieu de playlists_file
                playlist_service = PlaylistService(current_app.container.config.db_file)
                playlist = playlist_service.get_playlist_by_id(playlist_id)

                if not playlist:
                    return jsonify({
                        'status': 'error',
                        'message': 'Playlist not found'
                    }), HTTPStatus.NOT_FOUND

                playlists = playlist_service.read_playlist_file()
                self.nfc_service.load_mapping(playlists)
                self.nfc_service.start_listening(playlist_id)
                return jsonify({
                    'status': 'success',
                    'message': 'NFC listening started'
                }), HTTPStatus.OK

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error starting NFC listening: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Internal server error'
                }), HTTPStatus.INTERNAL_SERVER_ERROR

        # Route to stop NFC listening
        @self.api.route('/nfc/stop', methods=['POST'])
        def stop_nfc_listening():
            """Stop current NFC listening"""
            try:
                self.nfc_service.stop_listening()
                return jsonify({
                    'status': 'success',
                    'message': 'NFC listening stopped'
                }), HTTPStatus.OK

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error stopping NFC listening: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Internal server error'
                }), HTTPStatus.INTERNAL_SERVER_ERROR

        # Route to simulate tag detection (useful for testing)
        @self.api.route('/nfc/simulate_tag', methods=['POST'])
        def simulate_tag_detection():
            """Simulate NFC tag detection (for testing)"""
            try:
                data = request.get_json()
                if not data or 'tag_id' not in data:
                    return jsonify({
                        'status': 'error',
                        'message': 'tag_id missing'
                    }), HTTPStatus.BAD_REQUEST

                tag_id = data['tag_id']
                success = self.nfc_service.handle_tag_detected(tag_id)

                if success:
                    return jsonify({
                        'status': 'success',
                        'message': f'Tag {tag_id} processed successfully'
                    }), HTTPStatus.OK
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Tag not processed or already associated'
                    }), HTTPStatus.CONFLICT

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error simulating NFC detection: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Internal server error'
                }), HTTPStatus.INTERNAL_SERVER_ERROR