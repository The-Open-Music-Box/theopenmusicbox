# Tests for TheMusicBox Backend

This directory contains automated tests for the backend FastAPI application.

## How to Run the Tests

1. **Ensure your virtual environment is activated**
   ```sh
   source ../venv/bin/activate
   ```
   (or use your preferred method to activate the venv)

2. **Install dependencies (if not already installed)**
   ```sh
   pip install -r ../requirements.txt
   ```

3. **Run all tests**
   ```sh
   pytest --maxfail=1 --disable-warnings -v
   ```

   - This will run all tests in this directory and show verbose output.
   - The `--maxfail=1` flag stops at the first failure (remove it to run all tests regardless of failures).

4. **Test Output**
   - You should see output indicating which tests passed or failed.
   - All tests should pass before merging or deploying changes.

## Notes
- Tests use FastAPI's `TestClient` for API endpoint validation.
- The database used for tests is the same as development unless mocked or configured otherwise.
- If you add new endpoints or features, please add corresponding tests.

## Troubleshooting
- If you encounter import errors, verify your `PYTHONPATH` includes the `app` directory.
- For async tests, `pytest-asyncio` is available and configured.

---

For any issues, see the main project README or contact the maintainer.
