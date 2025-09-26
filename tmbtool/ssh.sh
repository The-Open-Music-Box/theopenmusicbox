#!/bin/bash

# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.

# TMBTool - SSH Management Functions
# ==================================
# Functions for SSH key setup and connection management

# SSH setup functions
setup_ssh_directory() {
    print_status $BLUE "📁 Setting up SSH directory and permissions..."

    if [[ ! -d "$SSH_DIR" ]]; then
        mkdir -p "$SSH_DIR"
        print_status $GREEN "✅ Created SSH directory: $SSH_DIR"
    fi

    chmod 700 "$SSH_DIR"

    if [[ ! -f "$SSH_DIR/config" ]]; then
        touch "$SSH_DIR/config"
        print_status $GREEN "✅ Created SSH config file"
    fi
    chmod 600 "$SSH_DIR/config"

    print_status $GREEN "✅ SSH directory permissions configured correctly"
}

get_existing_keys() {
    for key_file in "$SSH_DIR"/*; do
        if [[ -f "$key_file" && ! "$key_file" =~ \.pub$ && -f "${key_file}.pub" ]]; then
            echo "$key_file"
        fi
    done 2>/dev/null || true
}

select_ssh_key() {
    local existing_keys=()
    local key_file

    while IFS= read -r key_file; do
        [[ -n "$key_file" ]] && existing_keys+=("$key_file")
    done < <(get_existing_keys)

    if [[ ${#existing_keys[@]} -eq 0 ]]; then
        print_status $YELLOW "⚠️  No existing SSH key pairs found"
        create_new_ssh_key
    else
        echo "${YELLOW}🗝️  Found existing SSH keys:${NC}"
        local i=1
        for key in "${existing_keys[@]}"; do
            local key_name=$(basename "$key")
            echo "  $i) $key_name"
            ((i++))
        done
        echo "  $i) Create a new key"
        echo ""

        while true; do
            choice=$(ask_input "Choose an option (1-$i): ")

            if [[ "$choice" =~ ^[0-9]+$ ]]; then
                if [[ "$choice" -ge 1 && "$choice" -le ${#existing_keys[@]} ]]; then
                    SSH_KEY_PATH="${existing_keys[$((choice-1))]}"
                    print_status $GREEN "✅ Using existing key: $(basename "$SSH_KEY_PATH")"
                    return
                elif [[ "$choice" -eq $i ]]; then
                    create_new_ssh_key
                    return
                fi
            fi

            print_status $RED "❌ Invalid choice. Please enter a number between 1 and $i"
        done
    fi
}

create_new_ssh_key() {
    local key_name

    while true; do
        key_name=$(ask_input "🆕 Name for the new SSH key (e.g., tomb_key): ")

        if [[ -z "$key_name" ]]; then
            print_status $RED "❌ Key name cannot be empty"
            continue
        fi

        if [[ ! "$key_name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
            print_status $RED "❌ Key name can only contain letters, numbers, underscores, and hyphens"
            continue
        fi

        SSH_KEY_PATH="$SSH_DIR/$key_name"

        if [[ -f "$SSH_KEY_PATH" ]]; then
            print_status $YELLOW "⚠️  Key '$key_name' already exists"
            if ask_yes_no "Do you want to overwrite it?"; then
                break
            else
                continue
            fi
        else
            break
        fi
    done

    print_status $BLUE "🔑 Generating new SSH key pair..."

    if ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -C "$key_name-$(date +%Y%m%d)"; then
        chmod 600 "$SSH_KEY_PATH"
        chmod 644 "$SSH_KEY_PATH.pub"
        print_status $GREEN "✅ SSH key pair generated successfully"
    else
        print_status $RED "❌ Failed to generate SSH key pair"
        exit 1
    fi
}

copy_public_key() {
    print_status $BLUE "📤 Copying public key to server..."

    local pub_key_content
    if ! pub_key_content=$(cat "${SSH_KEY_PATH}.pub"); then
        print_status $RED "❌ Failed to read public key file"
        exit 1
    fi

    local setup_cmd="mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$pub_key_content' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.tmp && mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys && echo 'Public key setup completed'"

    print_status $BLUE "🔐 You will be prompted for your password..."

    if command -v ssh-copy-id >/dev/null 2>&1; then
        print_status $BLUE "📋 Using ssh-copy-id to copy the key..."
        if ssh-copy-id -o StrictHostKeyChecking=accept-new -i "${SSH_KEY_PATH}" "$REMOTE_USER@$REMOTE_HOST"; then
            print_status $GREEN "✅ Public key copied successfully using ssh-copy-id"
        else
            print_status $YELLOW "⚠️  ssh-copy-id failed, trying manual method..."
            if ssh -o StrictHostKeyChecking=accept-new "$REMOTE_USER@$REMOTE_HOST" "$setup_cmd"; then
                print_status $GREEN "✅ Public key copied and configured successfully"
            else
                print_status $RED "❌ Failed to copy public key"
                exit 1
            fi
        fi
    else
        if ssh -o StrictHostKeyChecking=accept-new "$REMOTE_USER@$REMOTE_HOST" "$setup_cmd"; then
            print_status $GREEN "✅ Public key copied and configured successfully"
        else
            print_status $RED "❌ Failed to copy public key"
            exit 1
        fi
    fi
}

update_ssh_config() {
    print_status $BLUE "📝 Adding entry to SSH config..."

    # Remove existing entry if it exists
    if grep -q "^Host $SSH_ALIAS$" "$SSH_DIR/config" 2>/dev/null; then
        sed -i.bak "/^Host $SSH_ALIAS$/,/^$/d" "$SSH_DIR/config"
    fi

    local config_entry="
Host $SSH_ALIAS
    HostName $REMOTE_HOST
    User $REMOTE_USER
    IdentityFile $SSH_KEY_PATH
    IdentitiesOnly yes
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
"

    echo "$config_entry" >> "$SSH_DIR/config"
    print_status $GREEN "✅ SSH config updated successfully"
}

test_ssh_connection() {
    print_status $BLUE "🧪 Testing SSH connection..."

    if ssh -o BatchMode=yes -o ConnectTimeout=10 "$SSH_ALIAS" "echo 'SSH connection test successful'" 2>/dev/null; then
        print_status $GREEN "✅ Passwordless SSH authentication working!"
        return 0
    else
        print_status $RED "❌ SSH connection failed"
        return 1
    fi
}

ssh_setup_menu() {
    print_header "🔑 SSH Setup"

    # Load config or prompt for host if not available
    if [[ -z "$REMOTE_HOST" ]]; then
        if ! load_config 2>/dev/null || [[ -z "$REMOTE_HOST" ]]; then
            print_status $YELLOW "⚠️  Server not configured. Please provide connection details."
            while true; do
                input=$(ask_input "🌐 Server hostname or IP address: ")
                if [[ -n "$input" ]] && validate_input "$input" "hostname"; then
                    REMOTE_HOST="$input"
                    break
                fi
            done

            while true; do
                input=$(ask_input "👤 Username on server (default: $DEFAULT_SSH_USER): ")
                input="${input:-$DEFAULT_SSH_USER}"
                if validate_input "$input" "username"; then
                    REMOTE_USER="$input"
                    break
                fi
            done

            while true; do
                input=$(ask_input "🔖 SSH alias/shortcut name: ")
                if [[ -n "$input" ]] && validate_input "$input" "alias"; then
                    SSH_ALIAS="$input"
                    break
                fi
            done

            # Save the basic config
            save_config
        fi
    fi

    print_status $BLUE "🎯 Setting up SSH for: $REMOTE_USER@$REMOTE_HOST"
    echo ""

    setup_ssh_directory
    select_ssh_key

    print_status $BLUE "🔍 Testing server connectivity..."
    if ! ping -c 1 -W 3 "$REMOTE_HOST" >/dev/null 2>&1; then
        print_status $YELLOW "⚠️  Cannot reach server via ping. Continuing anyway..."
    else
        print_status $GREEN "✅ Server is reachable"
    fi

    copy_public_key
    update_ssh_config

    if test_ssh_connection; then
        print_status $GREEN "🎉 SSH setup completed successfully!"
        echo ""
        echo -e "${CYAN}💻 You can now connect to your server with: ${BOLD}ssh $SSH_ALIAS${NC}"
        echo ""

        if ask_yes_no "Would you like to connect now?"; then
            ssh "$SSH_ALIAS"
        fi
    else
        print_status $YELLOW "⚠️  SSH setup completed but connection test failed"
        echo "You may need to check the server configuration manually"
    fi

    read -p "Press Enter to continue..."
}