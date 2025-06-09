#!/bin/bash
# Configuration
LOCAL_DIR="app" # Only syncing the app folder
REMOTE_USER="admin"
REMOTE_HOST="tmbdev.local"
REMOTE_DIR="/home/admin/app" # Remote directory
SSH_KEY="$HOME/.ssh/musicbox_key"

# Colors for logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log() {
  echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

log_error() {
  echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Create exclusion file
create_exclude_file() {
  local exclude_file=$(mktemp)
  echo ".git" > "$exclude_file"
  echo "node_modules" >> "$exclude_file"
  echo ".DS_Store" >> "$exclude_file"
  echo "logs/" >> "$exclude_file"
  echo "src/data/uploads/" >> "$exclude_file"
  echo "$exclude_file"
}

# Simple synchronization function (no monitoring)
sync_app_folder() {
  local start_time=$(date +%s)
  log "Starting app folder synchronization..."

  # Check if local directory exists
  if [ ! -d "$LOCAL_DIR" ]; then
    log_error "Local directory '$LOCAL_DIR' does not exist!"
    return 1
  fi

  # Create exclusion file
  local exclude_file=$(create_exclude_file)

  log "Syncing app folder to remote server..."
  
  # Run rsync to sync files
  rsync -aiz \
    -e "ssh -i $SSH_KEY" \
    --exclude-from="$exclude_file" \
    --exclude="src/data/uploads/" \
    --chmod=Du+rwx,Fu+rw \
    "$LOCAL_DIR/" \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
    
  # Synchroniser les uploads séparément pour préserver les fichiers existants
  if [ -d "$LOCAL_DIR/src/data/uploads" ]; then
    log "Syncing uploads folder separately (preserving existing files)..."
    rsync -aiz \
      -e "ssh -i $SSH_KEY" \
      --exclude-from="$exclude_file" \
      --chmod=Du+rwx,Fu+rw \
      --protect-args \
      "$LOCAL_DIR/src/data/uploads/" \
      "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/src/data/uploads/"
  else
    log "Local uploads directory not found, creating remote directory structure..."
    ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR/src/data/uploads && chmod -R 755 $REMOTE_DIR/src/data/uploads"
  fi
    
  local sync_status=$?

  # Cleanup
  rm -f "$exclude_file"

  local end_time=$(date +%s)
  local duration=$((end_time - start_time))

  if [ $sync_status -eq 0 ]; then
    log_success "App folder synchronized successfully in $duration seconds"
    return 0
  else
    log_error "Synchronization failed"
    return 1
  fi
}

# Print header
echo -e "${GREEN}=======================================================${NC}"
echo -e "${GREEN}    App Folder Synchronization Script                  ${NC}"
echo -e "${GREEN}=======================================================${NC}"
echo ""

# Test SSH connection
log "Testing SSH connection to server..."
ssh -i "$SSH_KEY" -q "$REMOTE_USER@$REMOTE_HOST" exit
if [ $? -ne 0 ]; then
  log_error "Cannot connect to server. Check your SSH settings."
  exit 1
fi

# Run synchronization once and exit
sync_app_folder
exit $?
