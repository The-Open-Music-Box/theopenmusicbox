#!/bin/bash
# Script d'installation des dépendances système pour TheOpenMusicBox sur Raspberry Pi
# À exécuter AVANT pip install -r requirements_pi.txt
set -e

sudo apt-get update
sudo apt-get install -y \
  python3-smbus \
  libasound2-dev \
  libffi-dev \
  build-essential \
  python3-dev \
  libi2c-dev \
  libjpeg-dev \
  libfreetype6-dev \
  libsdl2-dev \
  libsdl2-image-dev \
  libsdl2-mixer-dev \
  libsdl2-ttf-dev

echo "\nDépendances système installées. Vous pouvez maintenant activer votre venv et exécuter :"
echo "pip install -r requirements_pi.txt"
