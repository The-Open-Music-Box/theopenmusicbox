# TheMusicBox - Backend

> Backend for TheMusicBox, an application that links music playlists to NFC tags for an interactive, tangible listening experience.

---

## Table of Contents
- [Features](#features)
- [Screenshots](#screenshots)
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

## Screenshots
<!-- Add screenshots or animated GIFs here -->

---

## Requirements
- **Python** 3.9+
- **FFmpeg** (for audio processing)
- **Hardware (for Raspberry Pi):**
  - NFC Reader (PN532)
  - Sound card (WM8960)
  - Physical controls (buttons, rotary encoder)

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

pip install -r requirements_dev.txt
pip install -r requirements_base.txt
```

#### Requirements Files
| File                  | Purpose                                             |
|----------------------|-----------------------------------------------------|
| requirements_base.txt | Core, cross-platform dependencies for the app       |
| requirements_dev.txt  | Dev tools, test, lint, docs, CI                    |
| requirements_prod.txt | Raspberry Pi-specific production dependencies      |
| requirements_test.txt | Dependencies for running tests/CI                  |

### Production Environment (Raspberry Pi)
```bash
sudo bash app/install_pi_system_deps.sh
python -m venv venv
source venv/bin/activate
pip install -r requirements_base.txt
pip install -r requirements_prod.txt
```

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
- Recommended for Raspberry Pi (systemd service, etc.)
- *(Add instructions for running as a service, Docker, or other deployment tools if applicable)*

---

## Contributing
- Please follow the code conventions and improvement plan in `plan_amelioration.md`
- Open issues or submit pull requests for new features or bug fixes

---

## License
[To be defined]

---

## Contact / Support
- For questions, open an issue on GitHub or contact the maintainer.
- *(Add Discord, email, or other channels if available)*
