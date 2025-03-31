# app/src/services/nfc_mapping_service.py

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List
from uuid import uuid4
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class NFCMappingService:
    def __init__(self, mapping_file_path):
        self.mapping_file_path = Path(mapping_file_path)

    def read_mapping(self) -> list:
        return json.loads(self.mapping_file_path.read_text())

    def save_mapping(self, mapping: list):
        self.mapping_file_path.write_text(json.dumps(mapping, indent=2))

    def add_playlist(self, playlist_data: Dict) -> str:
        mapping = self.read_mapping()

        # Construire les entrées de pistes avec les informations complètes
        tracks = []
        for idx, chapter in enumerate(playlist_data.get('tracks', []), 1):
            track = {
                "number": idx,
                "title": chapter.get('title', f'Track {idx}'),
                "filename": chapter.get('filename', f"Track {idx}.mp3"),
                "duration": "",
                "play_counter": 0
            }

            # Ajouter des informations de timing si disponibles
            if 'start_time' in chapter or 'end_time' in chapter:
                track["start_time"] = str(chapter.get('start_time', 0))
                track["end_time"] = str(chapter.get('end_time', 0))

            tracks.append(track)

        new_playlist = {
            "id": str(uuid4()),
            "type": "playlist",
            "idtagnfc": "",
            "title": playlist_data['title'],
            "youtube_id": playlist_data['youtube_id'],
            "path": playlist_data['folder'],
            "tracks": tracks,
            "created_at": datetime.utcnow().isoformat() + 'Z'
        }

        mapping.append(new_playlist)
        self.save_mapping(mapping)
        return new_playlist['id']