#!/bin/bash

# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.

# TMBTool - Configuration Functions
# =================================
# Functions for managing TMBTool configuration settings

# Configuration menu
configure_settings() {
    print_header "🔧 Configuration Setup"

    echo "Welcome to TMB Tool configuration!"
    echo ""
    echo "This setup will configure your server connection and deployment settings."
    echo "You'll need the following information about your Raspberry Pi:"
    echo "  • Server IP address or hostname (e.g., 192.168.1.100 or raspberrypi.local)"
    echo "  • Username for SSH connection (usually 'pi' or 'admin')"
    echo "  • Installation directory (where the app will be installed)"
    echo ""
    echo "Let's get started:"
    echo ""

    # Remote host configuration
    echo "Step 1/5: Server Connection"
    echo "Enter your Raspberry Pi's IP address or hostname."
    echo "Examples: 192.168.1.100, raspberrypi.local, tomb.local"
    while true; do
        input=$(ask_input "🌐 Server hostname or IP address: ")
        if [[ -z "$input" ]]; then
            print_status $RED "❌ Server hostname cannot be empty"
        elif validate_input "$input" "hostname"; then
            REMOTE_HOST="$input"
            break
        fi
    done
    echo ""

    # Remote user configuration
    echo "Step 2/5: Server Username"
    echo "Enter the username for SSH connection to your Raspberry Pi."
    echo "Common usernames: pi, admin, ubuntu"
    while true; do
        input=$(ask_input "👤 Username on server (default: $DEFAULT_SSH_USER): ")
        input="${input:-$DEFAULT_SSH_USER}"
        if validate_input "$input" "username"; then
            REMOTE_USER="$input"
            break
        fi
    done
    echo ""

    # Remote directory configuration
    echo "Step 3/5: Installation Directory"
    echo "Choose where to install the application on your Raspberry Pi."
    echo "Default is recommended for most users."
    while true; do
        input=$(ask_input "📁 Installation directory on server (default: $DEFAULT_REMOTE_DIR): ")
        input="${input:-$DEFAULT_REMOTE_DIR}"
        if validate_input "$input" "path"; then
            REMOTE_DIR="$input"
            break
        fi
    done
    echo ""

    # SSH alias configuration
    echo "Step 4/5: SSH Shortcut Name"
    echo "Create a short name to easily connect to your server."
    echo "Examples: tomb, rpi, musicbox"
    while true; do
        input=$(ask_input "🔖 SSH alias/shortcut name: ")
        if [[ -z "$input" ]]; then
            print_status $RED "❌ SSH alias cannot be empty"
        elif validate_input "$input" "alias"; then
            SSH_ALIAS="$input"
            break
        fi
    done
    echo ""

    # Repository URL configuration
    echo "Step 5/5: Application Settings"
    echo "Configure the git repository URL and optional features."
    input=$(ask_input "🔗 Git repository URL (default: $DEFAULT_REPO_URL): ")
    REPO_URL="${input:-$DEFAULT_REPO_URL}"
    echo ""

    # FTP write access configuration
    echo "Optional Features:"
    if ask_yes_no "Enable FTP write access on server? (allows file transfers)" "n"; then
        ENABLE_FTP_WRITE="true"
        echo "  ✓ FTP write access will be enabled"
    else
        ENABLE_FTP_WRITE="false"
        echo "  ✗ FTP write access disabled"
    fi

    # Build settings
    if ask_yes_no "Run tests by default during deployment? (recommended)" "y"; then
        RUN_TESTS="true"
        echo "  ✓ Tests will run before deployment"
    else
        RUN_TESTS="false"
        echo "  ✗ Tests will be skipped by default"
    fi

    if ask_yes_no "Build frontend by default during deployment? (recommended)" "y"; then
        BUILD_FRONTEND="true"
        echo "  ✓ Frontend will be built before deployment"
    else
        BUILD_FRONTEND="false"
        echo "  ✗ Frontend build will be skipped by default"
    fi

    save_config

    echo ""
    print_status $GREEN "✅ Configuration completed successfully!"
    echo ""
    echo "Current settings:"
    echo "  • Server: $REMOTE_HOST"
    echo "  • User: $REMOTE_USER"
    echo "  • Directory: $REMOTE_DIR"
    echo "  • SSH Alias: $SSH_ALIAS"
    echo "  • FTP Write: $ENABLE_FTP_WRITE"
    echo ""

    read -p "Press Enter to continue..."
}

view_config_menu() {
    print_header "📋 Current Configuration"

    if load_config 2>/dev/null; then
        echo "${BOLD}Server Connection:${NC}"
        echo "  • Host: ${REMOTE_HOST:-'Not set'}"
        echo "  • User: ${REMOTE_USER:-'Not set'}"
        echo "  • Directory: ${REMOTE_DIR:-'Not set'}"
        echo "  • SSH Alias: ${SSH_ALIAS:-'Not set'}"
        echo "  • Connection Type: ${CONNECTION_TYPE:-'Not set'}"
        echo ""
        echo "${BOLD}Application Settings:${NC}"
        echo "  • Repository URL: ${REPO_URL:-'Not set'}"
        echo "  • Release Directory: ${RELEASE_DEV_DIR:-'Not set'}"
        echo "  • FTP Write Access: ${ENABLE_FTP_WRITE:-'Not set'}"
        echo ""
        echo "${BOLD}Build Settings:${NC}"
        echo "  • Run Tests: ${RUN_TESTS:-'Not set'}"
        echo "  • Build Frontend: ${BUILD_FRONTEND:-'Not set'}"
        echo ""
        echo "${BOLD}Configuration File:${NC}"
        echo "  • Location: $CONFIG_FILE"
        echo "  • Exists: $([ -f "$CONFIG_FILE" ] && echo "Yes" || echo "No")"
    else
        print_status $YELLOW "⚠️  No configuration found"
        echo ""
        echo "Use option 1 (Configuration) to create a new configuration"
    fi

    echo ""
    read -p "Press Enter to continue..."
}