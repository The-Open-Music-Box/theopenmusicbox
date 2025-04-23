# tests/conftest.py

import sys
import os
import pathlib
import warnings

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # If dotenv is not installed, skip loading .env

# Filter out specific deprecation warnings from rx library
warnings.filterwarnings('ignore', category=DeprecationWarning,
                       message='datetime.datetime.utcfromtimestamp.*',
                       module='rx.internal.constants')
warnings.filterwarnings('ignore', category=DeprecationWarning,
                       message='datetime.datetime.utcnow.*',
                       module='rx.internal.basic')

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the app directory to the Python path
app_dir = os.path.join(project_root, 'app')
sys.path.insert(0, app_dir)

# Add the tests directory to the Python path
tests_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, tests_dir)
