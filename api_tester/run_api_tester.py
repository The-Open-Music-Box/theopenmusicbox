# api_tester/run_api_tester.py

# app/tests/run_api_tester.py

import os
import sys
import argparse
from pathlib import Path

def setup_python_path():
    """Add the project root to Python path"""
    root_dir = Path(__file__).parent.parent.parent.resolve()
    if not (root_dir / "app").exists():
        print(f"Error: Could not find 'app' directory in {root_dir}")
        sys.exit(1)
    sys.path.insert(0, str(root_dir))

def main_wrapper():
    setup_python_path()

    try:
        # Now we can safely import our module
        from app.tests.api.main import main
    except ImportError as e:
        print(f"Error importing API tester modules: {e}")
        print("Make sure you are running this script from the correct directory")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="API Tester for The Music Box")
    parser.add_argument(
        "--host",
        default="http://tmbdev.local:5005",
        help="Host URL of the API (default: http://tmbdev.local:5005)"
    )

    args = parser.parse_args()

    try:
        import curses
        curses.wrapper(lambda stdscr: main(stdscr, args.host))
    except KeyboardInterrupt:
        print("\nExiting...")
    except curses.error as e:
        print(f"Terminal error: {e}")
        print("Make sure your terminal supports curses and is properly configured")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main_wrapper()