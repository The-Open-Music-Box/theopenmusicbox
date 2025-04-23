# app/tests/api/ui/window.py

import curses
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class Window:
    """Manages the curses window and provides layout management."""

    def __init__(self, stdscr: 'curses.window'):
        self.stdscr = stdscr

        # Enable double buffering and configure timeout
        curses.use_env(True)  # Enable terminal size detection
        curses.curs_set(0)    # Hide cursor

        # Initialize screen
        self.setup_colors()
        self.height, self.width = stdscr.getmaxyx()

        # Calculate panel dimensions
        self.menu_width = min(30, self.width // 4)
        self.events_width = min(40, self.width // 3)
        self.content_width = self.width - self.menu_width - self.events_width

        # Create pads with extra space for scrolling
        self.menu_win = curses.newpad(1000, self.menu_width)
        self.content_win = curses.newpad(1000, self.content_width)
        self.events_win = curses.newpad(1000, self.events_width)

        # Initial panel positions
        self.menu_pos = (0, 0)
        self.content_pos = (0, self.menu_width)
        self.events_pos = (0, self.menu_width + self.content_width)

        # Initialize last dimensions for resize detection
        self.last_height = self.height
        self.last_width = self.width

    def setup_colors(self):
        """Initialize color pairs."""
        try:
            curses.start_color()
            curses.use_default_colors()

            # Define color pairs
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Selected item
            curses.init_pair(2, curses.COLOR_YELLOW, -1)                 # Headers
            curses.init_pair(3, curses.COLOR_GREEN, -1)                  # Success
            curses.init_pair(4, curses.COLOR_RED, -1)                    # Error
            curses.init_pair(5, curses.COLOR_CYAN, -1)                  # Info
        except Exception as e:
            logger.error(f"Error setting up colors: {str(e)}")

    def check_resize(self):
        """Check if terminal has been resized and update dimensions."""
        try:
            new_height, new_width = self.stdscr.getmaxyx()
            if new_height != self.height or new_width != self.width:
                self.height = new_height
                self.width = new_width

                # Recalculate panel dimensions
                self.menu_width = min(30, self.width // 4)
                self.events_width = min(40, self.width // 3)
                self.content_width = self.width - self.menu_width - self.events_width

                # Update panel positions
                self.content_pos = (0, self.menu_width)
                self.events_pos = (0, self.menu_width + self.content_width)

                # Clear screen and redraw
                self.stdscr.clear()
                self.draw_boxes()
                return True
        except Exception as e:
            logger.error(f"Error checking resize: {str(e)}")
        return False

    def refresh_all(self):
        """Refresh all panels using double buffering."""
        try:
            # Check for resize
            if self.check_resize():
                logger.debug("Terminal resized, redrawing all windows")

            # Clear the screen
            self.stdscr.erase()

            # Draw boxes
            self.draw_boxes()

            # Calculate visible areas
            visible_height = self.height - 2  # Account for borders

            try:
                # Refresh each pad in its viewport
                self.menu_win.noutrefresh(0, 0, 1, self.menu_pos[1],
                                        visible_height, self.menu_pos[1] + self.menu_width-1)

                self.content_win.noutrefresh(0, 0, 1, self.content_pos[1],
                                           visible_height, self.content_pos[1] + self.content_width-1)

                self.events_win.noutrefresh(0, 0, 1, self.events_pos[1],
                                          visible_height, self.events_pos[1] + self.events_width-1)

                # Update the physical screen
                curses.doupdate()
            except curses.error as e:
                logger.error(f"Error refreshing pads: {str(e)}")
                # Try to recover by redrawing everything
                self.stdscr.clear()
                self.draw_boxes()
                curses.doupdate()

        except Exception as e:
            logger.error(f"Fatal error in refresh_all: {str(e)}")
            raise

    def draw_boxes(self):
        """Draw boxes around all windows with titles."""
        try:
            # Draw main window border
            self.stdscr.box()

            # Draw separators between panels
            for y in range(self.height):
                self.stdscr.addch(y, self.menu_width, curses.ACS_VLINE)
                self.stdscr.addch(y, self.menu_width + self.content_width, curses.ACS_VLINE)

            # Draw titles
            self.stdscr.addstr(0, 2, " Menu ", curses.color_pair(2))
            self.stdscr.addstr(0, self.menu_width + 2, " Response ", curses.color_pair(2))
            self.stdscr.addstr(0, self.menu_width + self.content_width + 2, " Events ", curses.color_pair(2))

            # Refresh the main window
            self.stdscr.noutrefresh()

        except Exception as e:
            logger.error(f"Error drawing boxes: {str(e)}")

    def create_panel(self, y: int, x: int, height: int, width: int) -> 'curses.window':
        """Create a new panel window."""
        return curses.newpad(height, width)

    def draw_box(self, win: 'curses.window', title: Optional[str] = None):
        """Draw a box around a window with an optional title."""
        win.box()
        if title:
            win.addstr(0, 2, f" {title} ", curses.color_pair(2))

    def draw_progress_bar(self, win: 'curses.window', y: int, x: int, width: int,
                         progress: float, total: float) -> None:
        """Draw a progress bar."""
        progress_width = int((progress / total) * (width - 2))
        win.addstr(y, x, "[" + "=" * progress_width +
                  " " * (width - 2 - progress_width) + "]")

    def clear_panel(self, win: 'curses.window'):
        """Clear a panel while preserving its border."""
        height, width = win.getmaxyx()
        for y in range(1, height-1):
            win.addstr(y, 1, " " * (width-2))

    def get_content_area(self, win: 'curses.window') -> Tuple[int, int]:
        """Get the usable area of a panel (excluding borders)."""
        height, width = win.getmaxyx()
        return height - 2, width - 2  # Subtract borders