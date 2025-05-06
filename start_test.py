#!/usr/bin/env python
"""
Test runner script that uses TestConfig.
This script runs the tests with the proper test configuration.
"""
import sys
import os
import subprocess
from pathlib import Path

# Ensure app directory is in path
sys.path.append(str(Path(__file__).resolve().parent))

from app.src.config.config_factory import ConfigFactory, ConfigType

print("[TheMusicBox] Starting tests with TEST configuration")

# Get test configuration
config = ConfigFactory.get_config(ConfigType.TEST)

if not config.use_mock_hardware:
    print("[TheMusicBox] WARNING: Mock hardware is not enabled in test configuration!")
else:
    print("[TheMusicBox] Using MOCK hardware for tests")

print(f"[TheMusicBox] Test config settings:")
print(f"  - Database file: {config.db_file}")
print(f"  - Upload folder: {config.upload_folder}")
print(f"  - Debug mode: {config.debug}")

# Set environment variables for tests
os.environ["TESTING"] = "1"
os.environ["USE_MOCK_HARDWARE"] = "1"

try:
    print("[TheMusicBox] Running tests...")
    
    # Run the tests using pytest
    test_cmd = ["python", "-m", "pytest", "tests/", "-v"]
    
    # Add coverage report if requested
    if "--cov" in sys.argv:
        test_cmd.extend(["--cov=app", "--cov-report=term"])
    
    # Pass any additional arguments to pytest
    for arg in sys.argv[1:]:
        if arg != "--cov":  # Skip this as we've already handled it
            test_cmd.append(arg)
    
    # Display command
    print(f"[TheMusicBox] Test command: {' '.join(test_cmd)}")
    
    # Execute the tests
    result = subprocess.run(test_cmd)
    sys.exit(result.returncode)
    
except KeyboardInterrupt:
    print("\n[TheMusicBox] Tests interrupted")
    sys.exit(1)
except Exception as e:
    print(f"[TheMusicBox] ERROR: {str(e)}")
    sys.exit(1)
