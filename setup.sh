#!/bin/bash
echo "========================================"
echo " 🎵  The Open Music Box Setup  🎵 "
echo "========================================"

# Local setup script for Raspberry Pi deployment
# Usage: sudo ./setup.sh
# This script must be run from the root of the extracted public_release folder

set -e

GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 1. Install required apt packages
REQUIRED_APT_PACKAGES=(python3 python3-venv python3-pip ffmpeg libasound2-dev libnss-mdns git i2c-tools python3-smbus python3-libgpiod)
echo -e "${GREEN}Installing required apt packages...${NC}"
sudo apt-get update
sudo apt-get install -y "${REQUIRED_APT_PACKAGES[@]}"

# Enable I2C interface
echo -e "${GREEN}Enabling I2C interface...${NC}"
sudo raspi-config nonint do_i2c 0
echo "I2C interface enabled"

# 2. Créer un environnement virtuel Python et installer les dépendances dans le venv
if [ ! -d "app/venv" ]; then
  echo -e "${GREEN}Creating Python virtual environment in venv...${NC}"
  python3 -m venv venv
fi

source venv/bin/activate
echo -e "${GREEN}Upgrading pip in venv...${NC}"
pip install --upgrade pip
echo -e "${GREEN}Installing Python dependencies from requirements.txt into venv...${NC}"
pip install -r requirements.txt
deactivate

# 4. Déploiement du service systemd
if [ -f "app.service" ]; then
  echo -e "${GREEN}Copie de app.service dans /etc/systemd/system/app.service...${NC}"
  sudo cp app.service /etc/systemd/system/app.service
  echo -e "${GREEN}Rechargement de systemd...${NC}"
  sudo systemctl daemon-reload
fi

echo -e "${GREEN}Setup complete!${NC}"
echo "→ Service installé : sudo systemctl status app"
echo "→ Configuration dans le fichier .env"
echo "→ Lancement : sudo systemctl start app"