# TheMusicBox Technical Documentation

## Overview

TheMusicBox is an asynchronous Python application that uses FastAPI and Socket.IO to create a music playlist controller system. The application is designed to work with both real hardware (for production) and mock hardware (for development and testing). This document outlines the technical architecture, configuration system, and development workflows.

## Configuration System

### Architecture

The configuration system is built on a hierarchical model:

1. **Interface (`IConfig`)**: Defines the contract that all configurations must implement, ensuring consistency across environments.
2. **Base Implementation (`StandardConfig`)**: Production configuration that reads values from environment variables or uses defaults.
3. **Environment-Specific Configurations**:
   - `DevConfig`: Development configuration with mock hardware enabled
   - `TestConfig`: Testing configuration with temporary paths and mock hardware

### Configuration Factory

The `ConfigFactory` provides a centralized way to create and access different configuration types:

```python
from app.src.config.config_factory import ConfigFactory, ConfigType

# Get development configuration
dev_config = ConfigFactory.get_config(ConfigType.DEV)

# Get test configuration
test_config = ConfigFactory.get_config(ConfigType.TEST)

# Get production configuration
prod_config = ConfigFactory.get_config(ConfigType.STANDARD)
```

### Mock Hardware

The application includes mock implementations of hardware components to facilitate development and testing without physical hardware:

- Mock NFC Reader (`nfc_mock.py`)
- Mock Audio Player (`audio_mock.py`)
- Mock GPIO (`gpio_mock.py`)

These mock components simulate the behavior of their real hardware counterparts while allowing development on any machine.

## Startup Scripts

The application can be launched in different modes using dedicated startup scripts:

1. **Development Mode** (`start_dev.py`):
   - Uses `DevConfig` with mock hardware
   - Sets appropriate environment variables
   - Starts the FastAPI/Socket.IO server with Uvicorn
   - Enables debug mode and auto-reload

2. **Production Mode** (`start_app.py`):
   - Uses `StandardConfig` with real hardware
   - Configures paths for database and uploads
   - Starts the FastAPI/Socket.IO server with Uvicorn

3. **Test Mode** (`start_test.py`):
   - Uses `TestConfig` with mock hardware
   - Uses temporary paths for database and uploads
   - Runs tests with pytest

## Async Architecture

The application uses an asynchronous architecture based on:

1. **FastAPI/Socket.IO**: For the web server and real-time communication
2. **Async/Await**: For non-blocking I/O operations
3. **Application Class**: Main application controller that initializes components and handles the core application lifecycle

### Application Class (`app.src.core.application.Application`)

The `Application` class is the central component that:

1. Initializes the playlist controller and services
2. Loads and synchronizes playlists
3. Sets up hardware components (NFC, Audio, LED)
4. Provides the main async run method for the application lifecycle
5. Handles cleanup on shutdown

## Testing Strategy

The project uses pytest for testing with:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing component interactions
3. **Mock Objects**: Simulating hardware and external dependencies
4. **Test Configuration**: Using dedicated test paths and databases

Tests can be run using:

```
python start_test.py
```

For coverage reports:

```
python start_test.py --cov
```

## Project Structure

```
├── app/
│   ├── src/
│   │   ├── config/             # Configuration system
│   │   │   ├── __init__.py
│   │   │   ├── config_factory.py
│   │   │   ├── config_interface.py
│   │   │   ├── dev_config.py
│   │   │   ├── standard_config.py
│   │   │   └── test_config.py
│   │   ├── core/               # Core application components
│   │   │   ├── application.py
│   │   │   ├── container_async.py
│   │   │   └── playlist_controller.py
│   │   ├── module/             # Hardware modules
│   │   │   ├── audio_player/
│   │   │   ├── gpio/
│   │   │   └── nfc/
│   │   ├── monitoring/         # Logging and monitoring
│   │   ├── routes/             # API routes and websocket handlers
│   │   └── services/           # Business logic services
│   ├── main.py                 # ASGI application entry point
│   └── uploads/                # Upload directory for playlists
├── tests/                      # Test suite
├── start_app.py                # Production starter script
├── start_dev.py                # Development starter script
└── start_test.py               # Test runner script
```

## Setting Up Development Environment

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd back
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run in Development Mode**:
   ```bash
   python start_dev.py
   ```
   The application will be available at `http://localhost:5004`

5. **Run Tests**:
   ```bash
   python start_test.py
   ```

## Development Workflow

1. **Local Development**:
   - Use `start_dev.py` to run the application with mock hardware
   - Make changes to the code
   - The server will auto-reload when files are changed

2. **Testing**:
   - Run tests with `start_test.py`
   - Add new tests for new functionality
   - Ensure all tests pass before deployment

3. **Production Deployment**:
   - Use `start_app.py` to run in production mode with real hardware
   - Set appropriate environment variables for configuration

## API and WebSockets

The application provides:

1. **REST API** for playlist management and system control
2. **Socket.IO Events** for real-time updates on playback status and NFC tag scans

## Troubleshooting

- **Application won't start**: Check database path and upload folder permissions
- **Mock hardware not working**: Ensure `USE_MOCK_HARDWARE` environment variable is set
- **Tests failing**: Verify that test configuration is correctly set up with temporary paths
