#!/bin/bash

# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.

# TMBTool - Deployment Functions
# ==============================
# Functions for building, packaging, and deploying the application

# Deploy functions
run_tests() {
    print_header "🧪 Running Comprehensive Test Suite"

    print_status $BLUE "📊 Running all tests across:"
    print_status $BLUE "   • back/tests/ (comprehensive business logic)"
    print_status $BLUE "   • back/app/tests/unit/ (unit tests)"
    print_status $BLUE "   • back/app/tests/integration/ (integration tests)"
    print_status $BLUE "   • back/app/tests/routes/ (API endpoint tests)"
    print_status $BLUE "   • back/tools/test_*.py (hardware tests)"
    echo ""

    cd "${PROJECT_ROOT}/back" || exit 1

    if ./run_tests.sh; then
        print_status $GREEN "✅ All tests passed successfully!"
        return 0
    else
        print_status $RED "❌ Tests failed! Deployment aborted."
        exit 1
    fi
}

build_frontend() {
    print_header "🔨 Building Frontend"

    local front_dir="${PROJECT_ROOT}/front"

    if [[ ! -d "$front_dir" ]]; then
        print_status $RED "❌ Frontend directory not found: $front_dir"
        exit 1
    fi

    print_status $BLUE "📦 Building Vue.js frontend..."

    cd "$front_dir" || exit 1

    if npm run build; then
        print_status $GREEN "✅ Frontend built successfully!"
        cd "$PROJECT_ROOT" || exit 1
        return 0
    else
        print_status $RED "❌ Frontend build failed!"
        exit 1
    fi
}

package_release() {
    print_header "📦 Packaging Release"

    local back_dir="${PROJECT_ROOT}/back"
    local front_dir="${PROJECT_ROOT}/front"
    local release_dir="${PROJECT_ROOT}/${RELEASE_DEV_DIR}/tomb-rpi"

    print_status $BLUE "📋 Creating release package in: $release_dir"

    # Create release directory
    mkdir -p "$release_dir"

    # Copy backend files
    print_status $BLUE "📂 Copying backend files..."

    rsync -a --delete \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='logs' \
        --exclude='app.db' \
        --exclude='venv' \
        --exclude='.pytest_cache' \
        "${back_dir}/app/" "${release_dir}/app/"

    # Create flattened requirements.txt
    local req_dst="${release_dir}/requirements.txt"
    awk -v src_dir="${back_dir}/requirements" '
      /^-r / {
        sub(/^-r /, "", $0);
        file = src_dir "/" $0;
        while ((getline line < file) > 0) print line;
        close(file);
        next;
      }
      { print }
    ' "${back_dir}/requirements/prod.txt" > "$req_dst"

    # Remove comments and blank lines
    sed -i.bak "/^\\s*#/d;/^\\s*$/d" "$req_dst" && rm "$req_dst.bak"

    # Copy additional files
    [[ -f "${back_dir}/README.md" ]] && cp "${back_dir}/README.md" "${release_dir}/"
    [[ -f "${back_dir}/LICENSE" ]] && cp "${back_dir}/LICENSE" "${release_dir}/"
    [[ -f "${back_dir}/setup.sh" ]] && cp "${back_dir}/setup.sh" "${release_dir}/"
    [[ -f "${back_dir}/start_app.py" ]] && cp "${back_dir}/start_app.py" "${release_dir}/" && chmod +x "${release_dir}/start_app.py"

    # Copy tools directory
    if [[ -d "${back_dir}/tools" ]]; then
        cp -r "${back_dir}/tools" "${release_dir}/"
        chmod +x "${release_dir}/tools/"*.py 2>/dev/null || true
    fi

    # Copy server files directory
    if [[ -d "${PROJECT_ROOT}/server_files" ]]; then
        cp -r "${PROJECT_ROOT}/server_files" "${release_dir}/"
        print_status $GREEN "✅ Server configuration files included"
    fi

    # Copy .env file
    if [[ -f "${back_dir}/.env" ]]; then
        cp "${back_dir}/.env" "${release_dir}/.env"
        print_status $GREEN "✅ Configuration file (.env) included"
    else
        print_status $YELLOW "⚠️  WARNING: .env file not found!"
    fi

    # Copy frontend build
    print_status $BLUE "📂 Copying frontend build..."
    mkdir -p "${release_dir}/app/static"
    cp -r "${front_dir}/dist/"* "${release_dir}/app/static/"

    print_status $GREEN "✅ Release packaged successfully!"
}

deploy_to_server() {
    print_header "🚀 Deploying to Server"

    if [[ -z "$REMOTE_HOST" ]]; then
        print_status $RED "❌ Server not configured!"
        return 1
    fi

    local release_dir="${PROJECT_ROOT}/${RELEASE_DEV_DIR}/tomb-rpi"

    print_status $BLUE "📤 Deploying to: $REMOTE_USER@$REMOTE_HOST"
    print_status $BLUE "📂 Remote directory: $REMOTE_DIR"

    # Create remote directory
    print_status $BLUE "📁 Creating remote directory..."
    ssh "$SSH_ALIAS" "mkdir -p ${REMOTE_DIR} && sudo chown $REMOTE_USER:$REMOTE_USER ${REMOTE_DIR}" 2>/dev/null

    # Upload files
    print_status $BLUE "📤 Synchronizing files..."

    rsync -azP --delete \
        --rsync-path="rsync" \
        --no-owner --no-group \
        --ignore-errors \
        -e "ssh" \
        "${release_dir}/" "${SSH_ALIAS}:${REMOTE_DIR}/" 2>/dev/null

    if [[ $? -eq 0 ]]; then
        print_status $GREEN "✅ Files synchronized successfully!"
    else
        print_status $RED "❌ File synchronization failed!"
        exit 1
    fi

    # Fix permissions
    print_status $BLUE "🔧 Fixing remote permissions..."
    ssh "$SSH_ALIAS" "sudo chown -R $REMOTE_USER:$REMOTE_USER ${REMOTE_DIR}" 2>/dev/null

    # Restart service
    print_status $BLUE "🔄 Restarting application service..."
    if ssh "$SSH_ALIAS" "sudo systemctl restart app.service" 2>/dev/null; then
        print_status $GREEN "✅ Service restarted successfully!"
    else
        print_status $RED "❌ Service restart failed!"
        exit 1
    fi

    # Health check
    print_status $BLUE "🏥 Performing health check..."
    sleep 3

    if ssh "$SSH_ALIAS" "sudo systemctl is-active app.service" 2>/dev/null | grep -q "active"; then
        print_status $GREEN "✅ Service is running and healthy!"
    else
        print_status $YELLOW "⚠️  Service status unclear, check manually"
    fi
}

deploy_menu() {
    print_header "🚀 Deploy Application"

    # Load configuration
    if ! load_config 2>/dev/null || [[ -z "$REMOTE_HOST" ]]; then
        print_status $RED "❌ Server not configured. Please run configuration first."
        read -p "Press Enter to continue..."
        return 1
    fi

    print_status $BLUE "🎯 Deploying to: $REMOTE_USER@$REMOTE_HOST"
    echo ""

    # Ask for deployment options
    local run_tests_local="$RUN_TESTS"
    local build_frontend_local="$BUILD_FRONTEND"

    if ask_yes_no "Run tests before deployment?" "y"; then
        run_tests_local="true"
    else
        run_tests_local="false"
    fi

    if ask_yes_no "Build frontend before deployment?" "y"; then
        build_frontend_local="true"
    else
        build_frontend_local="false"
    fi

    echo ""
    print_status $BLUE "🔄 Starting deployment process..."

    # Execute deployment steps
    [[ "$run_tests_local" == "true" ]] && run_tests
    [[ "$build_frontend_local" == "true" ]] && build_frontend
    package_release
    deploy_to_server

    print_status $GREEN "🎉 Deployment completed successfully!"

    read -p "Press Enter to continue..."
}

test_menu() {
    print_header "🧪 Run Tests"

    print_status $BLUE "🔄 Running comprehensive test suite..."

    if run_tests; then
        print_status $GREEN "🎉 All tests completed successfully!"
    else
        print_status $RED "❌ Some tests failed"
    fi

    read -p "Press Enter to continue..."
}

# Monitor server logs
monitor_server() {
    local target="${SSH_ALIAS:-$1}"

    if [[ -z "$target" ]]; then
        print_status $RED "❌ No SSH target specified for monitoring!"
        echo "Use: $0 --monitor [user@host]"
        exit 1
    fi

    print_header "📊 Monitoring Server Logs"
    print_status $BLUE "🔍 Monitoring: $target"
    print_status $BLUE "📋 Press Ctrl+C to stop monitoring"
    echo ""

    ssh "$target" "sudo journalctl -fu app.service --output=cat"
}