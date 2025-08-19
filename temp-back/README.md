# TheMusicBox - Backend

> Backend for TheOpenMusicBox, an application that links music playlists to NFC tags for an interactive, tangible listening experience.

---

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Hardware Setup](#hardware-setup)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Contact / Support](#contact--support)

---

## Features
- NFC tag reading and playlist association
- Audio playback with volume and navigation controls
- REST API for playlist and audio file management
- WebSocket interface for real-time updates
- YouTube content download support
- Raspberry Pi hardware compatibility


---

## Requirements
- **Python** 3.9+
- **FFmpeg** (for audio processing)
- **Hardware (for Raspberry Pi):**
  - NFC Reader (PN532)
  - Sound card (WM8960)
  - Physical controls (buttons, rotary encoder)
  - Raspberry Pi

---

## Hardware Setup
- **NFC Reader:** Connect PN532 to Raspberry Pi (I2C/SPI/UART as required)
- **Sound Card:** WM8960 wiring per manufacturer instructions
- **Physical Controls:** Wire buttons and rotary encoder to GPIO pins (see `app/src/module/controles/`)
- For troubleshooting and detailed wiring diagrams, see the [Hardware Setup Guide](docs/HARDWARE_SETUP.md) *(to be created)*

---

## Installation

### Development Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

pip install -r requirements/dev.txt
```

#### Requirements Files
All requirements are now in the `requirements/` directory:
| File              | Purpose                                 |
|-------------------|-----------------------------------------|
| base.txt          | Core, cross-platform dependencies        |
| dev.txt           | Dev tools, lint, docs, CI (includes base)|
| prod.txt          | Raspberry Pi production (includes base)  |
| test.txt          | Testing/CI (includes base)               |

See `requirements/README.md` for details.

### Production Environment (Raspberry Pi)
```bash
sudo bash app/install_pi_system_deps.sh
python -m venv venv
source venv/bin/activate
pip install -r requirements/prod.txt
```

#### Automated Deployment
You can use the provided deployment script to install everything on your Raspberry Pi:
```bash
./install_on_pi.sh <pi_host> <target_dir> [--requirements prod|dev|test]
```
- Example: `./install_on_pi.sh pi@raspberrypi.local /home/pi/tmbbox --requirements prod`

This will copy the app folder, the selected requirements, `.env`, and `app.service`, then set up the virtual environment and install dependencies on the Pi.

---

## Configuration
Configuration parameters are defined in `app/src/config/app_config.py` and can be overridden using environment variables or a `.env` file.

### Environment Variables
| Variable           | Description                        | Default       |
|--------------------|------------------------------------|---------------|
| DEBUG              | Enable debug mode                  | False         |
| SOCKETIO_HOST      | SocketIO server host               | 0.0.0.0       |
| SOCKETIO_PORT      | SocketIO server port               | 5004          |
| UPLOAD_FOLDER      | Path for uploaded files            | uploads       |
| AUTO_PAUSE_ENABLED | Enable auto-pause on disconnect    | True          |
| ...                | *(see app_config.py for more)*     |               |

**Example `.env` file:**
```
DEBUG=True
SOCKETIO_HOST=0.0.0.0
SOCKETIO_PORT=5004
UPLOAD_FOLDER=uploads
AUTO_PAUSE_ENABLED=True
```

---

## Usage

### Development
```bash
python start_dev.py
```

### Production
```bash
python start_app.py
```

### Tests
```bash
pytest
```

---

## API Documentation

The backend uses FastAPI, which provides auto-generated, interactive API documentation. Once the backend server is running, you can access the following documentation UIs:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

These interfaces allow you to explore and test all available API endpoints directly from your browser.

### Example Endpoints
- `GET /api/volume` — Get the current system volume
- `POST /api/volume` — Set the system volume (0-100)
- `GET /api/health` — Health check and subsystem status
- `GET /api/playlists` — List playlists
- `POST /api/playlists` — Create a new playlist
- `POST /api/youtube/download` — Download a YouTube playlist or track

> **Note:** The root URL and port may differ if you change the default configuration. See your environment variables or `start_app.py` for details.

- Interactive API docs available at [`/docs`](http://localhost:5004/docs) when running (FastAPI default)
- Example endpoints:
  - `GET /api/playlists`
  - `POST /api/playlists`
  - `GET /api/tracks/{track_id}`
  - ...
- See [API Reference](docs/API_REFERENCE.md) *(to be created)*

---

## Project Structure
- `app/` - Application source code
  - `src/` - Main modules
    - `config/` - App configuration
    - `core/` - Core components
    - `module/` - Functional modules (audio, NFC, controls)
    - `routes/` - API routes
    - `services/` - Business services
- `tests/` - Unit and integration tests
- `scripts/` - Utility scripts

---

## Development Workflow
- **Linting:**
  - `flake8` for style checks
  - `pydocstyle` for docstring checks
- **Formatting:**
  - Use `black` or `isort` as configured
- **Pre-commit Hooks:**
  - Install with `pre-commit install`
  - Configured in `.pre-commit-config.yaml`
- **Code conventions:**
  - See `plan_amelioration.md` for coding standards and guidelines

---

## Testing
- Run all tests:
  ```bash
  pytest
  ```
- Test coverage is reported automatically if `pytest-cov` is installed
- Add new tests in the relevant `tests/` subdirectory

---

## Deployment

### Exporting a Public Package
To create a public-ready package (for open source or distribution):
```bash
./export_public_package.sh /path/to/export_dir
```
This will export only the `app` folder, production requirements, README, and service file to the target directory.

### Deploying to Raspberry Pi
See the Production Environment section above for automated deployment instructions.

- *(Add instructions for running as a service, Docker, or other deployment tools if applicable)*

---

## Contributing
- Please follow the code conventions and improvement plan in `plan_amelioration.md`
- Open issues or submit pull requests for new features or bug fixes

---

## License

This project is open source and released under the following terms:

- You are free to use, copy, modify, and distribute this software for any non-commercial purpose.
- Contributions are welcome from anyone via pull requests or issues.
- **Commercial use and monetization (selling, offering paid services, or bundling with paid products) is reserved exclusively to the original author (Jonathan Piette).**
- If you wish to monetize or use this project commercially, please contact the maintainer for licensing options.

---

## Contact / Support
- For questions, open an issue on GitHub or contact the maintainer.
- *(Add Discord, email, or other channels if available)*
