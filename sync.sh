#!/bin/bash

# Configuration
LOCAL_DIR="app"  # Changez ceci selon votre dossier
REMOTE_USER="admin"
REMOTE_HOST="tmbdev.local"
REMOTE_DIR="/home/admin/app"  # Changez ceci selon votre destination
SSH_KEY="$HOME/.ssh/musicbox_key"

# Couleurs pour les logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Fonction de logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCÈS: $1${NC}"
}

# Fonction de synchronisation
sync_changes() {
    local start_time=$(date +%s)
    log "Début de la synchronisation..."

    rsync -avz --progress --delete \
        -e "ssh -i $SSH_KEY" \
        --exclude '.git' \
        --exclude 'node_modules' \
        --exclude '.DS_Store' \
        "$LOCAL_DIR/" \
        "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" 2>&1 | while read line; do
            echo -e "${BLUE}[RSYNC]${NC} $line"
        done

    local exit_status=${PIPESTATUS[0]}
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ $exit_status -eq 0 ]; then
        log_success "Synchronisation terminée en $duration secondes"
    else
        log_error "La synchronisation a échoué avec le code $exit_status"
    fi
}

# Surveillance des changements
log "Démarrage de la surveillance des fichiers..."
fswatch -o "$LOCAL_DIR" | while read f; do
    log "Changement détecté dans: $f"
    sync_changes
done
