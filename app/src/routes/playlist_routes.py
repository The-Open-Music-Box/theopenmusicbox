# app/src/routes/playlist_routes.py

from flask import Blueprint, current_app, request, jsonify
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import uuid
import datetime
import re

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.services import PlaylistService, UploadService
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

    def _get_playlist_or_404(self, playlist_id: str) -> Tuple[Optional[Dict[str, Any]], List, PlaylistService]:
        """
        Get a playlist by ID or return None.

        Args:
            playlist_id: ID of the playlist to retrieve

        Returns:
            Tuple containing: (playlist, mapping, playlist_service) or (None, mapping, playlist_service)
        """
        playlist_service = PlaylistService(current_app.container.config)
        mapping = playlist_service.read_playlist_file()

        playlist = next((p for p in mapping if p['id'] == playlist_id), None)
        return playlist, mapping, playlist_service

    def _create_playlist_model(self, playlist_data: Dict[str, Any], track_filter=None, debug_missing=False) -> Playlist:
        """
        Create a Playlist model object from playlist data.

        Args:
            playlist_data: Dictionary containing playlist information
            track_filter: Optional function to filter tracks

        Returns:
            A Playlist model object
        """
        base_path = Path(current_app.container.config.upload_folder) / playlist_data['path']
        logger.log(LogLevel.INFO, f"[DEBUG] Playlist '{playlist_data.get('title', playlist_data.get('id', ''))}' base_path: {base_path}")

        if track_filter:
            filtered_tracks = [t for t in playlist_data['tracks'] if track_filter(t)]
        else:
            filtered_tracks = playlist_data['tracks']

        missing_tracks = []
        track_paths = []
        for track in filtered_tracks:
            track_path = base_path / track['filename']
            logger.log(LogLevel.INFO, f"[DEBUG] Checking track_path: {track_path}")
            if Path(track_path).exists():
                track_paths.append(str(track_path))
            else:
                missing_tracks.append(str(track_path))
        if missing_tracks:
            logger.log(LogLevel.WARNING, f"[DEBUG] Missing tracks for playlist '{playlist_data.get('title', playlist_data.get('id', ''))}': {missing_tracks}")

        if debug_missing and missing_tracks:
            logger.log(LogLevel.ERROR, f"Missing files for playlist '{playlist_data['title']}': {missing_tracks}")
            # Optionally, you could return missing_tracks as part of the model or as a separate value
        return Playlist.from_files(playlist_data['title'], track_paths)

    def _validate_track_numbers(self, playlist: Dict[str, Any], track_numbers: List[int]) -> bool:
        """
        Validate that track numbers exist in the playlist.

        Args:
            playlist: Playlist dictionary
            track_numbers: List of track numbers to validate

        Returns:
            True if all track numbers are valid
        """
        current_tracks = {track['number'] for track in playlist['tracks']}
        return set(track_numbers).issubset(current_tracks)

    def _init_routes(self):
        @self.api.route('/playlists', methods=['GET'])
        def list_playlists():
            """Get all playlists with pagination support"""
            try:
                page = int(request.args.get('page', 1))
                page_size = int(request.args.get('page_size', 50))
                playlist_service = PlaylistService(current_app.container.config)
                playlists = playlist_service.get_all_playlists(page=page, page_size=page_size)
                return jsonify({
                    "playlists": playlists,
                    "page": page,
                    "page_size": page_size
                }), 200
            except Exception as e:
                import traceback
                logger.log(LogLevel.ERROR, f"Error listing playlists: {str(e)}\n{traceback.format_exc()}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlists/<playlist_id>', methods=['GET'])
        def get_playlist(playlist_id):
            """Get a playlist by ID with track pagination support"""
            try:
                track_page = int(request.args.get('track_page', 1))
                track_page_size = int(request.args.get('track_page_size', 1000))
                playlist_service = PlaylistService(current_app.container.config)
                playlist = playlist_service.get_playlist_by_id(playlist_id, track_page=track_page, track_page_size=track_page_size)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404
                return jsonify({
                    "playlist": playlist,
                    "track_page": track_page,
                    "track_page_size": track_page_size
                }), 200
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error getting playlist: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlists/<playlist_id>', methods=['DELETE'])
        def delete_playlist(playlist_id):
            """Delete a playlist and its files"""
            try:
                playlist_service = PlaylistService(current_app.container.config)
                success = playlist_service.delete_playlist(playlist_id)
                if not success:
                    return jsonify({"error": "Playlist not found or could not be deleted"}), 404
                return jsonify({"status": "success", "playlist_id": playlist_id}), 200
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error deleting playlist: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlists', methods=['POST'])
        def create_playlist():
            """Create a new playlist"""
            try:
                data = request.get_json()
                if not data or not data.get('title'):
                    return jsonify({"error": "Playlist title is required"}), 400
                playlist_service = PlaylistService(current_app.container.config)
                playlist = playlist_service.create_playlist(data['title'])
                return jsonify({"status": "success", "playlist": playlist}), 201
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Playlist creation error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlists/<playlist_id>/tracks', methods=['POST'])
        def upload_tracks(playlist_id):
            """Upload files to a specific playlist"""
            try:
                if 'files' not in request.files:
                    return jsonify({"error": "No files part in the request"}), 400
                files = request.files.getlist('files')
                upload_service = UploadService(current_app.container.config.upload_folder)
                playlist_service = PlaylistService(current_app.container.config)
                playlist = playlist_service.get_playlist_by_id(playlist_id)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404
                uploaded_files = upload_service.save_files(playlist, files)
                playlist_service.add_tracks_to_playlist(playlist_id, uploaded_files)
                return jsonify({"status": "success", "uploaded": uploaded_files}), 201
            except InvalidFileError as e:
                logger.log(LogLevel.ERROR, f"Invalid file upload: {str(e)}")
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error uploading tracks: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlists/<playlist_id>/tracks', methods=['PATCH'])
        def reorder_tracks(playlist_id):
            """Reorder tracks in a playlist"""
            try:
                new_order = request.get_json().get('order', [])
                if not new_order or not isinstance(new_order, list):
                    return jsonify({"error": "Invalid track order"}), 400
                playlist_service = PlaylistService(current_app.container.config)
                success = playlist_service.reorder_tracks(playlist_id, new_order)
                if not success:
                    return jsonify({"error": "Could not reorder tracks"}), 400
                return jsonify({"status": "success"}), 200
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Track reordering error: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playlists/<playlist_id>/tracks/<track_id>', methods=['DELETE'])
        def delete_track(playlist_id, track_id):
            """Remove a track from a playlist"""
            try:
                playlist_service = PlaylistService(current_app.container.config)
                success = playlist_service.delete_track(playlist_id, track_id)
                if not success:
                    return jsonify({"error": "Track not found or could not be deleted"}), 404
                return jsonify({"status": "success", "track_id": track_id}), 200
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error deleting track: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.api.route('/playback/<playlist_id>/start', methods=['POST'])
        def start_playlist(playlist_id):
            """Start playing a specific playlist"""
            try:
                audio = current_app.container.audio
                if not audio:
                    return jsonify({"error": "Audio system not available"}), 503
                playlist_service = PlaylistService(current_app.container.config)
                playlist = playlist_service.get_playlist_by_id(playlist_id)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404
                playlist_model = self._create_playlist_model(playlist, debug_missing=True)
                if not playlist_model.tracks:
                    return jsonify({"error": "No valid tracks found in playlist. Check logs for missing file details."}), 404
                audio.set_playlist(playlist_model)
                return jsonify({"status": "success", "message": f"Started playing playlist: {playlist['title']}"})
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

                playlist, _, _ = self._get_playlist_or_404(playlist_id)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                # Filter tracks to start from the specified track
                track = next((t for t in playlist['tracks'] if t['number'] == track_number), None)
                if not track:
                    return jsonify({"error": "Track not found"}), 404

                # Create playlist model starting from the specified track
                playlist_model = self._create_playlist_model(
                    playlist,
                    track_filter=lambda t: t['number'] >= track_number
                )

                if not playlist_model.tracks:
                    return jsonify({"error": "No valid tracks found"}), 404

                # Start playback
                audio.set_playlist(playlist_model)

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
                    'resume': audio.resume,
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

                playlist, mapping, playlist_service = self._get_playlist_or_404(playlist_id)
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

                        # Add track to playlist
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

                        # Emit progress via websocket
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
                    playlist_service.save_playlist_file(mapping)

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


        @self.api.route('/playlists/<playlist_id>/tracks', methods=['DELETE'])
        def delete_tracks(playlist_id):
            """Delete multiple tracks from a playlist"""
            try:
                if not request.is_json:
                    return jsonify({"error": "Content-Type must be application/json"}), 400

                track_numbers = request.json.get('tracks', [])
                if not track_numbers or not isinstance(track_numbers, list):
                    return jsonify({"error": "Invalid track numbers"}), 400

                playlist, mapping, playlist_service = self._get_playlist_or_404(playlist_id)
                if not playlist:
                    return jsonify({"error": "Playlist not found"}), 404

                # Validate track numbers
                if not self._validate_track_numbers(playlist, track_numbers):
                    return jsonify({"error": "One or more track numbers do not exist"}), 400

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
                for idx, track in enumerate(sorted(playlist['tracks'], key=lambda x: x['number']), 1):
                    track['number'] = idx

                playlist_service.save_playlist_file(mapping)
                return jsonify({"status": "success"})

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Track deletion error: {str(e)}")
                return jsonify({"error": str(e)}), 500
