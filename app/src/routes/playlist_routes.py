# app/src/routes/playlist_routes.py

from flask import Blueprint, current_app, request, jsonify
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from typing import List
import uuid
import datetime

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.services import NFCMappingService, UploadService
from src.helpers.exceptions import InvalidFileError, ProcessingError
from src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class PlaylistRoutes:
    def __init__(self, app):
        self.app = app
        self.api = Blueprint('playlist_api', __name__)

    def register(self):
        self._init_routes()
        self.app.register_blueprint(self.api, url_prefix='/api')

    def _init_routes(self):
        @self.api.route('/playlist/<playlist_id>/play', methods=['POST'])
        def start_playlist(playlist_id):
            """Start playing a specific playlist"""
            try:
                audio = current_app.container.audio
                if not audio:
                    return jsonify({"error": "Audio system not available"}), 503

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                playlist_data = next((p for p in mapping if p['id'] == playlist_id), None)
                if not playlist_data:
                    return jsonify({"error": "Playlist not found"}), 404

                # Construire la liste des chemins de fichiers
                base_path = Path(current_app.container.config.upload_folder) / playlist_data['path']
                track_paths = [
                    str(base_path / track['filename'])
                    for track in playlist_data['tracks']
                    if Path(base_path / track['filename']).exists()
                ]

                if not track_paths:
                    return jsonify({"error": "No valid tracks found in playlist"}), 404

                # Create a Playlist object
                playlist = Playlist.from_files(playlist_data['title'], track_paths)
                audio.set_playlist(playlist)

                return jsonify({
                    "status": "success",
                    "message": f"Started playing playlist: {playlist_data['title']}"
                })

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error starting playlist: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlist/<playlist_id>/track/<int:track_number>/play', methods=['POST'])
        def play_track(playlist_id, track_number):
            """Play a specific track from a playlist"""
            try:
                audio = current_app.container.audio
                if not audio:
                    return jsonify({"error": "Audio system not available"}), 503

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                playlist_data = next((p for p in mapping if p['id'] == playlist_id), None)
                if not playlist_data:
                    return jsonify({"error": "Playlist not found"}), 404

                track = next((t for t in playlist_data['tracks'] if t['number'] == track_number), None)
                if not track:
                    return jsonify({"error": "Track not found"}), 404

                # Construire la liste des chemins à partir du morceau sélectionné
                base_path = Path(current_app.container.config.upload_folder) / playlist_data['path']
                track_paths = [
                    str(base_path / t['filename'])
                    for t in sorted(playlist_data['tracks'], key=lambda x: x['number'])
                    if t['number'] >= track_number and Path(base_path / t['filename']).exists()
                ]

                if not track_paths:
                    return jsonify({"error": "No valid tracks found"}), 404

                # Create a Playlist object starting from the selected track
                playlist = Playlist.from_files(playlist_data['title'], track_paths)
                audio.set_playlist(playlist)

                return jsonify({
                    "status": "success",
                    "message": f"Started playing track: {track['title']}"
                })

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error playing track: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlist/control/<action>', methods=['POST'])
        def control_playlist(action):
            """Control the currently playing playlist"""
            try:
                audio = current_app.container.audio
                if not audio:
                    return jsonify({"error": "Audio system not available"}), 503

                actions = {
                    'play': audio.resume,
                    'pause': audio.pause,
                    'next': audio.next_track,
                    'previous': audio.previous_track,
                    'stop': audio.stop
                }

                if action not in actions:
                    return jsonify({"error": "Invalid action"}), 400

                actions[action]()
                return jsonify({"status": "success", "action": action})

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Playlist control error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlist/<playlist_id>/upload', methods=['POST'])
        def upload_files(playlist_id):
            """Upload files to a specific playlist"""
            try:
                if 'files' not in request.files:
                    return jsonify({"error": "No files provided"}), 400

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                playlist = next((p for p in mapping if p['id'] == playlist_id), None)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                upload_service = UploadService(current_app.container.config.upload_folder)
                uploaded_files = []
                failed_files = []

                files = request.files.getlist('files')
                total_files = len(files)

                for index, file in enumerate(files, 1):
                    try:
                        if not file.filename:
                            continue

                        filename, metadata = upload_service.process_upload(file, playlist['path'])

                        # Ajouter le morceau à la playlist avec les métadonnées
                        track = {
                            "number": len(playlist['tracks']) + 1,
                            "title": metadata['title'],
                            "artist": metadata['artist'],
                            "album": metadata['album'],
                            "duration": metadata['duration'],
                            "filename": filename,
                            "play_counter": 0
                        }
                        playlist['tracks'].append(track)
                        uploaded_files.append({
                            "filename": filename,
                            "metadata": metadata
                        })

                        # Émettre la progression
                        current_app.socketio.emit('upload_progress', {
                            'playlist_id': playlist_id,
                            'current': index,
                            'total': total_files,
                            'filename': filename
                        })

                    except (InvalidFileError, ProcessingError) as e:
                        failed_files.append({
                            "filename": file.filename,
                            "error": str(e)
                        })
                        continue

                if uploaded_files:
                    nfc_service.save_mapping(mapping)

                response = {
                    "status": "success" if uploaded_files else "error",
                    "uploaded_files": uploaded_files
                }

                if failed_files:
                    response["failed_files"] = failed_files
                    if not uploaded_files:
                        return jsonify(response), 400

                return jsonify(response)

            except Exception as e:
                logger.log(LogLevel.ERROR, f"File upload error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlist/<playlist_id>', methods=['DELETE'])
        def delete_playlist(playlist_id):
            """Delete a playlist and its files"""
            try:
                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                playlist = next((p for p in mapping if p['id'] == playlist_id), None)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                # Delete files
                playlist_path = Path(current_app.container.config.upload_folder) / playlist['path']
                if playlist_path.exists():
                    for track in playlist['tracks']:
                        file_path = playlist_path / track['filename']
                        if file_path.exists():
                            file_path.unlink()
                    playlist_path.rmdir()

                # Remove from mapping
                mapping.remove(playlist)
                nfc_service.save_mapping(mapping)

                return jsonify({"status": "success"})

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Playlist deletion error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlist/<playlist_id>/tracks', methods=['DELETE'])
        def delete_tracks(playlist_id):
            """Delete multiple tracks from a playlist"""
            try:
                if not request.is_json:
                    return jsonify({"error": "Content-Type must be application/json"}), 400

                track_numbers = request.json.get('tracks', [])
                if not track_numbers or not isinstance(track_numbers, list):
                    return jsonify({"error": "Invalid track numbers"}), 400

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                playlist = next((p for p in mapping if p['id'] == playlist_id), None)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                # Delete files and remove tracks
                playlist_path = Path(current_app.container.config.upload_folder) / playlist['path']
                tracks_to_remove = []

                for track in playlist['tracks']:
                    if track['number'] in track_numbers:
                        file_path = playlist_path / track['filename']
                        if file_path.exists():
                            file_path.unlink()
                        tracks_to_remove.append(track)

                for track in tracks_to_remove:
                    playlist['tracks'].remove(track)

                # Reindex remaining tracks
                for idx, track in enumerate(playlist['tracks'], 1):
                    track['number'] = idx

                nfc_service.save_mapping(mapping)
                return jsonify({"status": "success"})

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Track deletion error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlist/<playlist_id>/reorder', methods=['POST'])
        def reorder_tracks(playlist_id):
            """Reorder tracks in a playlist"""
            try:
                if not request.is_json:
                    return jsonify({"error": "Content-Type must be application/json"}), 400

                new_order = request.json.get('order', [])
                if not new_order or not isinstance(new_order, list):
                    return jsonify({"error": "Invalid track order"}), 400

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                playlist = next((p for p in mapping if p['id'] == playlist_id), None)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                # Verify all track numbers are valid
                current_tracks = {track['number'] for track in playlist['tracks']}
                if set(new_order) != current_tracks:
                    return jsonify({"error": "Invalid track numbers in order"}), 400

                # Create a map of current tracks by number
                tracks_by_number = {track['number']: track for track in playlist['tracks']}

                # Reorder tracks
                playlist['tracks'] = [tracks_by_number[num] for num in new_order]

                # Update track numbers
                for idx, track in enumerate(playlist['tracks'], 1):
                    track['number'] = idx

                nfc_service.save_mapping(mapping)
                return jsonify({"status": "success"})

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Track reordering error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlist', methods=['POST'])
        def create_playlist():
            """Create a new playlist"""
            try:
                if not request.is_json:
                    return jsonify({"error": "Content-Type must be application/json"}), 400

                data = request.json
                if not data.get('title'):
                    return jsonify({"error": "Playlist title is required"}), 400

                nfc_service = NFCMappingService(current_app.container.config.nfc_mapping_file)
                mapping = nfc_service.read_mapping()

                # Générer un ID unique pour la playlist
                playlist_id = str(uuid.uuid4())

                # Créer la nouvelle playlist
                new_playlist = {
                    "id": playlist_id,
                    "type": "playlist",
                    "title": data['title'],
                    "path": f"playlist_{playlist_id}",
                    "tracks": [],
                    "nfc_tag": None,  # Tag NFC initialement non associé
                    "created_at": datetime.datetime.now().isoformat()
                }

                # Ajouter la playlist au mapping
                mapping.append(new_playlist)
                nfc_service.save_mapping(mapping)

                # Créer le dossier pour la playlist
                playlist_path = Path(current_app.container.config.upload_folder) / new_playlist['path']
                playlist_path.mkdir(parents=True, exist_ok=True)

                return jsonify({
                    "status": "success",
                    "playlist": new_playlist
                })

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Playlist creation error: {str(e)}")
                return jsonify({"error": str(e)}), 500