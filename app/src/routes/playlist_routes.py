from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, FastAPI
from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict, Any
from app.src.services.playlist_service import PlaylistService
from app.src.services.upload_service import UploadService
from app.src.dependencies import get_config, get_audio
from pathlib import Path

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.helpers.exceptions import InvalidFileError, ProcessingError
from app.src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class PlaylistRoutes:
    """
    Registers the playlist-related API routes with the FastAPI app.
    """
    def __init__(self, app: FastAPI):
        self.app = app
        self.router = APIRouter(prefix="/playlists", tags=["playlists"])
        self._register_routes()

    def register(self):
        self.app.include_router(self.router)

    def _register_routes(self):
        @self.router.get("/", response_model=List[Dict[str, Any]])
        async def list_playlists(page: int = 1, page_size: int = 50, config=Depends(get_config)):
            """Get all playlists with pagination support"""
            playlist_service = PlaylistService(config)
            playlists = playlist_service.get_all_playlists(page=page, page_size=page_size)
            return playlists

        @self.router.post("/", response_model=Dict[str, Any])
        async def create_playlist(body: dict = Body(...), config=Depends(get_config)):
            """Create a new playlist"""
            playlist_service = PlaylistService(config)
            title = body.get("title")
            if not isinstance(title, str) or not title.strip():
                raise HTTPException(status_code=422, detail="Missing or invalid 'title' field")
            created = playlist_service.create_playlist(title)
            return created

        @self.router.get("/{playlist_id}", response_model=Dict[str, Any])
        async def get_playlist(playlist_id: str, config=Depends(get_config)):
            """Get a playlist by ID"""
            playlist_service = PlaylistService(config)
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return playlist

        @self.router.delete("/{playlist_id}", response_model=Dict[str, Any])
        async def delete_playlist(playlist_id: str, config=Depends(get_config)):
            """Delete a playlist and its files"""
            playlist_service = PlaylistService(config)
            try:
                deleted = playlist_service.delete_playlist(playlist_id)
                return deleted
            except ValueError:
                raise HTTPException(status_code=404, detail=f"Playlist {playlist_id} not found")

        @self.router.post("/{playlist_id}/upload", response_model=Dict[str, Any])
        async def upload_files(
            playlist_id: str,
            files: List[UploadFile] = File(...),
            config=Depends(get_config)
        ):
            """Upload files to a specific playlist (with progress, no websocket emit here)"""
            playlist_service = PlaylistService(config)
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            upload_service = UploadService(config.upload_folder)
            uploaded_files = []
            failed_files = []
            for file in files:
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
                except (InvalidFileError, ProcessingError) as e:
                    failed_files.append({
                        "filename": file.filename,
                        "error": str(e)
                    })
                    continue
            if uploaded_files:
                playlist_service.save_playlist_file()
            response = {
                "status": "success" if uploaded_files else "error",
                "uploaded_files": uploaded_files
            }
            if failed_files:
                response["failed_files"] = failed_files
                if not uploaded_files:
                    raise HTTPException(status_code=400, detail=response)
            return response

        @self.router.post("/{playlist_id}/reorder", response_model=Dict[str, Any])
        async def reorder_tracks(
            playlist_id: str,
            body: dict = Body(...),
            config=Depends(get_config)
        ):
            """Reorder tracks in a playlist"""
            order = body.get('order', [])
            if not order or not isinstance(order, list):
                raise HTTPException(status_code=400, detail="Invalid order")
            playlist_service = PlaylistService(config)
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            success = playlist_service.reorder_tracks(playlist_id, order)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to reorder tracks")
            return {"status": "success"}

        @self.router.delete("/{playlist_id}/tracks", response_model=Dict[str, Any])
        async def delete_tracks(
            playlist_id: str,
            body: dict = Body(...),
            config=Depends(get_config)
        ):
            """Delete multiple tracks from a playlist"""
            track_numbers = body.get('tracks', [])
            if not track_numbers or not isinstance(track_numbers, list):
                raise HTTPException(status_code=400, detail="Invalid track numbers")
            playlist_service = PlaylistService(config)
            playlist = playlist_service.get_playlist_by_id(playlist_id)
            if not playlist:
                raise HTTPException(status_code=404, detail="Playlist not found")
            success = playlist_service.delete_tracks(playlist_id, track_numbers)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to delete tracks")
            return {"status": "success"}

        @self.router.post("/{playlist_id}/start", response_model=Dict[str, Any])
        async def start_playlist(
            playlist_id: str,
            config=Depends(get_config),
            audio=Depends(get_audio)
        ):
            """Start playing a specific playlist"""
            if not audio:
                raise HTTPException(status_code=503, detail="Audio system not available")
            playlist_service = PlaylistService(config)
            success = playlist_service.start_playlist(playlist_id, audio)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to start playlist")
            return {"status": "success"}

        @self.router.post("/{playlist_id}/play/{track_number}", response_model=Dict[str, Any])
        async def play_track(
            playlist_id: str,
            track_number: int,
            config=Depends(get_config),
            audio=Depends(get_audio)
        ):
            """Play a specific track from a playlist"""
            if not audio:
                raise HTTPException(status_code=503, detail="Audio system not available")
            playlist_service = PlaylistService(config)
            success = playlist_service.play_track(playlist_id, track_number, audio)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to play track")
            return {"status": "success"}

        @self.router.post("/control", response_model=Dict[str, Any])
        async def control_playlist(
            action: str = Body(..., embed=True),
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

