# Hardware Abstraction Architecture

## Overview

This application uses a protocol/wrapper/factory pattern to abstract hardware access for all modules (audio player, GPIO, light sensor, motor, NFC, LED hat, etc). This ensures clean separation between business logic and hardware-specific code, and allows for easy mocking and testing on any platform (including non-Raspberry Pi environments).

## Pattern

- **Protocol (`*Hardware`)**: Defines the required methods for a hardware module (e.g., `AudioPlayerHardware`).
- **Real/Mock Implementations**: Each protocol has a real implementation (for Raspberry Pi) and a mock implementation (for dev/test environments).
- **Wrapper (`AudioPlayer`, `GPIOController`, etc)**: Generic class that delegates calls to the hardware implementation, providing a consistent interface.
- **Factory (`get_audio_player`, etc)**: Returns the appropriate wrapper instance based on environment/configuration.

## Adding a New Hardware Module
1. Define a protocol for the hardware API.
2. Implement both a real and a mock version.
3. Create a wrapper class that delegates to the protocol.
4. Create a factory function to select the implementation.
5. Expose only the factory in the module's `__init__.py`.

## Mock vs. Real Hardware
- The factory uses environment variables (e.g., `USE_MOCK_HARDWARE`) or platform checks to select between real and mock implementations.
- Mocks allow running and testing the app on any platform.

## Example Usage
```python
from app.src.module.audio_player import get_audio_player
player = get_audio_player()
player.play_track(1)
```

## Testing
- Tests are written to use the factory, ensuring both real and mock implementations are covered.

## Migration
- All legacy `*Interface` classes have been removed. Use the new protocol/wrapper/factory pattern for all hardware access.

---

For more details, see the docstrings in each module or contact the maintainers.
