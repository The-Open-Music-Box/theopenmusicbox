#!/usr/bin/env python
"""
Test runner script that uses TestConfig.
This script runs the tests with the proper test configuration.
"""
import sys
import os
import subprocess
from pathlib import Path
import site

# Check if we're already in a virtual environment
def is_venv_active():
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

# Activate the venv if not already active
if not is_venv_active():
    print("[TheMusicBox] Activating virtual environment...")
    venv_path = Path(__file__).resolve().parent / 'venv'
    
    if not venv_path.exists():
        print(f"[TheMusicBox] Error: Virtual environment not found at {venv_path}")
        print("[TheMusicBox] Please create a virtual environment with 'python -m venv venv' in the back folder")
        sys.exit(1)
    
    # Platform-specific activation paths
    if sys.platform == 'win32':
        activate_script = venv_path / 'Scripts' / 'python.exe'
    else:  # macOS and Linux
        activate_script = venv_path / 'bin' / 'python'
    
    if not activate_script.exists():
        print(f"[TheMusicBox] Error: Python interpreter not found at {activate_script}")
        sys.exit(1)
        
    print(f"[TheMusicBox] Using Python from: {activate_script}")
    
    # Re-execute the current script with the venv's Python
    os.execl(str(activate_script), str(activate_script), *sys.argv)
    # The script will restart from this point with the venv Python


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
