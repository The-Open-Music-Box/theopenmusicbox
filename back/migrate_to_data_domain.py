#!/usr/bin/env python3
"""
Script de migration pour remplacer les anciens imports par le nouveau domaine data.
"""

import os
import re
from pathlib import Path

# Mappings des anciens vers nouveaux imports
IMPORT_MAPPINGS = {
    # Anciens modèles → Nouveaux modèles
    r'from app\.src\.domain\.models\.playlist import': 'from app.src.domain.data.models.playlist import',
    r'from app\.src\.domain\.models\.track import': 'from app.src.domain.data.models.track import',

    # Ancien service application → Nouveau service application
    r'from app\.src\.application\.services\.playlist_application_service import PlaylistApplicationService': 'from app.src.application.services.data_application_service import DataApplicationService',
    r'PlaylistApplicationService': 'DataApplicationService',

    # Dependencies
    r'get_playlist_application_service': 'get_data_application_service',

    # Playlist manager → Data services
    r'from app\.src\.domain\.audio\.playlist\.playlist_manager import PlaylistManager': '# PlaylistManager removed - use DataApplicationService',
    r'from app\.src\.domain\.protocols\.playlist_manager_protocol import PlaylistManagerProtocol': '# PlaylistManagerProtocol removed - use data domain services',
}

def migrate_file(file_path: Path):
    """Migrer un fichier Python."""
    if not file_path.suffix == '.py':
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Appliquer les remplacements
        for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
            content = re.sub(old_pattern, new_pattern, content)

        # Si le contenu a changé, l'écrire
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Migrated: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error migrating {file_path}: {e}")
        return False

def main():
    """Migration principale."""
    back_dir = Path(__file__).parent
    app_dir = back_dir / 'app' / 'src'

    migrated_count = 0

    # Parcourir tous les fichiers Python
    for py_file in app_dir.rglob('*.py'):
        if migrate_file(py_file):
            migrated_count += 1

    print(f"\n📊 Migration completed: {migrated_count} files migrated")

    # Afficher les fichiers qui utilisent encore les anciens imports
    print("\n🔍 Files that may still need manual migration:")
    for py_file in app_dir.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Vérifier les anciens imports
            old_imports = [
                'domain.models.playlist',
                'domain.models.track',
                'PlaylistApplicationService',
                'playlist_application_service',
                'PlaylistManager',
                'PlaylistManagerProtocol'
            ]

            for old_import in old_imports:
                if old_import in content:
                    print(f"  ⚠️ {py_file}: contains '{old_import}'")
                    break

        except Exception:
            continue

if __name__ == '__main__':
    main()