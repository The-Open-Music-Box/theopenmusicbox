# back/app/src/routes/playlist_routes.py

from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict, Any
from app.src.services.playlist_service import PlaylistService
from app.src.services.upload_service import UploadService
from app.src.dependencies import get_config
from pathlib import Path

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.playlist_service import PlaylistService
from app.src.services.upload_service import UploadService
from app.src.helpers.exceptions import InvalidFileError, ProcessingError
from app.src.model.playlist import Playlist
from app.src.dependencies import get_config, get_audio

logger = ImprovedLogger(__name__)

router = APIRouter(prefix="/playlists", tags=["playlists"])

def get_playlist_or_404(playlist_id: str, config=Depends(get_config)) -> Tuple[Optional[Dict[str, Any]], List, PlaylistService]:
    playlist_service = PlaylistService(config)
    mapping = playlist_service.read_playlist_file()
    playlist = next((p for p in mapping if p['id'] == playlist_id), None)
    return playlist, mapping, playlist_service

def create_playlist_model(playlist_data: Dict[str, Any], config, track_filter=None, debug_missing=False) -> Playlist:
    # Sanitize playlist_data['path'] to avoid double uploads/
    original_path = playlist_data['path']
    sanitized_path = original_path
    if sanitized_path.startswith('uploads/'):
        sanitized_path = sanitized_path[len('uploads/'):]
        logger.log(LogLevel.WARNING, f"[SANITIZE] Removed leading 'uploads/' from playlist path: {original_path} -> {sanitized_path}")
    if sanitized_path.startswith('/'):
        sanitized_path = sanitized_path[1:]
        logger.log(LogLevel.WARNING, f"[SANITIZE] Removed leading '/' from playlist path: {original_path} -> {sanitized_path}")
    base_path = Path(config.upload_folder) / sanitized_path
    logger.log(LogLevel.INFO, f"[DEBUG] Playlist '{playlist_data.get('title', playlist_data.get('id', ''))}' base_path: {base_path}")
    filtered_tracks = [t for t in playlist_data['tracks'] if track_filter(t)] if track_filter else playlist_data['tracks']
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

@router.delete("/{playlist_id}", status_code=200)
async def delete_playlist(playlist_id: str, config=Depends(get_config)):
    """Delete a playlist and its files"""
    playlist_service = PlaylistService(config)
    success = playlist_service.delete_playlist(playlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Playlist not found or could not be deleted")
    return {"status": "success", "playlist_id": playlist_id}

from fastapi import Body

class TrackResponse(BaseModel):
    number: int
    title: str
    filename: str
    duration: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    play_counter: Optional[int] = 0

class PlaylistResponse(BaseModel):
    id: str
    type: str
    title: str
    path: str
    created_at: str
    tracks: List[TrackResponse]

class PlaylistListResponse(BaseModel):
    playlists: List[PlaylistResponse]
    page: int
    page_size: int

class PlaylistCreateRequest(BaseModel):
    title: str

class ReorderTracksRequest(BaseModel):
    order: List[int]

class DeleteTracksRequest(BaseModel):
    tracks: List[int]

@router.get("/", response_model=PlaylistListResponse)
async def list_playlists(
    page: int = 1,
    page_size: int = 50,
    config=Depends(get_config)
):
    """Get all playlists with pagination support"""
    playlist_service = PlaylistService(config)
    playlists = playlist_service.get_all_playlists(page=page, page_size=page_size)
    # Convert tracks to TrackResponse for OpenAPI
    for playlist in playlists:
        playlist["tracks"] = [TrackResponse(**track) for track in playlist.get("tracks", [])]
    return PlaylistListResponse(
        playlists=[PlaylistResponse(**p) for p in playlists],
        page=page,
        page_size=page_size
    )

@router.post("/", status_code=201, response_model=PlaylistResponse)
async def create_playlist(
    body: PlaylistCreateRequest, config=Depends(get_config)
):
    """Create a new playlist"""
    playlist_service = PlaylistService(config)
    playlist = playlist_service.create_playlist(body.title)
    playlist["tracks"] = []  # Always start empty
    return PlaylistResponse(**playlist)

@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: str, config=Depends(get_config)
):
    """Get a playlist by ID"""
    playlist_service = PlaylistService(config)
    playlist = playlist_service.get_playlist_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    playlist["tracks"] = [TrackResponse(**track) for track in playlist.get("tracks", [])]
    return PlaylistResponse(**playlist)

@router.delete("/{playlist_id}", status_code=200)
async def delete_playlist(playlist_id: str, config=Depends(get_config)):
    """Delete a playlist and its files"""
    playlist_service = PlaylistService(config)
    success = playlist_service.delete_playlist(playlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Playlist not found or could not be deleted")
    return {"status": "success", "playlist_id": playlist_id}

@router.post("/{playlist_id}/upload", status_code=200)
async def upload_files(
    playlist_id: str,
    files: List[UploadFile] = File(...),
    config=Depends(get_config)
):
    """Upload files to a specific playlist"""
    playlist_service = PlaylistService(config)
    playlist = playlist_service.get_playlist_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    upload_service = UploadService(config.upload_folder)
    uploaded_files = []
    failed_files = []
    for file in files:
        try:
            filename, metadata = upload_service.process_upload(file, playlist['path'])
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
        except Exception as e:
            failed_files.append({
                "filename": file.filename,
                "error": str(e)
            })
            continue
    if uploaded_files:
        playlist_service.repository.save_playlist_file(playlist)  # Adjust as needed
    response = {
        "status": "success" if uploaded_files else "error",
        "uploaded_files": uploaded_files,
        "failed_files": failed_files
    }
    if not uploaded_files:
        raise HTTPException(status_code=400, detail=response)
    return response

@router.patch("/{playlist_id}/tracks", status_code=200)
async def reorder_tracks(
    playlist_id: str,
    body: ReorderTracksRequest,
    config=Depends(get_config)
):
    """Reorder tracks in a playlist"""
    playlist_service = PlaylistService(config)
    success = playlist_service.reorder_tracks(playlist_id, body.order)
    if not success:
        raise HTTPException(status_code=400, detail="Could not reorder tracks")
    return {"status": "success"}

@router.delete("/{playlist_id}/tracks/{track_id}", status_code=200)
async def delete_track(
    playlist_id: str,
    track_id: str,
    config=Depends(get_config)
):
    """Remove a track from a playlist"""
    playlist_service = PlaylistService(config)
    success = playlist_service.delete_track(playlist_id, track_id)
    if not success:
        raise HTTPException(status_code=404, detail="Track not found or could not be deleted")
    return {"status": "success", "track_id": track_id}

@router.delete("/{playlist_id}/tracks", status_code=200)
async def delete_tracks(
    playlist_id: str,
    body: DeleteTracksRequest,
    config=Depends(get_config)
):
    """Delete multiple tracks from a playlist"""
    playlist_service = PlaylistService(config)
    success = playlist_service.delete_tracks(playlist_id, body.tracks)
    if not success:
        raise HTTPException(status_code=400, detail="Could not delete tracks")
    return {"status": "success"}

@router.post("/{playlist_id}/tracks", status_code=201)
async def upload_tracks(
    playlist_id: str,
    files: List[UploadFile] = File(...),
    config=Depends(get_config)
):
    """Upload files to a specific playlist"""
    upload_service = UploadService(config.upload_folder)
    playlist_service = PlaylistService(config)
    playlist = playlist_service.get_playlist_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    try:
        uploaded_files = upload_service.save_files(playlist, files)
        playlist_service.add_tracks_to_playlist(playlist_id, uploaded_files)
        return {"status": "success", "uploaded": uploaded_files}
    except InvalidFileError as e:
        logger.log(LogLevel.ERROR, f"Invalid file upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.log(LogLevel.ERROR, f"Error uploading tracks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{playlist_id}/tracks", status_code=200)
async def reorder_tracks(
    playlist_id: str,
    body: dict = Body(...),
    config=Depends(get_config)
):
    """Reorder tracks in a playlist"""
    new_order = body.get('order', [])
    if not new_order or not isinstance(new_order, list):
        raise HTTPException(status_code=400, detail="Invalid track order")
    playlist_service = PlaylistService(config)
    success = playlist_service.reorder_tracks(playlist_id, new_order)
    if not success:
        raise HTTPException(status_code=400, detail="Could not reorder tracks")
    return {"status": "success"}

@router.delete("/{playlist_id}/tracks/{track_id}", status_code=200)
async def delete_track(
    playlist_id: str,
    track_id: str,
    config=Depends(get_config)
):
    """Remove a track from a playlist"""
    playlist_service = PlaylistService(config)
    success = playlist_service.delete_track(playlist_id, track_id)
    if not success:
        raise HTTPException(status_code=404, detail="Track not found or could not be deleted")
    return {"status": "success", "track_id": track_id}

from app.src.dependencies import get_audio

@router.post("/playback/{playlist_id}/start", status_code=200)
async def start_playlist(
    playlist_id: str,
    config=Depends(get_config),
    audio=Depends(get_audio)
):
    """Start playing a specific playlist"""
    if not audio:
        raise HTTPException(status_code=503, detail="Audio system not available")
    playlist_service = PlaylistService(config)
    playlist = playlist_service.get_playlist_by_id(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    playlist_model = create_playlist_model(playlist, config, debug_missing=True)
    if not playlist_model.tracks:
        raise HTTPException(status_code=404, detail="No valid tracks found in playlist. Check logs for missing file details.")
    audio.set_playlist(playlist_model)
    return {"status": "success", "message": f"Started playing playlist: {playlist['title']}"}

@router.post("/play/{playlist_id}/track/{track_number}", status_code=200)
async def play_track(
    playlist_id: str,
    track_number: int,
    config=Depends(get_config),
    audio=Depends(get_audio)
):
    """Play a specific track from a playlist"""
    if not audio:
        raise HTTPException(status_code=503, detail="Audio system not available")
    playlist, _, _ = get_playlist_or_404(playlist_id, config)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    # Filter tracks to start from the specified track
    track = next((t for t in playlist['tracks'] if t['number'] == track_number), None)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    # Create playlist model starting from the specified track
    playlist_model = create_playlist_model(
        playlist,
        config,
        track_filter=lambda t: t['number'] >= track_number
    )
    if not playlist_model.tracks:
        raise HTTPException(status_code=404, detail="No valid tracks found")
    # Start playback
    audio.set_playlist(playlist_model)
    return {"status": "success", "message": f"Started playing track: {track['title']}"}

@router.post("/control/{action}", status_code=200)
async def control_playlist(
    action: str,
    audio=Depends(get_audio)
):
    """Control the currently playing playlist"""
    if not audio:
        raise HTTPException(status_code=503, detail="Audio system not available")
    actions = {
        'play': audio.resume,
        'resume': audio.resume,
        'pause': audio.pause,
        'next': audio.next_track,
        'previous': audio.previous_track,
        'stop': audio.stop
    }
    if action not in actions:
        raise HTTPException(status_code=400, detail="Invalid action")
    actions[action]()
    return {"status": "success", "action": action}

@router.post("/{playlist_id}/upload", status_code=200)
async def upload_files(
    playlist_id: str,
    files: List[UploadFile] = File(...),
    config=Depends(get_config)
):
    """Upload files to a specific playlist (with progress, no websocket emit here)"""
    playlist, mapping, playlist_service = get_playlist_or_404(playlist_id, config)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    upload_service = UploadService(config.upload_folder)
    uploaded_files = []
    failed_files = []
    total_files = len(files)
    for index, file in enumerate(files, 1):
        try:
            if not file.filename:
                continue
            filename, metadata = upload_service.process_upload(file, playlist['path'])
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
            # Websocket progress emit skipped for now
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
            raise HTTPException(status_code=400, detail=response)
    return response


@router.delete("/{playlist_id}/tracks", status_code=200)
async def delete_tracks(
    playlist_id: str,
    body: dict = Body(...),
    config=Depends(get_config)
):
    """Delete multiple tracks from a playlist"""
    track_numbers = body.get('tracks', [])
    if not track_numbers or not isinstance(track_numbers, list):
        raise HTTPException(status_code=400, detail="Invalid track numbers")
    playlist, mapping, playlist_service = get_playlist_or_404(playlist_id, config)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    # Validate track numbers
    current_tracks = {track['number'] for track in playlist['tracks']}
    if not set(track_numbers).issubset(current_tracks):
        raise HTTPException(status_code=400, detail="One or more track numbers do not exist")
    # Delete files and remove tracks
    playlist_path = Path(config.upload_folder) / playlist['path']
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
    return {"status": "success"}
