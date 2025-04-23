# app/tests/api/ui/events.py

import curses
from typing import List, Dict, Any
from collections import deque
import json
from datetime import datetime

class EventsManager:
    """Manages the display of WebSocket events."""

    def __init__(self, window: 'curses.window', max_events: int = 100):
        self.window = window
        self.max_events = max_events
        self.events: deque = deque(maxlen=max_events)
        self.current_track: Dict[str, Any] = {}
        self.playback_status: Dict[str, Any] = {}
        self.needs_redraw = True
        self.last_draw_state = {
            'track': {},
            'status': {},
            'events_count': 0
        }

    def add_event(self, event_type: str, data: Dict[str, Any]):
        """Add a new event to the list."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.append({
            'timestamp': timestamp,
            'type': event_type,
            'data': data
        })

        # Update track progress or playback status
        if event_type == 'track_progress':
            if self.current_track != data:
                self.current_track = data
                self.needs_redraw = True
        elif event_type == 'playback_status':
            if self.playback_status != data:
                self.playback_status = data
                self.needs_redraw = True

    def draw(self):
        """Draw the events panel with current playback information."""
        # Check if redraw is needed
        if not self._needs_redraw():
            return

        self.window.clear()
        height, width = self.window.getmaxyx()

        # Draw playback status section
        self._draw_playback_status(1, width)

        # Draw events list
        events_start = 8  # Start after playback status section
        self._draw_events_list(events_start, height - events_start, width)

        # Draw borders and title
        self.window.box()
        self.window.addstr(0, 2, " Events ", curses.color_pair(2))

        # Update last draw state
        self.last_draw_state['track'] = self.current_track.copy()
        self.last_draw_state['status'] = self.playback_status.copy()
        self.last_draw_state['events_count'] = len(self.events)
        self.needs_redraw = False
        # No refresh here - let the window manager handle it

    def _needs_redraw(self) -> bool:
        """Check if the display needs to be redrawn."""
        if self.needs_redraw:
            return True

        if self.current_track != self.last_draw_state['track']:
            return True

        if self.playback_status != self.last_draw_state['status']:
            return True

        if len(self.events) != self.last_draw_state['events_count']:
            return True

        return False

    def _draw_playback_status(self, start_y: int, width: int):
        """Draw the current playback status and progress."""
        try:
            # Current track info
            if self.current_track:
                elapsed = self.current_track.get('elapsed', 0)
                total = self.current_track.get('total', 0)
                progress = self.current_track.get('progress', 0)

                # Draw progress bar
                self.window.addstr(start_y, 2, "Progress:")
                bar_width = width - 6
                filled = int(bar_width * (progress / 100))
                self.window.addstr(start_y + 1, 2, "[" + "=" * filled +
                                 " " * (bar_width - filled) + "]")

                # Draw time
                time_str = f"{int(elapsed)}s / {int(total)}s"
                self.window.addstr(start_y + 2, 2, time_str)

            # Playback status
            if self.playback_status:
                status = self.playback_status.get('status', 'unknown')
                playlist = self.playback_status.get('playlist', {})
                track = self.playback_status.get('current_track', {})

                status_color = curses.color_pair(3) if status == 'playing' else curses.color_pair(5)
                self.window.addstr(start_y + 4, 2, f"Status: ", curses.color_pair(2))
                self.window.addstr(status.upper(), status_color)

                if playlist:
                    self.window.addstr(start_y + 5, 2,
                                     f"Playlist: {playlist.get('name', 'Unknown')} "
                                     f"({playlist.get('track_count', 0)} tracks)")
        except curses.error:
            # Handle potential curses errors gracefully
            pass

    def _draw_events_list(self, start_y: int, height: int, width: int):
        """Draw the list of recent events."""
        try:
            self.window.addstr(start_y - 1, 2, "Recent Events:", curses.color_pair(2))

            for i, event in enumerate(reversed(self.events)):
                if i >= height - 2:  # Leave space for borders
                    break

                y = start_y + i
                timestamp = event['timestamp']
                event_type = event['type']

                # Format event line
                event_str = f"{timestamp} | {event_type}"
                if len(event_str) > width - 4:
                    event_str = event_str[:width-7] + "..."

                # Choose color based on event type
                color = curses.color_pair(5)  # Default cyan
                if 'error' in event_type.lower():
                    color = curses.color_pair(4)  # Red for errors
                elif 'success' in event_type.lower():
                    color = curses.color_pair(3)  # Green for success

                self.window.addstr(y, 2, event_str, color)
        except curses.error:
            # Handle potential curses errors gracefully
            pass