from flask import Blueprint, current_app, request, jsonify
from app.src.services.nfc_service import NFCService
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services import PlaylistService
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
        @self.api.route('/nfc/associate/initiate', methods=['POST'])
        def initiate_nfc_association():
            """Initiate NFC association for a playlist (activate NFC reader)"""
            try:
                data = request.get_json()
                playlist_id = data.get('playlist_id') if data else None
                if not playlist_id:
                    return jsonify({'error': 'playlist_id is required'}), 400
                # Activate NFC reader for association
                started = self.nfc_service.start_association_mode(playlist_id)
                if not started:
                    return jsonify({'error': 'NFC association already in progress'}), 409
                return jsonify({'status': 'association_initiated', 'playlist_id': playlist_id}), 200
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error initiating NFC association: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.api.route('/nfc/associate/complete', methods=['POST'])
        def complete_nfc_association():
            """Complete association after tag scan (called by NFC service or frontend when tag is read)"""
            try:
                data = request.get_json()
                playlist_id = data.get('playlist_id') if data else None
                tag_id = data.get('nfc_tag') if data else None
                if not playlist_id or not tag_id:
                    return jsonify({'error': 'playlist_id and nfc_tag are required'}), 400
                # Complete association in NFC service
                result = self.nfc_service.complete_association(playlist_id, tag_id)
                if result == 'already_associated':
                    return jsonify({'error': 'NFC tag already associated'}), 409
                if result == 'playlist_not_found':
                    return jsonify({'error': 'Playlist not found'}), 404
                if result == 'success':
                    return jsonify({'status': 'association_complete', 'playlist_id': playlist_id, 'nfc_tag': tag_id}), 200
                return jsonify({'error': 'Failed to associate tag'}), 500
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error completing NFC association: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.api.route('/nfc/disassociate', methods=['POST'])
        def disassociate_nfc_tag():
            """Disassociate an NFC tag from a playlist"""
            try:
                data = request.get_json()
                playlist_id = data.get('playlist_id') if data else None
                tag_id = data.get('nfc_tag') if data else None
                if not playlist_id or not tag_id:
                    return jsonify({'error': 'playlist_id and nfc_tag are required'}), 400
                result = self.nfc_service.disassociate_tag(playlist_id, tag_id)
                if result == 'not_associated':
                    return jsonify({'error': 'Tag not associated with playlist'}), 404
                if result == 'success':
                    return jsonify({'status': 'disassociated', 'playlist_id': playlist_id, 'nfc_tag': tag_id}), 200
                return jsonify({'error': 'Failed to disassociate tag'}), 500
            except Exception as e:
                logger.log(LogLevel.ERROR, f"NFC tag dissociation error: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.api.route('/nfc/status', methods=['GET'])
        def nfc_status():
            """Get current NFC association/listening status"""
            try:
                status = self.nfc_service.get_status()
                return jsonify(status), 200
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error getting NFC status: {str(e)}")
                return jsonify({'error': str(e)}), 500

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