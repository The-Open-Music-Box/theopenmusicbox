#!/bin/bash

readonly GREEN="\033[0;32m"
readonly RED="\033[0;31m"
readonly YELLOW="\033[0;33m"
readonly BLUE="\033[0;34m"
readonly CYAN="\033[0;36m"
readonly BOLD="\033[1m"
readonly NC="\033[0m"

show_header() {
    echo -e "${GREEN}
    ========================================
    🎵  The Open Music Box Sync  🎵
    ========================================
    ${NC}"
    echo -e "${CYAN}${BOLD}Sync Local Files to tmbdev (Raspberry Pi)${NC}"
    echo ""
}

show_header

# ----------------- CONFIG -----------------
echo -e "${BOLD}${BLUE}🚀 Secure synchronization to Raspberry Pi (tomb)${NC}"

# SSH Alias (or user@host if you want to pass as an argument)
SSH_DEST="tomb"
if [ ! -z "$1" ]; then
    SSH_DEST="$1"
fi
readonly SSH_DEST

# Project directories
readonly PROJECT_ROOT="$(dirname "$(realpath "$0")")"
readonly BACK_DIR="${PROJECT_ROOT}/back"
readonly FRONT_DIR="${PROJECT_ROOT}/front"
readonly PUBLIC_RELEASE_DIR="${PROJECT_ROOT}/public_release/tomb-rpi"

# Remote directory on the Pi
readonly REMOTE_DIR="/home/admin/tomb"

# Common SSH options for all commands
readonly SSH_OPTS="-o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes -i ~/.ssh/musicbox_key"

# Files to exclude from synchronization
readonly RSYNC_EXCLUDES=(
    "--exclude=.DS_Store"
    "--exclude=__pycache__/"
    "--exclude=*.pyc"
    "--exclude=*.pyo"
    "--exclude=*.pyd"
    "--exclude=.Python"
    "--exclude=.venv"
    "--exclude=env/"
    "--exclude=app/data/"
    "--exclude=venv/"
    "--exclude=ENV/"
    "--exclude=env.bak/"
    "--exclude=venv.bak/"
    "--exclude=.coverage"
    "--exclude=htmlcov/"
    "--exclude=.tox/"
    "--exclude=.nox/"
    "--exclude=.hypothesis/"
    "--exclude=.pytest_cache/"
    "--exclude=.idea/"
    "--exclude=.vscode/"
    "--exclude=*.so"
    "--exclude=.git/"
    "--exclude=*.egg-info/"
    "--exclude=*.egg"
    "--exclude=dist/"
    "--exclude=build/"
    "--exclude=*.log"
    "--exclude=logs/"
    "--exclude=tmp/"
    "--exclude=temp/"
)

# ----------------- SCRIPT -----------------

# Step 1: Update public_release content
echo -e "${BLUE}📦 Exporting backend package...${NC}"
"${BACK_DIR}/export_public_package.sh"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error exporting backend package.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend package exported successfully.${NC}"

# Step 2: Build frontend
echo -e "${BLUE}🔨 Building frontend...${NC}"
# Save current directory
CURRENT_DIR=$(pwd)
cd "${FRONT_DIR}" || { echo -e "${RED}❌ Could not navigate to front directory.${NC}"; exit 1; }
npm run build
BUILD_EXIT=$?
# Return to original directory
cd "$CURRENT_DIR" || true
if [ $BUILD_EXIT -ne 0 ]; then
    echo -e "${RED}❌ Error building frontend.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend built successfully.${NC}"

# Step 3: Copy frontend build to public release
echo -e "${BLUE}📋 Copying frontend build to public release...${NC}"
mkdir -p "${PUBLIC_RELEASE_DIR}/app/static"
cp -r "${FRONT_DIR}/dist/"* "${PUBLIC_RELEASE_DIR}/app/static/"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error copying frontend build.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend copied to public release.${NC}"

# Step 4: Upload to server
echo -e "${BLUE}🗂️  Creating remote directory if needed...${NC}"
ssh ${SSH_OPTS} "${SSH_DEST}" "mkdir -p ${REMOTE_DIR} && sudo chown admin:admin ${REMOTE_DIR}" 2>/dev/null

echo -e "${BLUE}📤 Synchronizing files with rsync...${NC}"

rsync -avzP --delete \
    --rsync-path="sudo rsync" \
    --no-owner --no-group \
    --chown=admin:admin \
    --ignore-errors \
    -e "ssh ${SSH_OPTS}" \
    "${RSYNC_EXCLUDES[@]}" \
    "${PUBLIC_RELEASE_DIR}/" "${SSH_DEST}:${REMOTE_DIR}/" 2>/dev/null

RSYNC_EXIT=$?
if [ "$RSYNC_EXIT" -eq 0 ]; then
    echo -e "${GREEN}✅ Synchronization completed without errors.${NC}"
else
    echo -e "${RED}❌ Error during synchronization (code $RSYNC_EXIT).${NC}"
    exit $RSYNC_EXIT
fi

echo -e "${BLUE}🔧 Fixing permissions on the remote directory...${NC}"
ssh ${SSH_OPTS} "${SSH_DEST}" "sudo chown -R admin:admin ${REMOTE_DIR}" 2>/dev/null

echo -e "${GREEN}🎉 All done! Files are in ${REMOTE_DIR} on the RPi.${NC}"
