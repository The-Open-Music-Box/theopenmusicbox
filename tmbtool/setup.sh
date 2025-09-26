#!/bin/bash

# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.

# TMBTool - Server Setup Functions
# ================================
# Functions for installing and configuring the server environment

# Server setup functions
server_setup_menu() {
    print_header "🏗️  Server Setup"

    # Load configuration
    if ! load_config 2>/dev/null || [[ -z "$REMOTE_HOST" ]]; then
        print_status $RED "❌ Server not configured. Please run configuration first."
        read -p "Press Enter to continue..."
        return 1
    fi

    print_status $BLUE "🎯 Setting up server: $REMOTE_USER@$REMOTE_HOST"
    echo ""

    # Ask all questions upfront to avoid interruptions
    local skip_upgrade=false
    local install_ftp=false
    local allow_reboot=false

    echo "${BOLD}Setup Configuration:${NC}"

    if ask_yes_no "Skip apt-get upgrade to avoid interruptions?" "y"; then
        skip_upgrade=true
    fi

    if [[ "$ENABLE_FTP_WRITE" == "true" ]] || ask_yes_no "Install and configure FTP server with write access?"; then
        install_ftp=true
        ENABLE_FTP_WRITE="true"
    fi

    if ask_yes_no "Allow automatic reboot after setup completion?" "y"; then
        allow_reboot=true
    fi

    echo ""
    print_status $BLUE "📋 Setup will proceed with minimal interruptions"
    print_status $BLUE "🔄 This may take several minutes..."
    echo ""

    # Test SSH connection
    if ! ssh -o BatchMode=yes -o ConnectTimeout=10 "$SSH_ALIAS" "echo 'Connection OK'" 2>/dev/null; then
        print_status $RED "❌ Cannot connect to server via SSH"
        print_status $BLUE "💡 Please run SSH setup first"
        read -p "Press Enter to continue..."
        return 1
    fi

    # Create the comprehensive setup script
    local setup_script="#!/bin/bash
set -e

GREEN='\\033[0;32m'
RED='\\033[0;31m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

echo -e \"\${GREEN}========================================\"
echo -e \" 🎵  The Open Music Box Setup  🎵 \"
echo -e \"========================================\${NC}\"
echo \"\"

# Update system
echo -e \"\${GREEN}Updating system packages...\${NC}\"
sudo apt-get update

# Conditional upgrade
if [ \"$skip_upgrade\" != \"true\" ]; then
    echo -e \"\${GREEN}Upgrading system packages...\${NC}\"
    sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
fi

# Install required packages
echo -e \"\${GREEN}Installing required packages...\${NC}\"
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \\
    python3 python3-venv python3-pip ffmpeg libasound2-dev \\
    libnss-mdns git i2c-tools python3-smbus python3-libgpiod \\
    libsdl2-mixer-2.0-0 swig unzip build-essential

# Install FTP server if requested
if [ \"$install_ftp\" == \"true\" ]; then
    echo -e \"\${GREEN}Installing and configuring FTP server...\${NC}\"
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y vsftpd

    # Configure vsftpd for write access
    sudo cp /etc/vsftpd.conf /etc/vsftpd.conf.backup
    sudo sed -i 's/#write_enable=YES/write_enable=YES/' /etc/vsftpd.conf
    sudo sed -i 's/#local_enable=YES/local_enable=YES/' /etc/vsftpd.conf
    sudo systemctl restart vsftpd
    sudo systemctl enable vsftpd
    echo -e \"\${GREEN}✅ FTP server configured with write access\${NC}\"
fi

# Enable I2C interface
echo -e \"\${GREEN}Enabling I2C interface...\${NC}\"
sudo raspi-config nonint do_i2c 0

# Install lgpio from source
echo -e \"\${GREEN}Installing lgpio from source...\${NC}\"
cd /tmp
wget -q https://github.com/joan2937/lg/archive/master.zip
unzip -q master.zip
cd lg-master
make > /dev/null 2>&1
sudo make install > /dev/null 2>&1
cd ~

# Install WM8960 Audio HAT drivers
echo -e \"\${GREEN}Installing WM8960 Audio HAT drivers...\${NC}\"
git clone https://github.com/waveshare/WM8960-Audio-HAT
cd WM8960-Audio-HAT
sudo ./install.sh
cd ~

# Clone the repository
echo -e \"\${GREEN}Cloning application repository...\${NC}\"
if [ -d \"tomb\" ]; then
    rm -rf tomb
fi
git clone $REPO_URL tomb
cd tomb

# Copy server configuration files
echo -e \"\${GREEN}Installing server configuration files...\${NC}\"
if [ -f \"server_files/asound.conf\" ]; then
    sudo cp server_files/asound.conf /etc/asound.conf
    echo -e \"\${GREEN}✅ Audio configuration installed\${NC}\"
fi

# Make setup script executable and run it
chmod +x setup.sh
sudo ./setup.sh

echo -e \"\${GREEN}\"
echo \"========================================\"
echo \" 🎉  Setup Completed Successfully!  🎉 \"
echo \"========================================\"
echo -e \"\${NC}\"
echo \"Application is now installed and running\"
echo \"Service status: \$(sudo systemctl is-active app.service || echo 'checking...')\"
echo \"\"
"

    # Execute the setup script on the remote server
    print_status $BLUE "🚀 Executing setup on server..."

    if ssh "$SSH_ALIAS" "$setup_script"; then
        print_status $GREEN "✅ Server setup completed successfully!"

        # Check service status
        print_status $BLUE "🔍 Checking application service status..."
        if ssh "$SSH_ALIAS" "sudo systemctl is-active app.service" 2>/dev/null | grep -q "active"; then
            print_status $GREEN "✅ Application service is running"
        else
            print_status $YELLOW "⚠️  Application service status unclear"
        fi

        # Offer reboot
        if [[ "$allow_reboot" == "true" ]]; then
            print_status $BLUE "🔄 Rebooting server..."
            ssh "$SSH_ALIAS" "sudo reboot" 2>/dev/null || true
            print_status $GREEN "✅ Server reboot initiated"
        else
            if ask_yes_no "Reboot server now to complete setup?"; then
                ssh "$SSH_ALIAS" "sudo reboot" 2>/dev/null || true
                print_status $GREEN "✅ Server reboot initiated"
            fi
        fi
    else
        print_status $RED "❌ Server setup failed"
        print_status $BLUE "💡 Check the server manually or try running setup again"
    fi

    read -p "Press Enter to continue..."
}