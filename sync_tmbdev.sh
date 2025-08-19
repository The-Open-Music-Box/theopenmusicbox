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
echo -e "${BOLD}${BLUE}🚀 Secure synchronization to Raspberry Pi${NC}"

# Project directories
readonly PROJECT_ROOT="$(dirname "$(realpath "$0")")"  

# Load configuration
CONFIG_FILE="${PROJECT_ROOT}/sync_tmbdev.config"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi

source "$CONFIG_FILE"

# Allow SSH_DEST override from command line
if [ ! -z "$1" ]; then
    SSH_DEST="$1"
fi
readonly BACK_DIR="${PROJECT_ROOT}/back"
readonly FRONT_DIR="${PROJECT_ROOT}/front"
readonly RELEASE_DEV_DIR="${PROJECT_ROOT}/${RELEASE_DEV_DIR}/tomb-rpi"

# SSH options with key path from config
readonly SSH_FULL_OPTS="${SSH_OPTS} -i ${SSH_KEY}"


# ----------------- SCRIPT -----------------

# Step 1: Create release_dev directory
echo -e "${BLUE}📦 Creating release_dev directory...${NC}"
mkdir -p "${RELEASE_DEV_DIR}"

# Step 2: Export backend package
echo -e "${BLUE}📦 Exporting backend package...${NC}"
"${BACK_DIR}/export_public_package.sh"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error exporting backend package.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend package exported successfully.${NC}"

# Step 3: Copy backend package to release_dev
echo -e "${BLUE}📦 Copying backend package to release_dev...${NC}"
cp -r "${PROJECT_ROOT}/public_release/tomb-rpi/"* "${RELEASE_DEV_DIR}/"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error copying backend package.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend package copied to release_dev.${NC}"

# Step 4: Build frontend
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

# Step 5: Copy frontend build to release_dev
echo -e "${BLUE}📋 Copying frontend build to release_dev...${NC}"
mkdir -p "${RELEASE_DEV_DIR}/app/static"
cp -r "${FRONT_DIR}/dist/"* "${RELEASE_DEV_DIR}/app/static/"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error copying frontend build.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend copied to release_dev.${NC}"

# Step 6: Upload to server
echo -e "${BLUE}🗂️  Creating remote directory if needed...${NC}"
ssh ${SSH_FULL_OPTS} "${SSH_DEST}" "mkdir -p ${REMOTE_DIR} && sudo chown admin:admin ${REMOTE_DIR}" 2>/dev/null

echo -e "${BLUE}📤 Synchronizing files with rsync...${NC}"

rsync -avzP --delete \
    --rsync-path="sudo rsync" \
    --no-owner --no-group \
    --chown=admin:admin \
    --ignore-errors \
    -e "ssh ${SSH_FULL_OPTS}" \
    "${RSYNC_EXCLUDES[@]}" \
    "${RELEASE_DEV_DIR}/" "${SSH_DEST}:${REMOTE_DIR}/" 2>/dev/null

RSYNC_EXIT=$?
if [ "$RSYNC_EXIT" -eq 0 ]; then
    echo -e "${GREEN}✅ Synchronization completed without errors.${NC}"
else
    echo -e "${RED}❌ Error during synchronization (code $RSYNC_EXIT).${NC}"
    exit $RSYNC_EXIT
fi

echo -e "${BLUE}🔧 Fixing permissions on the remote directory...${NC}"
ssh ${SSH_FULL_OPTS} "${SSH_DEST}" "sudo chown -R admin:admin ${REMOTE_DIR}" 2>/dev/null

echo -e "${GREEN}🎉 All done! Files are in ${REMOTE_DIR} on the RPi.${NC}"
