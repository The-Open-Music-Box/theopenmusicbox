# app/tests/api/ui/menu.py

import curses
from typing import List, Optional
from app.tests.api.models.menu_item import MenuItem
import time
import logging

logger = logging.getLogger(__name__)

class MenuManager:
    """Manages menu rendering and navigation."""

    def __init__(self, window: 'curses.window'):
        self.window = window
        self.items: List[MenuItem] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.last_key_time = 0
        self.key_repeat_delay = 0.1  # 100ms delay between key repeats

    def add_item(self, item: MenuItem):
        """Add a menu item to the list."""
        self.items.append(item)

    def draw(self):
        """Draw the menu."""
        try:
            self.window.erase()
            height, width = self.window.getmaxyx()
            visible_items = height - 2  # Space for borders

            # Draw menu items
            for i, item in enumerate(self.items[self.scroll_offset:self.scroll_offset + visible_items]):
                y = i + 1  # +1 for border

                # Format menu text
                shortcut = f"({item.shortcut})" if item.shortcut else "   "
                menu_text = f"{shortcut} {item.title}"

                # Truncate if too long
                max_text_width = width - 4
                if len(menu_text) > max_text_width:
                    menu_text = menu_text[:max_text_width-3] + "..."

                try:
                    # Highlight selected item
                    if i + self.scroll_offset == self.selected_index:
                        self.window.attron(curses.color_pair(1))
                        self.window.addstr(y, 2, menu_text)
                        self.window.attroff(curses.color_pair(1))
                    else:
                        self.window.addstr(y, 2, menu_text)
                except curses.error:
                    continue  # Skip if can't draw at this position

            # Draw scrollbar if needed
            if len(self.items) > visible_items:
                self._draw_scrollbar(height, width)

        except Exception as e:
            logger.error(f"Error drawing menu: {str(e)}")

    def handle_input(self, key: int) -> Optional[MenuItem]:
        """Handle keyboard input."""
        if not self.items:
            return None

        try:
            height = self.window.getmaxyx()[0]
            visible_items = height - 2  # Subtract borders
            current_time = time.time()

            # Check for key repeat delay
            if current_time - self.last_key_time < self.key_repeat_delay:
                return None
            self.last_key_time = current_time

            # Handle navigation keys
            if key == curses.KEY_UP:
                self._move_selection(-1, visible_items)
            elif key == curses.KEY_DOWN:
                self._move_selection(1, visible_items)
            elif key == curses.KEY_PPAGE:  # Page Up
                self._move_selection(-visible_items, visible_items)
            elif key == curses.KEY_NPAGE:  # Page Down
                self._move_selection(visible_items, visible_items)
            elif key == curses.KEY_HOME:
                self.selected_index = 0
                self.scroll_offset = 0
            elif key == curses.KEY_END:
                self.selected_index = len(self.items) - 1
                self._ensure_selection_visible(visible_items)
            else:
                # Check for shortcut keys
                try:
                    char = chr(key).lower()
                    for i, item in enumerate(self.items):
                        if item.shortcut and item.shortcut.lower() == char:
                            self.selected_index = i
                            self._ensure_selection_visible(visible_items)
                            return item
                except (ValueError, AttributeError):
                    pass

            return None

        except Exception as e:
            logger.error(f"Error handling input: {str(e)}")
            return None

    def _move_selection(self, delta: int, visible_items: int):
        """Move the selection by delta items."""
        self.selected_index = max(0, min(len(self.items) - 1,
                                       self.selected_index + delta))
        self._ensure_selection_visible(visible_items)

    def _ensure_selection_visible(self, visible_items: int):
        """Ensure the selected item is visible in the viewport."""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_items:
            self.scroll_offset = max(0, self.selected_index - visible_items + 1)

    def _draw_scrollbar(self, height: int, width: int):
        """Draw a scrollbar if needed."""
        try:
            if not self.items:
                return

            # Calculate scrollbar parameters
            visible_items = height - 2
            total_items = len(self.items)
            scrollbar_height = max(1, int((visible_items / total_items) * (height - 2)))
            scrollbar_pos = int((self.scroll_offset / total_items) * (height - 2))

            # Draw scrollbar
            for i in range(height - 2):
                if scrollbar_pos <= i < scrollbar_pos + scrollbar_height:
                    self.window.addch(i + 1, width - 1, curses.ACS_CKBOARD)
                else:
                    self.window.addch(i + 1, width - 1, curses.ACS_VLINE)

        except Exception as e:
            logger.error(f"Error drawing scrollbar: {str(e)}")

    def get_selected_item(self) -> Optional[MenuItem]:
        """Get the currently selected menu item."""
        if not self.items or self.selected_index >= len(self.items):
            return None
        return self.items[self.selected_index]