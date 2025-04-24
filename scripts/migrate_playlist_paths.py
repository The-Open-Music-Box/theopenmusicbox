"""
Migration script to clean up playlist 'path' fields by removing any leading 'uploads/' from the path.
This script updates the playlist storage (JSON or DB) in-place.

USAGE:
    python scripts/migrate_playlist_paths.py

- Make sure to backup your data before running this script.
- This script assumes playlists are stored in a JSON file or SQLite DB.
- Adjust the script as needed for your actual storage format.
"""

import os
import json
from pathlib import Path
import sqlite3

# --- CONFIGURATION ---
# Set these paths as appropriate for your app
PLAYLIST_JSON_PATH = Path('app/src/data/playlists.json')  # If using JSON
PLAYLIST_DB_PATH = Path('app/src/data/tmb.db')            # If using SQLite DB

# --- JSON MIGRATION ---
def migrate_json():
    if not PLAYLIST_JSON_PATH.exists():
        print(f"No playlist JSON file found at {PLAYLIST_JSON_PATH}, skipping JSON migration.")
        return
    with open(PLAYLIST_JSON_PATH, 'r', encoding='utf-8') as f:
        playlists = json.load(f)

    changed = False
    for p in playlists:
        orig = p.get('path', '')
        if orig.startswith('uploads/'):
            p['path'] = orig[len('uploads/'):]
            print(f"Updated: {orig} -> {p['path']}")
            changed = True

    if changed:
        with open(PLAYLIST_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(playlists, f, indent=2, ensure_ascii=False)
        print("JSON playlist paths migrated.")
    else:
        print("No changes needed in JSON playlist paths.")

# --- SQLITE MIGRATION ---
def migrate_sqlite():
    if not PLAYLIST_DB_PATH.exists():
        print(f"No playlist DB file found at {PLAYLIST_DB_PATH}, skipping SQLite migration.")
        return
    conn = sqlite3.connect(PLAYLIST_DB_PATH)
    cur = conn.cursor()
    # Adjust table/column names as appropriate
    try:
        cur.execute("SELECT id, path FROM playlists")
        rows = cur.fetchall()
        changed = False
        for pid, orig in rows:
            if orig and orig.startswith('uploads/'):
                new_path = orig[len('uploads/'):]
                cur.execute("UPDATE playlists SET path = ? WHERE id = ?", (new_path, pid))
                print(f"Updated: {orig} -> {new_path}")
                changed = True
        if changed:
            conn.commit()
            print("SQLite playlist paths migrated.")
        else:
            print("No changes needed in SQLite playlist paths.")
    except Exception as e:
        print(f"Error during SQLite migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_json()
    migrate_sqlite()
    print("Migration complete.")
