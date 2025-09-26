# TMBTool Modular Architecture

## Overview

The TMBTool has been refactored from a single large script (~1000+ lines) into a modular architecture with separate files for different functionality areas. This improves maintainability, readability, and makes the codebase easier to extend.

## File Structure

```
tmbtool/
├── README.md          # This documentation
├── utils.sh          # Core utilities and common functions
├── config.sh         # Configuration management
├── ssh.sh            # SSH key setup and management
├── setup.sh          # Server installation and setup
└── deploy.sh         # Build, package, and deployment functions
```

## Module Descriptions

### 1. `utils.sh` - Core Utilities
**Purpose**: Provides common functions used across all modules.

**Key Functions**:
- `print_status()` - Colored output formatting
- `print_header()` - Section headers with decorative lines
- `ask_input()` - User input prompts with colors
- `ask_yes_no()` - Yes/no question prompts
- `validate_input()` - Input validation (hostname, username, path, alias)
- `load_config()` - Load configuration from file
- `save_config()` - Save configuration to file

**Dependencies**: None (loaded first)

### 2. `config.sh` - Configuration Management
**Purpose**: Handles all configuration-related functionality.

**Key Functions**:
- `configure_settings()` - Interactive configuration setup (5-step process)
- `view_config_menu()` - Display current configuration settings

**Features**:
- Step-by-step configuration with examples
- Input validation for all fields
- Default value suggestions
- Clear explanations for each setting

**Dependencies**: `utils.sh`

### 3. `ssh.sh` - SSH Management
**Purpose**: SSH key generation, setup, and connection management.

**Key Functions**:
- `setup_ssh_directory()` - Create and configure SSH directory
- `get_existing_keys()` - Discover existing SSH keys
- `select_ssh_key()` - Interactive key selection or creation
- `create_new_ssh_key()` - Generate new SSH key pairs
- `copy_public_key()` - Copy public key to remote server
- `update_ssh_config()` - Update SSH client configuration
- `test_ssh_connection()` - Test passwordless SSH connection
- `ssh_setup_menu()` - Main SSH setup interface

**Features**:
- Support for existing and new SSH keys
- Automatic SSH config management
- Connection testing and validation
- ssh-copy-id integration with fallback

**Dependencies**: `utils.sh`

### 4. `setup.sh` - Server Setup
**Purpose**: Remote server installation and environment configuration.

**Key Functions**:
- `server_setup_menu()` - Interactive server setup interface

**Features**:
- Comprehensive server environment installation
- Non-interactive setup (all questions asked upfront)
- WM8960 Audio HAT driver installation
- Application cloning and installation
- Optional FTP server configuration
- systemd service setup
- Automatic reboot handling

**Dependencies**: `utils.sh`

### 5. `deploy.sh` - Deployment Functions
**Purpose**: Build, package, and deploy the application.

**Key Functions**:
- `run_tests()` - Execute comprehensive test suite
- `build_frontend()` - Build Vue.js frontend
- `package_release()` - Create deployment package
- `deploy_to_server()` - Upload and deploy to server
- `deploy_menu()` - Interactive deployment interface
- `test_menu()` - Test execution interface
- `monitor_server()` - Server log monitoring

**Features**:
- Full CI/CD pipeline simulation
- Frontend and backend packaging
- Server file deployment
- Health checks and monitoring
- Service management

**Dependencies**: `utils.sh`

## Main Script (`tmbtool.sh`)

The main script has been significantly streamlined to ~220 lines (down from 1000+). It serves as the entry point and orchestrator:

**Responsibilities**:
- Module loading and validation
- Variable initialization
- Main menu display
- Command-line argument parsing
- Interactive menu handling

**Key Features**:
- Graceful error handling for missing modules
- Backward compatibility with all original commands
- Clean separation of concerns
- Minimal code duplication

## Benefits of Modular Architecture

### 1. **Maintainability**
- Each module has a single responsibility
- Easier to locate and fix bugs
- Changes isolated to specific functionality areas

### 2. **Readability**
- Smaller, focused files
- Clear separation of concerns
- Better code organization

### 3. **Extensibility**
- Easy to add new features in appropriate modules
- New modules can be added without touching existing code
- Plugin-like architecture

### 4. **Testing**
- Individual modules can be tested separately
- Easier to mock dependencies
- Better test isolation

### 5. **Collaboration**
- Multiple developers can work on different modules
- Reduced merge conflicts
- Clear ownership boundaries

## Dependencies and Loading Order

1. **`utils.sh`** - Loaded first (no dependencies)
2. **`config.sh`** - Depends on utils.sh
3. **`ssh.sh`** - Depends on utils.sh
4. **`setup.sh`** - Depends on utils.sh
5. **`deploy.sh`** - Depends on utils.sh

All modules are loaded by the main script with error checking.

## Variables and Configuration

### Global Variables
All configuration variables are defined in the main script and are available to all modules:

```bash
# Server connection
REMOTE_HOST=""
REMOTE_USER="admin"
REMOTE_DIR="/home/admin/tomb"
SSH_KEY_PATH=""
SSH_ALIAS=""

# Application settings
REPO_URL="https://github.com/yourusername/tomb"
RELEASE_DEV_DIR="release_dev"
ENABLE_FTP_WRITE="false"

# Build settings
RUN_TESTS="true"
BUILD_FRONTEND="true"
```

### Constants
```bash
# Paths
PROJECT_ROOT - Root directory of the project
CONFIG_FILE - Path to configuration file
SSH_DIR - SSH directory path
TMBTOOL_DIR - Module directory path

# Defaults
DEFAULT_REMOTE_DIR - Default installation directory
DEFAULT_SSH_USER - Default SSH username
DEFAULT_REPO_URL - Default repository URL
```

## Error Handling

Each module includes comprehensive error handling:
- Input validation
- File existence checks
- Network connectivity tests
- Service status verification
- Graceful failure with helpful error messages

## Usage Examples

The modular architecture maintains full backward compatibility:

```bash
# Interactive mode (recommended)
./tmbtool.sh

# Direct module access
./tmbtool.sh config
./tmbtool.sh ssh-setup
./tmbtool.sh setup
./tmbtool.sh deploy
./tmbtool.sh test

# Legacy commands (still supported)
./tmbtool.sh --prod
./tmbtool.sh --test-only
./tmbtool.sh --monitor
```

## Future Enhancements

The modular architecture makes it easy to add:
- New deployment targets
- Additional testing frameworks
- Monitoring integrations
- Configuration formats
- Authentication methods
- Backup and restore functionality

## Migration Notes

- All original functionality preserved
- No changes required to existing workflows
- Configuration files remain compatible
- Command-line arguments unchanged
- Performance improved (faster loading, less memory usage)