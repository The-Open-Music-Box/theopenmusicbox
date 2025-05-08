#!/bin/bash
# Configuration
LOCAL_DIR="app" # Change this according to your folder
REMOTE_USER="admin"
REMOTE_HOST="tmbdev.local"
REMOTE_DIR="/home/admin/app" # Change this according to your destination
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

log_warning() {
  echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Verify and create remote directory if necessary
prepare_remote_dir() {
  log "Preparing remote directory..."

  # Check if user can sudo without password
  CAN_SUDO=$(ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "sudo -n true && echo yes || echo no" 2>/dev/null)

  if [ "$CAN_SUDO" = "yes" ]; then
    # Use sudo to create and configure directory
    ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "sudo mkdir -p $REMOTE_DIR && sudo chown -R $REMOTE_USER:$REMOTE_USER $REMOTE_DIR && sudo chmod -R 755 $REMOTE_DIR" 2>/dev/null
    if [ $? -eq 0 ]; then
      log_success "Remote directory successfully prepared (with sudo)"
      return 0
    fi
  else
    # Try without sudo
    ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR && chmod -R 755 $REMOTE_DIR" 2>/dev/null
    if [ $? -eq 0 ]; then
      log_success "Remote directory successfully prepared"
      return 0
    fi
  fi

  log_error "Unable to prepare remote directory. Check permissions."
  return 1
}

# Create exclusion file
create_exclude_file() {
  local exclude_file=$(mktemp)
  echo ".git" > "$exclude_file"
  echo "node_modules" >> "$exclude_file"
  echo ".DS_Store" >> "$exclude_file"
  echo "logs/" >> "$exclude_file"
  echo "$exclude_file"
}

# Main synchronization function
sync_changes() {
  local start_time=$(date +%s)
  log "Starting synchronization..."

  # Check if local directory exists
  if [ ! -d "$LOCAL_DIR" ]; then
    log_error "Local directory '$LOCAL_DIR' does not exist!"
    return 1
  fi

  # Prepare remote directory
  prepare_remote_dir

  # Create exclusion file
  local exclude_file=$(create_exclude_file)
  local changed_count=0

  # Create a temporary directory for modified files lists
  local tmp_dir=$(mktemp -d)
  local modified_list="$tmp_dir/modified.txt"
  local deleted_list="$tmp_dir/deleted.txt"

  # Synchronize regular files - only modified files
  log "Checking for modified files..."

  # Run rsync in dry-run mode to check what files need to be transferred
  # Send all output to a file to process later
  rsync -aiz --update --itemize-changes --dry-run \
    -e "ssh -i $SSH_KEY" \
    --exclude-from="$exclude_file" \
    --exclude="src/data/uploads/" \
    --chmod=Du+rwx,Fu+rw \
    "$LOCAL_DIR/" \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" > "$tmp_dir/rsync_changes.txt" 2>/dev/null

  # Extract just the modified files and count them
  grep "^[><]f" "$tmp_dir/rsync_changes.txt" | awk '{print $2}' > "$modified_list"
  local modified_count=$(wc -l < "$modified_list" | xargs)

  if [ "$modified_count" -gt 0 ]; then
    log "Transferring $modified_count modified files..."

    # Show a spinner during synchronization
    echo -n "Transferring... "

    # Run actual rsync with all output suppressed
    rsync -aiz --update \
      -e "ssh -i $SSH_KEY" \
      --exclude-from="$exclude_file" \
      --exclude="src/data/uploads/" \
      --chmod=Du+rwx,Fu+rw \
      "$LOCAL_DIR/" \
      "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" > /dev/null 2>&1

    echo -e "${GREEN}Done${NC}"

    # Display concise summary
    echo -e "\n${CYAN}Modified files transferred: ${GREEN}$modified_count${NC}"

    # Show only the first 5 modified files if there are many
    if [ "$modified_count" -gt 5 ]; then
      echo -e "${CYAN}First 5 modified files:${NC}"
      head -5 "$modified_list" | while read -r file; do
        [ ! -z "$file" ] && echo -e "${GREEN}✓${NC} $file"
      done
      echo -e "... and ${YELLOW}$(($modified_count - 5))${NC} more files"
    else
      echo -e "${CYAN}Modified files:${NC}"
      cat "$modified_list" | while read -r file; do
        [ ! -z "$file" ] && echo -e "${GREEN}✓${NC} $file"
      done
    fi

    changed_count=$((changed_count + modified_count))
  else
    echo -e "${CYAN}No regular files to synchronize${NC}"
  fi

  # Handle uploads directory separately
  log "Synchronizing uploads directory..."

  # Only sync if the directory exists
  if [ -d "$LOCAL_DIR/src/data/uploads" ]; then
    # Check if any files in uploads need to be transferred
    rsync -aiz --update --itemize-changes --dry-run \
      -e "ssh -i $SSH_KEY" \
      --exclude-from="$exclude_file" \
      --chmod=Du+rwx,Fu+rw \
      "$LOCAL_DIR/src/data/uploads/" \
      "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/src/data/uploads/" > "$tmp_dir/uploads_changes.txt" 2>/dev/null

    local uploads_modified=$(grep "^[><]f" "$tmp_dir/uploads_changes.txt" | wc -l | xargs)

    if [ "$uploads_modified" -gt 0 ]; then
      log "Transferring $uploads_modified files in uploads directory..."

      # Show a spinner during synchronization
      echo -n "Transferring uploads... "

      # Use rsync with proper options for handling special filenames
      rsync -aiz --update \
        -e "ssh -i $SSH_KEY" \
        --exclude-from="$exclude_file" \
        --chmod=Du+rwx,Fu+rw \
        --protect-args \
        "$LOCAL_DIR/src/data/uploads/" \
        "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/src/data/uploads/" > /dev/null 2>&1

      echo -e "${GREEN}Done${NC}"

      changed_count=$((changed_count + uploads_modified))
      log_success "Uploads directory synchronized"
    else
      log "No files to update in uploads directory"
    fi
  fi

  # Handle deleted files
  log "Checking for deleted files..."

  rsync -aiz --delete --dry-run \
    -e "ssh -i $SSH_KEY" \
    --exclude-from="$exclude_file" \
    "$LOCAL_DIR/" \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" | grep "^deleting" | sed 's/^deleting //' > "$deleted_list"

  local deleted_count=$(wc -l < "$deleted_list" | xargs)

  if [ "$deleted_count" -gt 0 ]; then
    log "Deleting $deleted_count files on remote server..."

    # Run rsync to delete files
    rsync -aiz --delete \
      -e "ssh -i $SSH_KEY" \
      --exclude-from="$exclude_file" \
      --chmod=Du+rwx,Fu+rw \
      "$LOCAL_DIR/" \
      "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" > /dev/null 2>&1

    echo -e "\n${CYAN}Deleted files:${NC}"

    # Show only first 5 deleted files if there are many
    if [ "$deleted_count" -gt 5 ]; then
      head -5 "$deleted_list" | while read -r file; do
        [ ! -z "$file" ] && echo -e "${RED}✗${NC} $file"
      done
      echo -e "... and ${YELLOW}$(($deleted_count - 5))${NC} more files"
    else
      cat "$deleted_list" | while read -r file; do
        [ ! -z "$file" ] && echo -e "${RED}✗${NC} $file"
      done
    fi

    changed_count=$((changed_count + deleted_count))
  else
    log "No files to delete"
  fi

  # Cleanup
  rm -f "$exclude_file"
  rm -rf "$tmp_dir"

  local end_time=$(date +%s)
  local duration=$((end_time - start_time))

  # Display a cleaner summary
  echo ""
  echo -e "${GREEN}==================== SYNC SUMMARY ====================${NC}"
  echo -e "${CYAN}Total files processed:${NC} ${GREEN}$changed_count${NC}"
  echo -e "${CYAN}Time taken:${NC} ${GREEN}$duration${NC} seconds"

  # Check for any permission issues and fix them
  if ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "find $REMOTE_DIR -not -perm -u+rw 2>/dev/null | wc -l" | grep -q "^0$"; then
    echo -e "${CYAN}Permissions:${NC} ${GREEN}OK${NC}"
  else
    echo -e "${CYAN}Permissions:${NC} ${YELLOW}Fixing...${NC}"
    ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "sudo chown -R $REMOTE_USER:$REMOTE_USER $REMOTE_DIR && sudo chmod -R u+rw $REMOTE_DIR" 2>/dev/null
    echo -e "${CYAN}Permissions:${NC} ${GREEN}Fixed${NC}"
  fi

  echo -e "${GREEN}====================================================${NC}"

  if [ "$changed_count" -eq 0 ]; then
    log_success "No changes needed - already in sync"
  else
    log_success "Synchronization completed successfully"
  fi
}

# SSH connection test
log "Testing SSH connection to server..."
ssh -i "$SSH_KEY" -q "$REMOTE_USER@$REMOTE_HOST" exit
if [ $? -ne 0 ]; then
  log_error "Cannot connect to server. Check your SSH settings."
  exit 1
fi

# Function to detect and ignore multiple rapid changes
sync_with_debounce() {
  local last_sync=0
  local debounce_delay=2  # delay in seconds

  fswatch -o "$LOCAL_DIR" | while read f; do
    current_time=$(date +%s)
    time_diff=$((current_time - last_sync))

    if [ $time_diff -ge $debounce_delay ]; then
      echo ""  # Empty line to separate from previous events
      log "Change detected in: $f"
      sync_changes
      last_sync=$(date +%s)
    else
      log "Ignoring change (too close): $f"
    fi
  done
}

# Display welcome message
clear
echo -e "${GREEN}=======================================================${NC}"
echo -e "${GREEN}    Incremental Synchronization Script                  ${NC}"
echo -e "${GREEN}=======================================================${NC}"
echo ""
log "Starting synchronization script..."

# Initial synchronization before starting monitoring
log "Running initial synchronization..."
sync_changes

# Monitor for changes
log "Starting file monitoring..."
sync_with_debounce