import os
from pathlib import Path
import sys
import json

# Usage: python check_playlist_files.py /absolute/path/to/upload_folder /absolute/path/to/playlist.json

def main(upload_folder, playlist_json):
    with open(playlist_json, 'r', encoding='utf-8') as f:
        playlist_data = json.load(f)
    
    playlist_path = playlist_data['playlist']['path']
    tracks = playlist_data['playlist']['tracks']
    base_path = Path(upload_folder) / playlist_path

    missing = []
    present = []
    for track in tracks:
        track_file = base_path / track['filename']
        if track_file.exists():
            present.append(str(track_file))
        else:
            missing.append(str(track_file))
    
    print(f"Checked {len(tracks)} tracks in playlist '{playlist_data['playlist']['title']}'\n")
    print(f"Present files: {len(present)}")
    for f in present:
        print(f"  [OK] {f}")
    print(f"\nMissing files: {len(missing)}")
    for f in missing:
        print(f"  [MISSING] {f}")
    if missing:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python check_playlist_files.py /absolute/path/to/upload_folder /absolute/path/to/playlist.json")
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
