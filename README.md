# The Open Music Box - Installation and Development Guide

The Open Music Box is an interactive music player that links physical NFC tags to digital music playlists, creating a tangible music experience. This guide explains how to set up, use, and develop the application.

## Table of Contents

### For Users
- [Quick Installation Guide](#quick-installation-guide)
  - [1. Configuring the Raspberry Pi SD Card](#1-configuring-the-raspberry-pi-sd-card)
  - [2. Configuring SSH with the Raspberry Pi](#2-configuring-ssh-with-the-raspberry-pi)
  - [3. Deploying the Application](#3-deploying-the-application)
  - [4. Monitoring the Service](#4-monitoring-the-service)
  - [5. Adding Music to the Server](#5-adding-music-to-the-server)

### For Developers
- [Contributor Guide](#contributor-guide)
  - [Required Directory Structure](#required-directory-structure)
  - [Repository Cloning Instructions](#repository-cloning-instructions)
  - [Dependencies Between Repos and Scripts](#dependencies-between-repos-and-scripts)
  - [Development Workflow](#development-workflow)
  - [Project Components](#project-components)
    - [Documentation Directory](#documentation-directory)
    - [Back Directory](#back-directory)
    - [Front Directory](#front-directory)
    - [Public Release Directory](#public-release-directory)
    - [Release Dev Directory](#release-dev-directory)

- [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Quick Installation Guide

This section is intended for users who only want to install the application on their Raspberry Pi.

### 1. Configuring the Raspberry Pi SD Card

To set up a new Raspberry Pi for The Open Music Box:

1. **Download and install the Raspberry Pi Imager** from [raspberrypi.org](https://www.raspberrypi.org/software/)

2. **Insert your SD card** into your computer

3. **Open Raspberry Pi Imager and select**:
   - Choose OS: Raspberry Pi OS (32-bit) or Raspberry Pi OS Lite (32-bit) for headless setup
   - Choose Storage: Your SD card

4. **Click on the gear icon** (Advanced options) and configure:
   - Set hostname: `theopenmusicbox.local` (recommended)
   - Enable SSH
   - Set username and password (default: `admin` / `musicbox`)
   - Configure WiFi

5. **Click 'Write'** and wait for the process to complete

6. **Insert the SD card** into your Raspberry Pi and power it on

7. **Connect to your Raspberry Pi** via SSH to verify it's working:
   ```bash
   ssh admin@theopenmusicbox.local
   ```

### 2. Configuring SSH with the Raspberry Pi (optional)

SSH connection simplifies deployment and management of the Raspberry Pi.

#### Using the `setup_ssh_key_to_rpi.sh` Script

This script simplifies SSH configuration by automating several steps:

1. **Run the script**:
   ```bash
   ./setup_ssh_key_to_rpi.sh
   ```

2. **Available options**:
   - Use an existing SSH key or create a new one
   - Specify connection details for the Raspberry Pi
   - Create an SSH alias in your `~/.ssh/config` file

3. **Required information**:
   - Username on the Raspberry Pi (e.g., admin)
   - IP address or hostname (e.g., theopenmusicbox.local)
   - Desired alias for SSH configuration (e.g., theopenmusicbox, you will use this shortcut to connect easily to the Pi with the commmand ssh theopenmusicbox)

4. **Result**:
   - Your SSH key is copied to the Raspberry Pi
   - An entry is added to your SSH configuration
   - A test connection is automatically established

### 3. Deploying the Application

To deploy the application on your Raspberry Pi:

1. **Download the latest release** from the project's GitHub releases page.

2. **Extract the release archive** on your local machine:
   ```bash
   tar -xzf tomb-rpi-release-*.tar.gz
   ```
   
   Note: If you've already set up SSH access in step 2, you can use your configured SSH alias in the following steps.

3. **Transfer the files to your Raspberry Pi**:
   ```bash
   # Copy the files to your Raspberry Pi using your SSH alias (if configured in step 2)
   scp -r public_release/tomb-rpi/* theopenmusicbox:/home/admin/tomb/
   
   # Or using the direct hostname if you skipped the SSH configuration
   scp -r public_release/tomb-rpi/* admin@theopenmusicbox.local:/home/admin/tomb/
   ```

4. **Install on the Raspberry Pi**:
   ```bash
   # Connect to your Pi using your SSH alias (if configured in step 2)
   ssh theopenmusicbox
   
   # Or using the direct hostname if you skipped the SSH configuration
   ssh admin@theopenmusicbox.local
   
   # Then run the installation
   cd ~/tomb
   chmod +x setup.sh
   ./setup.sh
   ```
   The `setup.sh` script will install the application as a system service that starts automatically on boot.

### 4. Monitoring the Service

To monitor the running application:

```bash
sudo journalctl -fu app.service --output=cat
```
This command displays the service logs in real time.

### 5. Adding Music to the Server

To add new music:

1. **Place audio files in the upload folder**:
   ```
   public_release/app/data/upload
   ```

2. **Organization**:
   - Create a sub-folder for each playlist
   - Place audio files in the corresponding sub-folders

3. **Synchronize with the Raspberry Pi**:
   ```bash
   # If you're a developer with the full repository
   ./sync_tmbdev.sh
   
   # Or manually copy the files using your SSH alias (if configured)
   scp -r your_music_files/* theopenmusicbox:/home/admin/tomb/app/data/upload/
   
   # Or using the direct hostname if you skipped the SSH configuration
   scp -r your_music_files/* admin@theopenmusicbox.local:/home/admin/tomb/app/data/upload/
   ```

4. **Restart the service**:
   ```bash
   # Connect using your SSH alias (if configured)
   ssh theopenmusicbox
   
   # Or using the direct hostname if you skipped the SSH configuration
   ssh admin@theopenmusicbox.local
   
   # Then restart the service
   sudo systemctl restart app.service
   ```

5. **Result**: The server will automatically create playlists corresponding to the upload folders.

## Contributor Guide

This section is intended for developers who want to contribute to the project.

### Required Directory Structure

For the scripts to work correctly, it is **essential** to follow this directory layout:

```
theopenmusicbox/                  # Parent folder
├── tomb-rpi/                     # This repo (backend + frontend)
│   ├── back/                     # Python backend
│   ├── front/                    # Vue.js frontend
│   └── public_release/           # Deployable version
├── tomb-esp32-firmware/          # ESP32 firmware repo
└── tomb_flutter/                 # Flutter mobile app repo
```

### Repository Cloning Instructions

To set up the full development environment:

1. **Create the parent folder first**:
   ```bash
   mkdir -p theopenmusicbox
   cd theopenmusicbox
   ```

2. **Clone the repositories with the exact names**:
   ```bash
   # Clone the main repo (this repo)
   git clone https://github.com/TheOpenMusicBox/tomb-rpi.git

   # Clone the firmware repo (optional if you are not working on the ESP32)
   git clone https://github.com/TheOpenMusicBox/tomb-esp32-firmware.git

   # Clone the mobile app repo (optional if you are not working on the app)
   git clone https://github.com/TheOpenMusicBox/tomb_flutter.git
   ```

## Project Components

The Open Music Box project is organized into several key directories, each with a specific purpose in the development and deployment workflow.

### Documentation Directory

The `documentation/` directory contains essential documentation that harmonizes the application architecture:

- **code-style-guide.md**: Coding standards and best practices for the project
- **deployment-guide.md**: Instructions for deploying the application
- **routes-api.md**: API documentation and endpoint specifications
- **ui_theme.md**: UI design guidelines including color palette and styling
- **ui-refactor-report.md**: Documentation on UI refactoring decisions

This directory serves as the central reference for architectural decisions and standards that maintain consistency across the project.

### Back Directory

The `back/` directory contains the main application that runs on the Raspberry Pi:

- **app/**: Core application code
  - **src/**: Source code modules (audio, NFC, controls)
  - **data/**: User data (playlists, audio files) - excluded from public releases
  - **static/**: Frontend build output (automatically populated)
- **requirements/**: Python dependency files
- **tests/**: Unit and integration tests
- **export_public_package.sh**: Script to prepare the backend for deployment
- **setup.sh**: Installation script for the Raspberry Pi

This is the heart of the application, containing the Python backend that handles audio playback, NFC tag reading, and hardware control.

### Front Directory

The `front/` directory contains the user interface of the application:

- **src/**: Vue.js source code
  - **components/**: UI components
  - **assets/**: Images, icons, and other static assets
  - **config/**: Frontend configuration
- **public/**: Static files
- **scripts/**: Build and optimization scripts

The frontend is built with Vue.js and is embedded into the backend during the build process.

### Public Release Directory

The `public_release/` directory contains the release version provided to users:

- Generated by the `build_public_release.sh` script
- Contains a clean, deployable version of the application
- Excludes development files, tests, and sensitive data
- Includes an empty `app/data` directory structure for user content

This directory is packaged into a tar.gz archive for distribution to users.

### Release Dev Directory

The `release_dev/` directory is used during development:

- Generated by the `sync_tmbdev.sh` script
- Contains a development build of the application
- Used for testing and deploying to development servers
- Not included in version control (gitignored)

This directory allows developers to test changes before creating a public release.

### Dependencies Between Components

This diagram shows the key interactions between the different components:

```
 tomb-rpi/front          tomb-rpi/back                tomb-rpi/public_release
    │                        │                               │
    │                        │                               │
    │                        ▼                               │
    │     ┌───────────────────────────────────────┐          │
    └────►│ npm run serve                         │          │
          │ Compile and copy into back/app/static │          │
          └───────────────────────────────────────┘          │
                               │                             │
                               ▼                             │
                      ┌──────────────────────────┐           │
                      │ export_public_package.sh ├──────────►│
                      └──────────────────────────┘           │
                                                             │
                                                             ▼
                                                 ┌─────────────────────┐
                                                 │  sync_tmbdev.sh     │
                                                 │  Deploys to the Pi  │
                                                 └─────────────────────┘
```

**Important workflow notes**:

1. Frontend builds are placed in `back/app/static/` for integration
2. The backend's `export_public_package.sh` prepares files for the `public_release/` directory
3. For development, `sync_tmbdev.sh` builds into `release_dev/` and deploys to the Pi
4. For public distribution, `build_public_release.sh` creates a clean archive without sensitive data

### Verifying the Structure

To verify that your folder structure is correct, you can run:

```bash
[ -d "$(pwd)/back" ] && [ -d "$(pwd)/front" ] && [ -d "$(pwd)/public_release" ] && echo "Structure OK" || echo "Incorrect structure"
```
This command will output "Structure OK" only if you are in the `tomb-rpi` folder with all required sub-folders.

### Development Workflow

The Open Music Box development workflow involves several steps for efficient development, testing, and deployment.

#### 1. Development Environment Setup

1. **Clone the repository and set up the directory structure**:
   ```bash
   mkdir -p theopenmusicbox
   cd theopenmusicbox
   git clone https://github.com/TheOpenMusicBox/tomb-rpi.git
   ```

2. **Set up the backend environment**:
   ```bash
   cd tomb-rpi/back
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   pip install -r requirements/dev.txt
   ```

3. **Set up the frontend environment**:
   ```bash
   cd ../front
   npm install
   ```

#### 2. Development Cycle

##### Frontend Development

1. **Start the frontend development server**:
   ```bash
   cd front
   npm run serve
   ```
   This compiles the frontend and watches for changes. The compiled files are automatically placed in `back/app/static`.

2. **Make changes to the frontend code** in the `front/src` directory. The development server will automatically reload when changes are detected.

##### Backend Development

1. **Start the backend development server**:
   ```bash
   cd back
   python start_dev.py
   ```

2. **Make changes to the backend code** in the `back/app/src` directory.

3. **Run tests** to verify your changes:
   ```bash
   pytest
   ```

#### 3. Development Deployment

To test your changes on a development Raspberry Pi:

1. **Configure SSH access** to your development Pi using the provided script:
   ```bash
   ./setup_ssh_key_to_rpi.sh
   ```

2. **Deploy to the development Pi** using the sync script:
   ```bash
   ./sync_tmbdev.sh
   ```
   This script:
   - Creates a `release_dev` directory
   - Exports the backend package
   - Builds the frontend
   - Copies all files to the `release_dev` directory
   - Synchronizes the `release_dev` directory to the Pi using rsync

3. **Monitor the application** on the Pi:
   ```bash
   ssh tomb
   sudo journalctl -fu app.service --output=cat
   ```

#### 4. Creating a Public Release

When your changes are ready for distribution to users:

1. **Build the public release**:
   ```bash
   ./build_public_release.sh
   ```
   This script:
   - Creates a clean `public_release` directory
   - Exports the backend package
   - Creates an empty data directory structure (without user data)
   - Builds the frontend
   - Creates a dated tar.gz archive for distribution

2. **Distribute the archive** to users or upload it to a distribution platform.

#### 5. Continuous Integration

1. **Run linting and style checks**:
   ```bash
   cd back
   flake8
   pydocstyle
   ```

2. **Run tests with coverage**:
   ```bash
   pytest --cov=app
   ```

3. **Generate coverage report**:
   ```bash
   python tests/generate_coverage_report.py
   ```

## Troubleshooting Common Issues

- **SSH connection problem**: Check that the Raspberry Pi is connected to the network and accessible via IP address or hostname.
- **Synchronization failed**: Ensure that file permissions are correct and you have sufficient access rights.
- **Service not started**: Check the service status with `sudo systemctl status app.service`.
