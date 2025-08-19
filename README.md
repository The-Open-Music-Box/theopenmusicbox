# The Open Music Box - Installation and Development Guide

This guide explains the installation and development process for the The Open Music Box application.

## Quick Installation Guide

This section is intended for users who only want to install the application on their Raspberry Pi.

### 1. Configuring the Raspberry Pi SD Card

*TODO: This section will be completed later.*

### 2. Configuring SSH with the Raspberry Pi

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
   - Desired alias for SSH configuration (e.g., tmbdev)

4. **Result**:
   - Your SSH key is copied to the Raspberry Pi
   - An entry is added to your SSH configuration
   - A test connection is automatically established

### 3. Deploying the Application

To deploy the application on the Raspberry Pi:

1. **Run the synchronization script** from the project directory:
   ```bash
   ./sync_to_tmbdev.sh
   ```
   This script synchronizes the contents of the `public_release` folder to the Raspberry Pi using the previously configured SSH alias.

2. **Install on the Raspberry Pi**:
   ```bash
   ssh tmbdev
   chmod +x setup.sh
   ./setup.sh
   ```
   The `setup.sh` script will install the application as a system service that starts automatically.

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
   ./sync_to_tmbdev.sh
   ```

4. **Restart the service**:
   ```bash
   ssh tmbdev
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

### Dependencies Between Repos and Scripts

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
                                                 │  sync_to_tmbdev.sh  │
                                                 │  Deploys to the Pi  │
                                                 └─────────────────────┘
```

**Important points to note**:

1. The `npm run serve` script of the frontend places its files in `../back/app/static/` – this path is fixed.
2. The `export_public_package.sh` script prepares the deployable version by extracting files from `../back/app/` to `../public_release/`.
3. All script paths are relative to this precise structure.

### Verifying the Structure

To verify that your folder structure is correct, you can run:

```bash
[ -d "$(pwd)/back" ] && [ -d "$(pwd)/front" ] && [ -d "$(pwd)/public_release" ] && echo "Structure OK" || echo "Incorrect structure"
```
This command will output "Structure OK" only if you are in the `tomb-rpi` folder with all required sub-folders.

### Development Workflow

#### 1. Preparing a New Frontend Release

To update the frontend:

1. **Navigate to the frontend directory**:
   ```bash
   cd front
   ```

2. **Compile the frontend files**:
   ```bash
   npm run serve
   ```

3. **Result**: The compiled files are automatically copied to the backend folder:
   ```
   back/app/static
   ```

#### 2. Preparing a New Backend Release

To generate the deployable package:

1. **Navigate to the backend directory**:
   ```bash
   cd back
   ```

2. **Run the export script**:
   ```bash
   ./export_public_package.sh
   ```

3. **Script functionality**:
   - Copies application files to the `public_release` folder
   - Automatically excludes temporary files, caches, and logs
   - Preserves important data (database, uploads)
   - Generates an optimized `requirements.txt` file
   - Copies configuration files like `app.service`

4. **Result**: A deployable version is created in the `public_release` folder.

## Troubleshooting Common Issues

- **SSH connection problem**: Check that the Raspberry Pi is connected to the network and accessible via IP address or hostname.
- **Synchronization failed**: Ensure that file permissions are correct and you have sufficient access rights.
- **Service not started**: Check the service status with `sudo systemctl status app.service`.
