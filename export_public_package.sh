#!/bin/bash
# Export a public package with only the app folder and production requirements
# Usage: ./export_public_package.sh <target_dir>

set -e

SRC_DIR="$(dirname "$0")"
APP_SRC="$SRC_DIR/app"
REQ_SRC="$SRC_DIR/requirements/prod.txt"
README_SRC="$SRC_DIR/README.md"
SERVICE_SRC="$SRC_DIR/app.service"

# If no argument, default to ../public_release
if [ -z "$1" ]; then
  TARGET_DIR="$SRC_DIR/../public_release"
  echo "No target_dir provided. Using default: $TARGET_DIR"
else
  TARGET_DIR="$1"
fi

mkdir -p "$TARGET_DIR"

# Nettoyer le répertoire cible avant l'export (supprime tout sauf les dossiers spécifiques)
find "$TARGET_DIR" -mindepth 1 -not -path "$TARGET_DIR/app/data/upload*" -not -path "$TARGET_DIR/app/data/database*" -not -path "$TARGET_DIR/app/logs*" -delete 2>/dev/null || true

# Copy app folder, excluding caches, logs, uploads, and database folders
rsync -av --delete \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='uploads' \
  --exclude='logs' \
  --exclude='data/upload' \
  --exclude='data/database' \
  "$APP_SRC" "$TARGET_DIR/"

# Flatten requirements: replace '-r base.txt' with contents of base.txt
REQ_DST="$TARGET_DIR/requirements.txt"

awk -v src_dir="$SRC_DIR/requirements" '
  /^-r / {
    sub(/^-r /, "", $0);
    file = src_dir "/" $0;
    while ((getline line < file) > 0) print line;
    close(file);
    next;
  }
  { print }
' "$REQ_SRC" > "$REQ_DST"

# Remove comments and blank lines from the output
sed -i.bak "/^\s*#/d;/^\s*$/d" "$REQ_DST" && rm "$REQ_DST.bak"

# Warn if requirements.txt is empty
if [ ! -s "$REQ_DST" ]; then
  echo "Warning: requirements.txt is empty after export. Check prod.txt content."
  # Uncomment the next line to fail the script on empty requirements
  # exit 1
fi

# Copy README, LICENSE, service file, setup script, and start_app.py if present
[ -f "$README_SRC" ] && cp "$README_SRC" "$TARGET_DIR/"
[ -f "$SERVICE_SRC" ] && cp "$SERVICE_SRC" "$TARGET_DIR/"
LICENSE_SRC="$SRC_DIR/LICENSE"
[ -f "$LICENSE_SRC" ] && cp "$LICENSE_SRC" "$TARGET_DIR/"
SETUP_SRC="$SRC_DIR/setup.sh"
[ -f "$SETUP_SRC" ] && cp "$SETUP_SRC" "$TARGET_DIR/"
START_APP_SRC="$SRC_DIR/start_app.py"
[ -f "$START_APP_SRC" ] && cp "$START_APP_SRC" "$TARGET_DIR/" && chmod +x "$TARGET_DIR/start_app.py"

echo "Export complete. Public package is in $TARGET_DIR."
