#!/bin/bash

# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.

# TheOpenMusicBox - Unified Management Tool (TMB Tool)
# ===================================================
#
# Unified tool that replaces deploy.sh, setup_ssh_key_to_rpi.sh, and back/setup.sh
# Provides comprehensive deployment, SSH setup, server configuration, and testing capabilities

set -e  # Exit on any error

# Script metadata
readonly SCRIPT_VERSION="2.0.0"
readonly SCRIPT_NAME="TheOpenMusicBox Unified Tool"

# Configuration files and paths
readonly PROJECT_ROOT="$(dirname "$(realpath "$0")")"
readonly CONFIG_FILE="${PROJECT_ROOT}/tmbtool.config"
readonly SSH_DIR="$HOME/.ssh"
readonly TMBTOOL_DIR="${PROJECT_ROOT}/tmbtool"

# Default configuration values
DEFAULT_REMOTE_DIR="/home/admin/tomb"
DEFAULT_SSH_USER="admin"
DEFAULT_CONNECTION_TYPE="ssh"
DEFAULT_REPO_URL="https://github.com/yourusername/tomb"
DEFAULT_RELEASE_DEV_DIR="release_dev"

# Configuration variables (will be loaded from config file)
REMOTE_HOST=""
REMOTE_USER="$DEFAULT_SSH_USER"
REMOTE_DIR="$DEFAULT_REMOTE_DIR"
CONNECTION_TYPE="$DEFAULT_CONNECTION_TYPE"
SSH_KEY_PATH=""
SSH_ALIAS=""
REPO_URL="$DEFAULT_REPO_URL"
RELEASE_DEV_DIR="$DEFAULT_RELEASE_DEV_DIR"
ENABLE_FTP_WRITE="false"
RUN_TESTS="true"
BUILD_FRONTEND="true"

# Source all utility and feature modules
if [[ -f "${TMBTOOL_DIR}/utils.sh" ]]; then
    source "${TMBTOOL_DIR}/utils.sh"
else
    echo "❌ Error: Required file ${TMBTOOL_DIR}/utils.sh not found"
    exit 1
fi

if [[ -f "${TMBTOOL_DIR}/config.sh" ]]; then
    source "${TMBTOOL_DIR}/config.sh"
else
    echo "❌ Error: Required file ${TMBTOOL_DIR}/config.sh not found"
    exit 1
fi

if [[ -f "${TMBTOOL_DIR}/ssh.sh" ]]; then
    source "${TMBTOOL_DIR}/ssh.sh"
else
    echo "❌ Error: Required file ${TMBTOOL_DIR}/ssh.sh not found"
    exit 1
fi

if [[ -f "${TMBTOOL_DIR}/setup.sh" ]]; then
    source "${TMBTOOL_DIR}/setup.sh"
else
    echo "❌ Error: Required file ${TMBTOOL_DIR}/setup.sh not found"
    exit 1
fi

if [[ -f "${TMBTOOL_DIR}/deploy.sh" ]]; then
    source "${TMBTOOL_DIR}/deploy.sh"
else
    echo "❌ Error: Required file ${TMBTOOL_DIR}/deploy.sh not found"
    exit 1
fi

# Main menu display
show_main_menu() {
    clear
    printf "${GREEN}"
    printf "    ========================================\n"
    printf "    🎵  The Open Music Box Tool  🎵\n"
    printf "    ========================================\n"
    printf "${NC}\n"
    printf "${CYAN}${BOLD}$SCRIPT_NAME v$SCRIPT_VERSION${NC}\n"
    printf "\n"
    printf "${BOLD}Main Menu - Choose an option:${NC}\n"
    printf "\n"
    printf "${BOLD}Setup & Configuration:${NC}\n"
    printf "  1) Configuration  - Set up server connection details\n"
    printf "  2) SSH Tool       - Configure SSH keys for passwordless access\n"
    printf "  3) Setup          - Install application on Raspberry Pi\n"
    printf "\n"
    printf "${BOLD}Development & Deployment:${NC}\n"
    printf "  4) Deploy         - Build and deploy application to server\n"
    printf "  5) Tests          - Run all test suites locally\n"
    printf "\n"
    printf "${BOLD}Information:${NC}\n"
    printf "  6) View Config    - Show current settings\n"
    printf "  0) Exit           - Quit TMB Tool\n"
    printf "\n"
}

show_help() {
    echo -e "${BOLD}${SCRIPT_NAME} v${SCRIPT_VERSION}${NC}"
    echo "==============================================="
    echo ""
    echo -e "${CYAN}${BOLD}🚀 GETTING STARTED (First time users):${NC}"
    echo "1. Run: $0"
    echo "2. Choose option 1 (Configuration) to set up your server"
    echo "3. Choose option 2 (SSH Tool) to configure SSH keys"
    echo "4. Choose option 3 (Setup) to install the app on your Pi"
    echo "5. Use option 4 (Deploy) to update your app later"
    echo ""
    echo -e "${BOLD}USAGE:${NC}"
    echo "  $0 [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${BOLD}INTERACTIVE COMMANDS:${NC}"
    echo "  config              Configure server connection details"
    echo "  ssh-setup           Setup SSH keys for passwordless access"
    echo "  setup               Install application on Raspberry Pi"
    echo "  deploy              Build and deploy application to server"
    echo "  test                Run comprehensive test suite locally"
    echo ""
    echo -e "${BOLD}DIRECT COMMANDS (Legacy compatibility):${NC}"
    echo "  --prod [target]     Deploy to production server"
    echo "  --dev               Deploy for local development"
    echo "  --test-only         Run tests without deployment"
    echo "  --build-only        Build without deployment"
    echo "  --monitor [target]  Monitor remote server logs"
    echo ""
    echo -e "${BOLD}OPTIONS:${NC}"
    echo "  -h, --help          Show this help message"
    echo "  -v, --verbose       Enable verbose output"
    echo "  -q, --quiet         Enable quiet mode"
    echo "  --skip-tests        Skip test execution"
    echo "  --skip-build        Skip frontend build"
    echo "  --no-monitor        Don't monitor after deployment"
    echo ""
    echo -e "${BOLD}EXAMPLES:${NC}"
    echo "  $0                           # Interactive main menu (recommended)"
    echo "  $0 config                    # Configure server settings"
    echo "  $0 ssh-setup                 # Setup SSH connection"
    echo "  $0 deploy                    # Interactive deployment"
    echo "  $0 --prod                    # Quick deploy to configured server"
    echo ""
    echo -e "${CYAN}💡 TIP: Run '$0' without arguments for the user-friendly menu!${NC}"
    echo ""
}

# Interactive main menu
interactive_menu() {
    while true; do
        show_main_menu
        printf "${BLUE}Choose an option (0-6): ${NC}"
        read choice

        case $choice in
            1) configure_settings ;;
            2) ssh_setup_menu ;;
            3) server_setup_menu ;;
            4) deploy_menu ;;
            5) test_menu ;;
            6) view_config_menu ;;
            0) print_status $GREEN "👋 Goodbye!"; exit 0 ;;
            *) print_status $RED "❌ Invalid choice. Please try again."; sleep 1 ;;
        esac
    done
}

# Command-line argument parsing
parse_arguments() {
    case ${1:-} in
        config) configure_settings; exit 0 ;;
        ssh-setup) ssh_setup_menu; exit 0 ;;
        setup) server_setup_menu; exit 0 ;;
        deploy) deploy_menu; exit 0 ;;
        test) test_menu; exit 0 ;;
        --prod)
            load_config 2>/dev/null || true
            if [[ -n "${2:-}" ]]; then
                REMOTE_HOST="$2"
                save_config
            fi
            deploy_menu
            exit 0 ;;
        --dev)
            load_config 2>/dev/null || true
            print_status $BLUE "🔧 Development mode not yet implemented"
            exit 0 ;;
        --test-only) test_menu; exit 0 ;;
        --build-only)
            [[ "$BUILD_FRONTEND" == "true" ]] && build_frontend
            package_release
            exit 0 ;;
        --monitor)
            load_config 2>/dev/null || true
            if [[ -z "$SSH_ALIAS" ]]; then
                print_status $RED "❌ SSH not configured. Run ssh-setup first."
                exit 1
            fi
            print_status $BLUE "📊 Monitoring server logs (Ctrl+C to stop):"
            ssh "$SSH_ALIAS" "sudo journalctl -fu app.service --output=cat"
            exit 0 ;;
        -h|--help) show_help; exit 0 ;;
        "") interactive_menu ;;
        *) print_status $RED "❌ Unknown command: $1"; show_help; exit 1 ;;
    esac
}

# Main execution
main() {
    # Try to load existing configuration
    load_config 2>/dev/null || true

    # Parse arguments or start interactive menu
    parse_arguments "$@"
}

# Run main function with all arguments
main "$@"