#!/bin/bash
echo "========================================"
echo " 🎵  The Open Music Box Setup  🎵 "
echo "========================================"

# Local setup script for Raspberry Pi deployment
# Usage: sudo ./setup.sh
# This script must be run from the root of the extracted public_release folder

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check if the script is run with sudo
if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}This script must be run as root. Please use sudo.${NC}"
  exit 1
fi

# 1. Install required apt packages
REQUIRED_APT_PACKAGES=(python3 python3-venv python3-pip ffmpeg libasound2-dev libnss-mdns git i2c-tools python3-smbus python3-libgpiod libsdl2-mixer-2.0-0)
echo -e "${GREEN}Installing required apt packages...${NC}"
sudo apt-get update
sudo apt-get install -y "${REQUIRED_APT_PACKAGES[@]}"

# Enable I2C interface
echo -e "${GREEN}Enabling I2C interface...${NC}"
sudo raspi-config nonint do_i2c 0
echo "I2C interface enabled"

# 1.5. Configure audio system for WM8960
echo -e "${GREEN}Configuring audio system for WM8960...${NC}"
# Add user to audio group
sudo usermod -a -G audio $SUDO_USER

# Configure ALSA for WM8960
cat << 'EOF' | sudo tee /etc/asound.conf > /dev/null
pcm.!default {
    type plug
    slave {
        pcm "hw:0,0"
        format S16_LE
        rate 44100
    }
}

ctl.!default {
    type hw
    card 0
}

pcm.wm8960 {
    type hw
    card wm8960soundcard
    device 0
}

ctl.wm8960 {
    type hw
    card wm8960soundcard
}
EOF

sudo cp /tmp/asound.conf /etc/asound.conf
echo "Audio system configured for WM8960"

# 2. Créer un environnement virtuel Python et installer les dépendances dans le venv
# Correct the virtual environment path with absolute path logic
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"

# Create the virtual environment in the specified path
if [ ! -d "$VENV_PATH" ]; then
  echo -e "${GREEN}Creating Python virtual environment in $VENV_PATH...${NC}"
  python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
echo -e "${GREEN}Upgrading pip in venv...${NC}"
pip install --upgrade pip
echo -e "${GREEN}Installing Python dependencies from requirements.txt into venv...${NC}"
pip install -r "$SCRIPT_DIR/requirements.txt"
deactivate

# 3.5. Initialize audio system
echo -e "${GREEN}Initializing audio system...${NC}"
sudo alsactl init || true
sudo alsa force-reload || true

# Set audio device permissions
sudo chmod 666 /dev/snd/* 2>/dev/null || true

# 4. Déploiement du service systemd
# Ensure app.service exists before enabling
if [ -f "$SCRIPT_DIR/app.service" ]; then
  echo -e "${GREEN}Copying app.service to /etc/systemd/system/app.service...${NC}"
  sudo cp "$SCRIPT_DIR/app.service" /etc/systemd/system/app.service
  echo -e "${GREEN}Reloading systemd...${NC}"
  sudo systemctl daemon-reload
  # Enable and start the service
  sudo systemctl enable app
  sudo systemctl start app
else
  echo -e "${RED}app.service not found in $SCRIPT_DIR. Please ensure it is present.${NC}"
fi

echo -e "${GREEN}Setup complete!${NC}"
echo "→ Service installé : sudo systemctl status app"
echo "→ Configuration dans le fichier .env"
echo "→ Lancement : sudo systemctl start app"