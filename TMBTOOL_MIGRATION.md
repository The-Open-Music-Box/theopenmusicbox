# TMBTool Migration Guide

## Overview

The `tmbtool.sh` script is a unified management tool that replaces three separate scripts:
- ✅ `deploy.sh` - Build and deployment functionality
- ✅ `setup_ssh_key_to_rpi.sh` - SSH key setup and configuration
- ✅ `back/setup.sh` - Server environment setup and installation

## Key Features

### 🎯 Unified Interface
- **Interactive Menu**: Run `./tmbtool.sh` for a user-friendly text interface
- **Command Line**: Run specific commands directly (e.g., `./tmbtool.sh config`)
- **Backwards Compatible**: Supports existing deploy script arguments

### 🔧 Configuration Management
- **Persistent Config**: All settings stored in `tmbtool.config`
- **Server Details**: Hostname, username, directories, SSH settings
- **Build Settings**: Test and frontend build preferences
- **FTP Configuration**: Optional FTP server setup with write access

### 🔑 SSH Management
- **Key Generation**: Create new SSH keys or use existing ones
- **Automatic Setup**: Copy keys and configure SSH connections
- **Connection Testing**: Verify passwordless authentication
- **Config Integration**: Uses server settings from main configuration

### 🏗️ Server Setup
- **Automated Installation**: Complete server environment setup
- **WM8960 Audio HAT**: Automatic driver installation
- **Service Configuration**: systemd service setup and management
- **Zero Interruption**: All questions asked upfront for unattended installation

### 🚀 Deployment
- **Full Pipeline**: Tests → Build → Package → Upload → Restart → Monitor
- **Flexible Options**: Skip tests, skip build, or run specific steps
- **Health Checks**: Automatic service status verification
- **Server Files**: Automatic deployment of configuration files

## Usage Examples

### 🚀 Getting Started (First Time Users)
1. **Start TMB Tool**: `./tmbtool.sh`
2. **Configure Server**: Choose option 1 to set up your Raspberry Pi connection details
3. **Setup SSH**: Choose option 2 to configure SSH keys for passwordless access
4. **Install Application**: Choose option 3 to install the app on your Pi
5. **Deploy Updates**: Use option 4 to deploy future updates

### Interactive Mode
```bash
./tmbtool.sh
```
Shows the user-friendly main menu with clear explanations.

### Direct Commands
```bash
./tmbtool.sh config          # Configure server settings
./tmbtool.sh ssh-setup       # Setup SSH keys
./tmbtool.sh setup          # Install server environment
./tmbtool.sh deploy         # Deploy application
./tmbtool.sh test          # Run test suite
```

### Legacy Deploy Commands (Backwards Compatible)
```bash
./tmbtool.sh --prod                    # Deploy to configured server
./tmbtool.sh --prod admin@192.168.1.100  # Deploy to specific server
./tmbtool.sh --test-only              # Run tests only
./tmbtool.sh --build-only             # Build only
./tmbtool.sh --monitor                # Monitor server logs
```

## Configuration File

The `tmbtool.config` file stores all settings:

```bash
# Server connection settings
REMOTE_HOST="192.168.1.100"
REMOTE_USER="admin"
REMOTE_DIR="/home/admin/tomb"
CONNECTION_TYPE="ssh"
SSH_KEY_PATH="/Users/you/.ssh/tomb_key"
SSH_ALIAS="tomb-server"

# Application settings
REPO_URL="https://github.com/yourusername/tomb"
RELEASE_DEV_DIR="release_dev"
ENABLE_FTP_WRITE="false"

# Default build settings
RUN_TESTS="true"
BUILD_FRONTEND="true"
```

## Menu Options

### 1. Configuration
- Configure server hostname/IP
- Set username and installation directory
- Configure SSH alias for easy connection
- Set repository URL and build preferences
- Enable/disable FTP server with write access

### 2. SSH Tool
- Generate new SSH keys or use existing ones
- Copy public keys to server
- Configure SSH client settings
- Test passwordless authentication
- Uses server configuration from main config

### 3. Setup
- Complete server environment installation
- Install required packages (python3, ffmpeg, etc.)
- Install WM8960 Audio HAT drivers
- Clone application repository
- Install and configure the application
- Setup systemd service
- Optional FTP server configuration
- Automatic reboot option

### 4. Deploy
- Run comprehensive test suite
- Build Vue.js frontend
- Package release directory
- Upload to server via rsync
- Restart application service
- Perform health checks

### 5. Tests
- Run all test suites:
  - back/tests/ (business logic)
  - back/app/tests/unit/ (unit tests)
  - back/app/tests/integration/ (integration tests)
  - back/app/tests/routes/ (API tests)
  - back/tools/test_*.py (hardware tests)

### 6. View Config
- Display current configuration
- Show all settings and their values
- Verify configuration file status

## Server Files Integration

The script automatically deploys configuration files from the `server_files/` directory:

- `server_files/app.service` → `/etc/systemd/system/app.service`
- `server_files/asound.conf` → `/etc/asound.conf`

These files are included in the release package and deployed automatically.

## Migration Steps

1. **Test the new tool:**
   ```bash
   ./tmbtool.sh --help
   ./tmbtool.sh config  # Configure your server
   ```

2. **Setup SSH (if not already done):**
   ```bash
   ./tmbtool.sh ssh-setup
   ```

3. **Test deployment:**
   ```bash
   ./tmbtool.sh deploy
   ```

4. **Once satisfied, remove old scripts:**
   ```bash
   rm deploy.sh setup_ssh_key_to_rpi.sh back/setup.sh
   ```

## Improvements Over Original Scripts

### Enhanced SSH Setup
- ✅ Better error handling and validation
- ✅ Support for existing SSH keys
- ✅ Automatic SSH config management
- ✅ Connection testing and verification
- ✅ Uses server configuration from main config

### Improved Server Setup
- ✅ Non-interactive installation (no interruptions)
- ✅ All questions asked upfront
- ✅ Automatic FTP configuration
- ✅ Better error handling and status reporting
- ✅ Integrated service management

### Better Deployment
- ✅ Consistent with original deploy.sh functionality
- ✅ Integrated SSH key management
- ✅ Server configuration files deployment
- ✅ Comprehensive health checks

### Unified Experience
- ✅ Single tool for all operations
- ✅ Consistent configuration across all functions
- ✅ Interactive and command-line modes
- ✅ Better documentation and help system

## Troubleshooting

### Configuration Issues
- Run `./tmbtool.sh config` to reconfigure
- Check `tmbtool.config` file for correct settings
- Use `./tmbtool.sh` option 6 to view current config

### SSH Issues
- Run `./tmbtool.sh ssh-setup` to reconfigure SSH
- Test connection: `ssh your-alias`
- Check SSH config: `cat ~/.ssh/config`

### Deployment Issues
- Verify server is accessible: `ping your-server`
- Check SSH connection: `ssh your-alias`
- Review service logs: `./tmbtool.sh --monitor`

### Server Setup Issues
- Check server connectivity before setup
- Ensure SSH keys are configured first
- Review installation logs on the server

## Security Notes

- 🔒 Server passwords are never stored in configuration files
- 🔑 SSH key-based authentication is strongly recommended
- 🛡️ All connections use SSH for security
- 📝 Configuration files contain only connection metadata

## Support

If you encounter issues:
1. Check this migration guide
2. Use `./tmbtool.sh --help` for command reference
3. Review the configuration with option 6 in the main menu
4. Test individual components (SSH, config, etc.) separately