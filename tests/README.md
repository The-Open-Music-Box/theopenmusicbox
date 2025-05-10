# TheMusicBox Test Documentation

## Overview

This document provides comprehensive guidance on the test suite for TheMusicBox application. The test suite is designed to ensure the reliability and correctness of the application's core functionality, including playlist management, NFC tag detection, and audio playback.

## Test Categories

The test suite is organized into several categories using pytest markers:

### Test Types

- **Unit Tests** (`@pytest.mark.unit`): Test individual components in isolation
- **Integration Tests** (`@pytest.mark.integration`): Test interactions between components
- **API Tests** (`@pytest.mark.api`): Test REST API endpoints

### Feature Areas

- **NFC Tests** (`@pytest.mark.nfc`): Tests related to NFC tag detection and handling
- **Audio Tests** (`@pytest.mark.audio`): Tests related to audio playback functionality
- **Playlist Tests** (`@pytest.mark.playlist`): Tests related to playlist management

### Performance Categories

- **Slow Tests** (`@pytest.mark.slow`): Tests that take longer to execute
- **Fast Tests** (`@pytest.mark.fast`): Tests that execute quickly

## Running Tests

### Basic Test Run

To run all tests:

```bash
python start_test.py
```

### Run with Coverage

To run tests with coverage reporting:

```bash
python start_test.py --cov
```

### Run Specific Categories

To run tests with specific markers:

```bash
# Run all API tests
python start_test.py -m "api"

# Run all audio-related tests
python start_test.py -m "audio"

# Run tests that are both API and audio-related
python start_test.py -m "api and audio"

# Run all tests except slow ones
python start_test.py -m "not slow"
```

### Run Specific Test Files

To run tests from a specific file:

```bash
python start_test.py tests/src/api/test_playback.py
```

### Run Specific Test Functions

To run a specific test function:

```bash
python start_test.py tests/src/api/test_playback.py::test_playlist_start
```

## Test Structure

The test suite is organized as follows:

- `tests/conftest.py` - Common fixtures and setup
- `tests/helpers/` - Helper modules for testing
  - `assertions.py` - Common assertion functions
  - `utils.py` - Utility functions and classes
  - `find_non_english.py` - Tool to identify non-English comments
- `tests/src/` - Test modules organized by application structure
  - `api/` - API endpoint tests
  - `core/` - Core application tests
  - `module/` - Module-specific tests
  - `services/` - Service layer tests

## Test Fixtures

The test suite provides several fixtures to assist with testing:

- `test_client_with_mock_db`: FastAPI TestClient with an isolated test database
- `dummy_audio`: A simple mock audio player that records calls
- `mock_playlist_with_tracks`: Creates a test playlist with mock tracks
- `mock_nfc_handler`: A mock NFC handler for testing NFC functionality

## Test Utilities

### Assertion Helpers

The `tests/helpers/assertions.py` module provides standardized assertion functions:

- `assert_success_response`: Assert that an API response indicates success
- `assert_error_response`: Assert that an API response indicates an error
- `assert_nfc_status`: Assert that an NFC status response contains the expected status
- `assert_playback_status`: Assert that a playback status response contains the expected status

### Test Utilities

The `tests/helpers/utils.py` module provides utility functions and classes:

- `AsyncTestHelper`: Helper class for testing async code
- `MockHelpers`: Helper methods for creating common mocks
- `EventCollector`: Collect events for testing asynchronous event-based code

## Test Environment

Tests run in a mock hardware environment by default, which simulates the hardware components (NFC reader, audio player) without requiring actual hardware. This allows tests to run in any environment, including CI/CD pipelines.

The test environment is configured through the `ConfigType.TEST` configuration, which sets up:

- A temporary database file
- A temporary upload folder
- Mock hardware components

## Best Practices

When writing tests for TheMusicBox, follow these best practices:

1. **Use appropriate markers**: Categorize your tests with the appropriate markers to make them easier to find and run.
2. **Use fixtures**: Use the provided fixtures to set up test data and dependencies.
3. **Test edge cases**: Include tests for error conditions and edge cases, not just the happy path.
4. **Keep tests isolated**: Each test should be independent of others and should not rely on state from previous tests.
5. **Use descriptive names**: Test names should clearly describe what they're testing.
6. **Follow AAA pattern**: Structure tests with Arrange, Act, Assert sections.
7. **Use helper functions**: Use the provided assertion helpers and utilities to keep tests clean and consistent.

## Troubleshooting

If tests are failing, check the following:

1. **Environment setup**: Make sure the test environment is properly set up with the required dependencies.
2. **Database state**: Check if the test database is in the expected state.
3. **Mock hardware**: Verify that the mock hardware components are functioning correctly.
4. **Async issues**: For tests involving async code, make sure the async functions are properly awaited.

## Adding New Tests

When adding new tests:

1. Place them in the appropriate directory based on what they're testing.
2. Add appropriate markers to categorize the test.
3. Use existing fixtures and utilities where possible.
4. Follow the naming convention of existing tests.
5. Include docstrings that clearly describe what the test is verifying.

## Continuous Integration

The test suite is integrated with the CI/CD pipeline and runs automatically on pull requests and commits to the main branch. All tests must pass before code can be merged.
