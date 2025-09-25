# Raspberry Pi Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying The Open Music Box on a Raspberry Pi, from SD card preparation to full system configuration with automated deployment scripts.

## System Requirements

### Hardware Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Raspberry Pi** | Zero 2W | 4B (1GB RAM) |
| **SD Card** | 16GB Class 10 | 32GB+ U1/A1 |
| **Audio** | 3.5mm jack | WM8960 I2S HAT |
| **Power** | 5V 2.5A USB-C | 5V 3A + battery pack |
| **Network** | WiFi | Ethernet + WiFi |

### Optional Hardware
- **NFC Reader**: RC522 module for tag functionality
- **Physical Controls**: Rotary encoder, push buttons
- **Status LEDs**: RGB LEDs for visual feedback

### Software Requirements
- **OS**: Raspberry Pi OS (64-bit recommended)
- **Python**: 3.9+ with pip
- **Git**: For code deployment
- **System**: 4GB+ free storage space

## Step 1: SD Card Preparation

### Using Raspberry Pi Imager

1. **Download Raspberry Pi Imager**
   ```bash
   # macOS
   brew install --cask raspberry-pi-imager

   # Windows: Download from raspberry.org
   # Linux: Use package manager or snap
   ```

2. **Flash the SD Card**
   - Select "Raspberry Pi OS (64-bit)" from the list
   - Choose your SD card (16GB minimum)
   - Click the gear icon for advanced options

3. **Configure Advanced Settings**
   - ✅ Enable SSH (use password authentication)
   - ✅ Set username: `admin` (or your preference)
   - ✅ Set password: Choose a secure password
   - ✅ Configure WiFi (SSID and password)
   - ✅ Set locale settings (timezone, keyboard)
   - ✅ Enable SSH public key authentication (if you have keys)

4. **Write to SD Card**
   - Click "Write" and wait for completion
   - Safely eject the SD card

### First Boot Configuration

1. **Insert SD Card** into Raspberry Pi
2. **Power on** the device
3. **Wait 2-3 minutes** for first boot setup
4. **Find the Pi's IP address**:
   ```bash
   # From your computer
   ping theopenmusicbox.local
   # OR check your router's admin panel
   ```

## Step 2: SSH Access Configuration

### Automated SSH Key Setup

The project includes a convenient SSH setup script:

```bash
# From your development machine
./setup_ssh_key_to_rpi.sh
```

**The script will:**
1. ✅ Configure SSH directory and permissions
2. ✅ List available SSH keys or create new ones
3. ✅ Test connectivity to the Raspberry Pi
4. ✅ Copy public key to the device
5. ✅ Configure SSH config for easy access
6. ✅ Test passwordless authentication

**Expected Output:**
```
🎵  The Open Music Box SSH Setup  🎵
========================================

Enhanced SSH Key Setup for Raspberry Pi

✅ Using existing key: tomb
👤 Username: admin
🌐 IP address: theopenmusicbox.local
✅ Host theopenmusicbox.local is reachable
✅ Public key copied successfully
✅ SSH config updated successfully
✅ Passwordless SSH authentication working!

💻 You can now connect with: ssh tomb
```

### Manual SSH Setup (Alternative)

If you prefer manual setup:

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -f ~/.ssh/tomb -N ""

# Copy public key to Pi
ssh-copy-id -i ~/.ssh/tomb.pub admin@theopenmusicbox.local

# Add to SSH config
echo "Host tomb
  HostName theopenmusicbox.local
  User admin
  IdentityFile ~/.ssh/tomb" >> ~/.ssh/config
```

### Test SSH Connection

```bash
ssh tomb
# Should connect without password prompt
```

## Step 3: System Deployment

### Automated Deployment

Use the deployment script for one-command setup:

```bash
./deploy.sh --prod tomb
```

**What the deployment script does:**

1. **System Updates**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade -y
   sudo apt-get install git python3-pip
   ```

2. **Audio Hardware Setup** (if WM8960 HAT detected)
   ```bash
   git clone https://github.com/waveshare/WM8960-Audio-HAT
   cd WM8960-Audio-HAT
   sudo ./install.sh
   sudo reboot  # Automatic reboot for audio drivers
   ```

3. **Application Installation**
   ```bash
   git clone [your-repo-url] /home/admin/tomb
   cd /home/admin/tomb
   chmod +x setup.sh
   sudo ./setup.sh
   ```

4. **Service Configuration**
   - Creates systemd service files
   - Configures environment variables
   - Sets up log rotation
   - Configures auto-start on boot

### Manual Deployment Steps

If you prefer step-by-step manual deployment:

#### 1. System Preparation
```bash
ssh tomb

# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y git python3-pip python3-venv sqlite3 ffmpeg

# Create application directory
sudo mkdir -p /opt/openmusicbox
sudo chown admin:admin /opt/openmusicbox
```

#### 2. Clone Repository
```bash
cd /opt/openmusicbox
git clone [your-repo-url] .
```

#### 3. Python Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 4. Configuration
```bash
# Create configuration file
cp config/.env.example config/.env

# Edit configuration
nano config/.env
```

**Key Configuration Options:**
```bash
# Database
DATABASE_URL="sqlite:///data/music.db"

# Audio Backend (auto-detected)
AUDIO_BACKEND="wm8960"  # or "system", "dummy"

# Network
HOST="0.0.0.0"
PORT=5004

# Hardware
NFC_ENABLED=true
GPIO_ENABLED=true

# File Storage
UPLOAD_DIR="/opt/openmusicbox/data/uploads"
MAX_UPLOAD_SIZE=100  # MB
```

#### 5. Database Initialization
```bash
# Create data directory
mkdir -p data/uploads

# Initialize database
python -c "from app.db.database import init_db; init_db()"
```

#### 6. Service Setup
```bash
# Create systemd service
sudo cp scripts/openmusicbox.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable openmusicbox
```

## Step 4: Audio System Configuration

### WM8960 Audio HAT Setup

If using the recommended WM8960 Audio HAT:

```bash
# Clone and install drivers
git clone https://github.com/waveshare/WM8960-Audio-HAT
cd WM8960-Audio-HAT
sudo ./install.sh

# Reboot to load drivers
sudo reboot
```

### Audio Testing

```bash
# Test audio output
aplay /usr/share/sounds/alsa/Front_Center.wav

# Check audio devices
aplay -l

# Adjust volume
alsamixer
```

### Audio Configuration

Edit `/boot/config.txt` if needed:
```bash
# Enable I2S for WM8960
dtparam=i2s=on

# Disable built-in audio (optional)
dtparam=audio=off
```

## Step 5: Service Management

### Start the Service

```bash
# Start the service
sudo systemctl start openmusicbox

# Check status
sudo systemctl status openmusicbox

# View logs
sudo journalctl -fu openmusicbox --output=cat
```

### Service Commands

```bash
# Service management
sudo systemctl start openmusicbox     # Start service
sudo systemctl stop openmusicbox      # Stop service
sudo systemctl restart openmusicbox   # Restart service
sudo systemctl status openmusicbox    # Check status

# Log viewing
journalctl -u openmusicbox -f         # Follow logs
journalctl -u openmusicbox --since "1 hour ago"  # Recent logs
```

## Step 6: Network Access

### Web Interface

After successful deployment, access the web interface:

- **URL**: `http://[raspberry-pi-ip]:5004`
- **Local URL**: `http://theopenmusicbox.local:5004`
- **Default Port**: 5004

### Firewall Configuration (if needed)

```bash
# Allow HTTP traffic
sudo ufw allow 5004/tcp

# Check firewall status
sudo ufw status
```

## Step 7: Continuous Deployment

### Sync Script for Development

Use the sync script for ongoing development:

```bash
./sync_tmbdev.sh
```

**What it does:**
- Synchronizes local changes to the Pi
- Restarts services if needed
- Validates configuration deployment
- Shows deployment status

**Expected Output:**
```
🎵  The Open Music Box Sync  🎵
========================================
✅ Synchronization completed without errors.
🔧 Fixing permissions on the remote directory...
🔍 Validating configuration deployment...
✅ Configuration file (.env) successfully deployed to server.
🎉 All done! Files are in /opt/openmusicbox on the RPi.
```

### Auto-Update Setup

For automatic updates (optional):

```bash
# Create update script
sudo tee /usr/local/bin/update-openmusicbox.sh << EOF
#!/bin/bash
cd /opt/openmusicbox
git pull origin main
sudo systemctl restart openmusicbox
EOF

sudo chmod +x /usr/local/bin/update-openmusicbox.sh

# Add to crontab for daily updates (optional)
echo "0 2 * * * /usr/local/bin/update-openmusicbox.sh" | sudo crontab -
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u openmusicbox -n 50

# Check configuration
sudo systemctl status openmusicbox

# Verify Python dependencies
source /opt/openmusicbox/venv/bin/activate
pip list
```

#### Audio Not Working
```bash
# Check audio devices
aplay -l

# Test system audio
speaker-test -t wav

# Check WM8960 driver
lsmod | grep snd

# Reinstall audio drivers if needed
cd WM8960-Audio-HAT && sudo ./install.sh
```

#### Network Access Issues
```bash
# Check service is listening
sudo netstat -tlnp | grep 5004

# Test local connection
curl http://localhost:5004/api/health

# Check firewall
sudo ufw status
```

#### NFC Reader Issues
```bash
# Check SPI is enabled
ls /dev/spi*

# Enable SPI in raspi-config
sudo raspi-config
# Interface Options > SPI > Enable

# Check NFC reader connection
python3 -c "from app.hardware.nfc import NFCReader; NFCReader().test_connection()"
```

### Log Analysis

```bash
# System logs
sudo journalctl -p err                # Error messages only
sudo dmesg | grep -i error            # Hardware errors

# Application logs
tail -f /opt/openmusicbox/logs/app.log

# Audio system logs
sudo journalctl -u alsa-state
```

### Performance Monitoring

```bash
# System resources
htop
iostat -x 1

# Application performance
curl http://localhost:5004/api/system/info

# Database performance
sqlite3 /opt/openmusicbox/data/music.db ".schema"
```

## Security Considerations

### Basic Security Setup

```bash
# Update system regularly
sudo apt-get update && sudo apt-get upgrade

# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 5004/tcp

# Disable password authentication (SSH keys only)
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### File Permissions

```bash
# Secure application files
sudo chown -R admin:admin /opt/openmusicbox
chmod 755 /opt/openmusicbox
chmod 600 /opt/openmusicbox/config/.env
```

## Backup and Maintenance

### Database Backup

```bash
# Create backup script
tee ~/backup-music.sh << EOF
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 /opt/openmusicbox/data/music.db ".backup /home/admin/backups/music_$DATE.db"
find /home/admin/backups -name "music_*.db" -mtime +7 -delete
EOF

chmod +x ~/backup-music.sh

# Add to crontab
echo "0 3 * * * /home/admin/backup-music.sh" | crontab -
```

### System Maintenance

```bash
# Weekly system cleanup
sudo apt-get autoremove
sudo apt-get autoclean
journalctl --vacuum-time=30d
```

This deployment guide should get your Open Music Box running smoothly on Raspberry Pi with proper audio, NFC functionality, and reliable service management.