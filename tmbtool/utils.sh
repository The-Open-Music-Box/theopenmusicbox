#!/bin/bash

# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.

# TMBTool - Utility Functions
# ===========================
# Common utility functions used across all TMBTool modules

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    printf "${color}${message}${NC}\n"
}

print_header() {
    printf "\n"
    print_status $CYAN "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_status $CYAN "  $1"
    print_status $CYAN "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Function to ask for input with colored prompt
ask_input() {
    local prompt="$1"
    local response
    printf "${BLUE}$prompt${NC}"
    read response
    echo "$response"
}

ask_yes_no() {
    local prompt="$1"
    local default="${2:-n}"
    local response

    while true; do
        if [[ "$default" == "y" ]]; then
            printf "${BLUE}$prompt [Y/n]: ${NC}"
            read response
            response="${response:-y}"
        else
            printf "${BLUE}$prompt [y/N]: ${NC}"
            read response
            response="${response:-n}"
        fi

        case "$response" in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            [Nn]|[Nn][Oo]) return 1 ;;
            *) print_status $RED "Please answer yes or no." ;;
        esac
    done
}

# Input validation functions
validate_input() {
    local input="$1"
    local type="$2"

    case "$type" in
        "hostname")
            if [[ ! "$input" =~ ^[a-zA-Z0-9._-]+$ ]]; then
                print_status $RED "❌ Hostname can only contain letters, numbers, dots, underscores, and hyphens"
                return 1
            fi
            ;;
        "username")
            if [[ ! "$input" =~ ^[a-zA-Z0-9_-]+$ ]]; then
                print_status $RED "❌ Username can only contain letters, numbers, underscores, and hyphens"
                return 1
            fi
            ;;
        "path")
            if [[ ! "$input" =~ ^[a-zA-Z0-9/_.-]+$ ]]; then
                print_status $RED "❌ Path contains invalid characters"
                return 1
            fi
            ;;
        "alias")
            if [[ ! "$input" =~ ^[a-zA-Z0-9_-]+$ ]]; then
                print_status $RED "❌ SSH alias can only contain letters, numbers, underscores, and hyphens"
                return 1
            fi
            ;;
    esac
    return 0
}

# Configuration file management
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
        print_status $BLUE "📋 Configuration loaded from: $CONFIG_FILE"
        return 0
    else
        print_status $YELLOW "⚠️  No configuration file found. Use 'config' to create one."
        return 1
    fi
}

save_config() {
    cat > "$CONFIG_FILE" << EOF
# TMBTool Configuration File
# Generated on $(date)

# Server connection settings
REMOTE_HOST="$REMOTE_HOST"
REMOTE_USER="$REMOTE_USER"
REMOTE_DIR="$REMOTE_DIR"
CONNECTION_TYPE="$CONNECTION_TYPE"
SSH_KEY_PATH="$SSH_KEY_PATH"
SSH_ALIAS="$SSH_ALIAS"

# Application settings
REPO_URL="$REPO_URL"
RELEASE_DEV_DIR="$RELEASE_DEV_DIR"
ENABLE_FTP_WRITE="$ENABLE_FTP_WRITE"

# Default build settings
RUN_TESTS="$RUN_TESTS"
BUILD_FRONTEND="$BUILD_FRONTEND"
EOF
    print_status $GREEN "✅ Configuration saved to: $CONFIG_FILE"
}