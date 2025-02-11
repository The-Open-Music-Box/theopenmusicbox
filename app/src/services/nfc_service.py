# app/src/services/nfc_service.py

# app/src/services/nfc_service.py

import json
import uuid
from pathlib import Path

class NFCMappingService:
    def __init__(self, mapping_file_path):
        self.mapping_file_path = Path(mapping_file_path)

    def read_mapping(self):
        if not self.mapping_file_path.exists():
            return []
        return json.loads(self.mapping_file_path.read_text())

    def save_mapping(self, mapping):
        self.mapping_file_path.write_text(json.dumps(mapping, indent=2))

    def add_playlist_mapping(self, folder_name, playlist_id):
        mapping = self.read_mapping()
        mapping.append({
            "id": str(uuid.uuid4()),
            "type": "playlist",
            "idtagnfc": "",
            "path": folder_name
        })
        self.save_mapping(mapping)