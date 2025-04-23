# app/tests/api/main.py

import curses
import logging
import argparse
from app.tests.api.core.app import Application

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='api_tester.log'
)

def main(stdscr, host):
    """Initialize and run the application."""
    # Set up curses
    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(1)   # Non-blocking input

    # Create and run application
    app = Application(stdscr, host)
    app.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API Tester for The Music Box")
    parser.add_argument(
        "--host",
        default="http://tmbdev.local:5005",
        help="Host URL of the API (default: http://tmbdev.local:5005)"
    )

    args = parser.parse_args()

    try:
        curses.wrapper(lambda stdscr: main(stdscr, args.host))
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        raise