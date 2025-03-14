# app/tests/api/core/app.py

import curses
import json
import time
from typing import Dict, Any, Optional, Union, List
import logging
from app.tests.api.ui.window import Window
from app.tests.api.ui.menu import MenuManager
from app.tests.api.ui.events import EventsManager
from app.tests.api.models.menu_item import MenuItem
from app.tests.api.services.api_client import APIClient
from app.tests.api.services.socket_client import SocketClient

logger = logging.getLogger(__name__)

class Application:
    """Main application class that coordinates all components."""

    def __init__(self, stdscr: 'curses.window', host: str = "http://localhost:5000"):
        # Initialize curses settings
        curses.halfdelay(1)  # 100ms input timeout
        curses.curs_set(0)   # Hide cursor

        # Initialize components
        self.window = Window(stdscr)
        self.menu = MenuManager(self.window.menu_win)
        self.events = EventsManager(self.window.events_win)
        self.api = APIClient(host)
        self.socket = SocketClient(host)

        # Set up state
        self.running = True
        self.current_content: Optional[Dict[str, Any]] = None
        self.last_update = 0
        self.update_interval = 0.1  # 100ms between updates

        # Set up WebSocket handlers
        self._setup_socket_handlers()

        # Create menu items
        self._setup_menu()

    def _setup_socket_handlers(self):
        """Set up WebSocket event handlers."""
        self.socket.on('track_progress', lambda data: self._handle_event('track_progress', data))
        self.socket.on('playback_status', lambda data: self._handle_event('playback_status', data))

    def _handle_event(self, event_type: str, data: Dict[str, Any]):
        """Handle incoming WebSocket events."""
        self.events.add_event(event_type, data)
        # Don't refresh immediately - let the main loop handle it

    def _should_update(self) -> bool:
        """Check if enough time has passed for the next update."""
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.last_update = current_time
            return True
        return False

    def _setup_menu(self):
        """Set up the menu items."""
        menu_items = [
            MenuItem("Get Playlists", self.get_playlists, "List all playlists", "p"),
            MenuItem("Play Playlist", self.play_playlist, "Play a specific playlist", "l"),
            MenuItem("Pause", self.pause_playback, "Pause playback", "s"),
            MenuItem("Resume", self.resume_playback, "Resume playback", "r"),
            MenuItem("Stop", self.stop_playback, "Stop playback", "x"),
            MenuItem("Next Track", self.next_track, "Skip to next track", "n"),
            MenuItem("Previous Track", self.previous_track, "Go to previous track", "b"),
            MenuItem("Get Volume", self.get_volume, "Get current volume", "v"),
            MenuItem("Set Volume", self.set_volume, "Set volume level", "m"),
            MenuItem("System Info", self.get_system_info, "Get system information", "i"),
            MenuItem("Quit", self.quit, "Exit application", "q")
        ]

        for item in menu_items:
            self.menu.add_item(item)

    def display_content(self, content: Union[Dict[str, Any], List[Any], str]) -> None:
        """Display content in the content panel."""
        try:
            self.window.content_win.erase()
            y = 1
            height, width = self.window.get_content_area(self.window.content_win)

            # Display raw data first if it's a dictionary
            if isinstance(content, dict):
                # Display raw data section
                self.window.content_win.attron(curses.color_pair(4))  # Cyan for raw data
                self.window.content_win.addstr(y, 1, "=== Raw Data ===")
                self.window.content_win.attroff(curses.color_pair(4))
                y += 1
                raw_data = str(content)
                if len(raw_data) > width - 4:
                    raw_data = raw_data[:width-7] + "..."
                self.window.content_win.addstr(y, 2, raw_data)
                y += 2  # Add extra space after raw data

                # Then handle status messages
                if 'error' in content:
                    self.window.content_win.attron(curses.color_pair(1))  # Red for errors
                    self.window.content_win.addstr(y, 1, "ERROR:")
                    self.window.content_win.addstr(y + 1, 2, str(content['error']))
                    self.window.content_win.attroff(curses.color_pair(1))
                    y += 3
                elif 'status' in content and content['status'] in ['success', 'info']:
                    color = curses.color_pair(3) if content['status'] == 'success' else curses.color_pair(4)
                    self.window.content_win.attron(color)
                    self.window.content_win.addstr(y, 1, content['status'].upper() + ":")
                    self.window.content_win.addstr(y + 1, 2, content.get('message', 'Operation completed successfully'))
                    self.window.content_win.attroff(color)
                    y += 3

                # Finally display formatted data
                for key, value in content.items():
                    if key not in ['status', 'error', 'message']:
                        # Section header
                        self.window.content_win.attron(curses.color_pair(2))  # Yellow for headers
                        header = f"=== {key} ==="
                        self.window.content_win.addstr(y, 1, header)
                        self.window.content_win.attroff(curses.color_pair(2))
                        y += 1

                        if isinstance(value, list):
                            for item in value:
                                if y >= height - 1:
                                    break
                                if isinstance(item, dict):
                                    # Format dictionary items
                                    item_str = " | ".join(f"{k}: {v}" for k, v in item.items())
                                else:
                                    item_str = str(item)

                                if len(item_str) > width - 4:
                                    item_str = item_str[:width-7] + "..."

                                self.window.content_win.addstr(y, 2, item_str)
                                y += 1
                        else:
                            if y >= height - 1:
                                break
                            value_str = str(value)
                            if len(value_str) > width - 4:
                                value_str = value_str[:width-7] + "..."
                            self.window.content_win.addstr(y, 2, value_str)
                            y += 1
                        y += 1  # Space between sections

            elif content is None:
                self.window.content_win.attron(curses.color_pair(3))  # Green for success
                self.window.content_win.addstr(y, 1, "SUCCESS: Operation completed successfully")
                self.window.content_win.attroff(curses.color_pair(3))
                y += 2
            elif isinstance(content, list):
                self.window.content_win.attron(curses.color_pair(4))  # Cyan for lists
                self.window.content_win.addstr(y, 1, "=== Results ===")
                self.window.content_win.attroff(curses.color_pair(4))
                y += 1

                for item in content:
                    if y >= height - 1:
                        break
                    item_str = str(item)
                    if len(item_str) > width - 4:
                        item_str = item_str[:width-7] + "..."
                    self.window.content_win.addstr(y, 2, item_str)
                    y += 1
            else:
                # Handle string content
                content_str = str(content)
                if content_str.strip():
                    lines = content_str.split('\n')
                    for line in lines:
                        if y >= height - 1:
                            break
                        if len(line) > width - 2:
                            line = line[:width-5] + "..."
                        self.window.content_win.addstr(y, 1, line)
                        y += 1

            # Force window refresh
            self.window.refresh_all()

        except Exception as e:
            logger.error(f"Error displaying content: {str(e)}")
            try:
                self.window.content_win.erase()
                self.window.content_win.attron(curses.color_pair(1))
                self.window.content_win.addstr(1, 1, f"Error displaying content: {str(e)}")
                self.window.content_win.attroff(curses.color_pair(1))
                self.window.refresh_all()
            except:
                pass  # If we can't even display the error, we log it simply

    def run(self) -> None:
        """Run the application."""
        try:
            # Initialize colors
            curses.start_color()
            curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)     # For errors
            curses.init_pair(2, curses.COLOR_YELLOW, -1)                  # Headers
            curses.init_pair(3, curses.COLOR_GREEN, -1)                   # Success
            curses.init_pair(4, curses.COLOR_CYAN, -1)                    # Info

            # Configure terminal
            curses.curs_set(0)  # Hide cursor
            curses.halfdelay(1) # 100ms input timeout
            self.window.stdscr.nodelay(1)  # Non-blocking input

            # Initial draw
            self.window.draw_boxes()
            self.menu.draw()
            self.events.draw()
            self.window.refresh_all()

            # Connect to websocket
            try:
                self.socket.connect()
            except Exception as e:
                logger.error(f"Failed to connect to WebSocket: {str(e)}")
                self.display_content({"error": "Failed to connect to WebSocket server"})

            # Main loop
            last_update = time.time()
            update_interval = 0.1  # 100ms between updates

            while True:
                try:
                    current_time = time.time()

                    # Handle input
                    try:
                        key = self.window.stdscr.getch()
                    except curses.error:
                        key = -1

                    if key != -1:
                        if key == ord('q'):
                            break

                        # Handle menu navigation
                        if key in [curses.KEY_UP, curses.KEY_DOWN,
                                 curses.KEY_PPAGE, curses.KEY_NPAGE,
                                 curses.KEY_HOME, curses.KEY_END]:
                            self.menu.handle_input(key)
                            self.menu.draw()
                        elif key == ord('\n'):  # Enter key
                            selected_item = self.menu.get_selected_item()
                            if selected_item and selected_item.action:
                                try:
                                    result = selected_item.action()
                                    self.display_content(result)
                                except Exception as e:
                                    logger.error(f"Error executing action: {str(e)}")
                                    self.display_content({"error": f"Error executing action: {str(e)}"})
                        else:
                            # Try to handle shortcut keys
                            selected = self.menu.handle_input(key)
                            if selected and selected.action:
                                try:
                                    result = selected.action()
                                    self.display_content(result)
                                except Exception as e:
                                    logger.error(f"Error executing action: {str(e)}")
                                    self.display_content({"error": f"Error executing action: {str(e)}"})

                    # Update display periodically
                    if current_time - last_update >= update_interval:
                        self.events.draw()
                        self.window.refresh_all()
                        last_update = current_time

                except curses.error as e:
                    logger.error(f"Curses error in main loop: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Error in main loop: {str(e)}")
                    self.display_content({"error": f"Error in main loop: {str(e)}"})
                    time.sleep(1)  # Prevent error spam

        except KeyboardInterrupt:
            logger.info("Application terminated by user")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        self.socket.disconnect()

    # Menu action methods
    def get_playlists(self):
        """Get and display all playlists."""
        try:
            response = self.api.get_playlists()
            logger.info(f"Received response: {response}")  # Log for debug

            # If we have an error, display it
            if 'error' in response:
                return {"error": response['error']}

            # If we have data in the response
            if response.get('status') == 'success' and 'data' in response:
                playlists = response['data']
                if not playlists:
                    return {"message": "No playlists available", "status": "info"}

                # Format the playlists for display
                formatted_playlists = []
                for idx, mapping in enumerate(playlists, 1):
                    formatted_playlists.append({
                        "number": idx,
                        "id": mapping.get("id", "N/A"),
                        "title": mapping.get("title", "Untitled"),  # Title is now directly in the mapping
                        "tracks": len(mapping.get("tracks", [])),
                        "tag_uid": mapping.get("tag_uid", "N/A")
                    })

                # Create a readable display format
                return {
                    "Available Playlists": formatted_playlists,
                    "Total Count": len(playlists),
                    "Instructions": "Use 'Play Playlist' option and enter a number to select a playlist"
                }

            # If we have neither error nor valid data
            return {"error": "Unexpected response format from server"}

        except Exception as e:
            logger.error(f"Error getting playlists: {str(e)}")
            return {"error": f"Failed to get playlists: {str(e)}"}

    def play_playlist(self):
        """Prompt for playlist ID and play it."""
        try:
            # Get playlists first
            response = self.api.get_playlists()
            logger.info("Got playlists response")

            # Check for errors
            if 'error' in response:
                return {"error": response['error']}

            # Extract playlists from response
            playlists = response.get('data', []) if response.get('status') == 'success' else []
            if not playlists:
                return {"error": "No playlists available"}

            # Format playlists for display
            formatted_playlists = []
            for idx, mapping in enumerate(playlists, 1):
                formatted_playlists.append({
                    "number": idx,
                    "id": mapping.get("id"),
                    "title": mapping.get("title", "Untitled"),  # Title is now directly in the mapping
                    "tracks": len(mapping.get("tracks", [])),
                    "tag_uid": mapping.get("tag_uid", "N/A")
                })

            # Display the playlists with clear instructions
            self.display_content({
                "Available Playlists": formatted_playlists,
                "Instructions": [
                    "Please select a playlist by entering its number",
                    f"Valid numbers are 1 to {len(playlists)}",
                    "Press Enter after typing your selection"
                ],
                "status": "info"
            })

            # Force screen update
            self.window.refresh_all()
            curses.doupdate()

            # Switch to input mode
            self.window.stdscr.nodelay(0)  # Switch to blocking mode for input
            curses.echo()
            curses.curs_set(1)  # Show cursor

            try:
                # Clear the entire bottom line
                self.window.stdscr.move(self.window.height - 1, 0)
                self.window.stdscr.clrtoeol()
                self.window.stdscr.refresh()

                # Show prompt with available range
                prompt = f"Enter playlist number (1-{len(playlists)}): "
                self.window.stdscr.addstr(self.window.height - 1, 1, prompt)
                self.window.stdscr.refresh()

                # Get user input (will block until user enters something)
                user_input = self.window.stdscr.getstr().decode().strip()
                logger.info(f"Got user input: {user_input}")

                # Validate and process input
                if not user_input:
                    return {"error": "No input provided"}

                try:
                    idx = int(user_input) - 1
                    if 0 <= idx < len(playlists):
                        playlist_id = playlists[idx]["id"]
                        # Play the selected playlist
                        response = self.api.play_playlist(playlist_id)
                        if response.get('status') == 'success':
                            return {
                                "status": "success",
                                "message": f"Playing playlist: {formatted_playlists[idx]['title']}"
                            }
                        return response
                    else:
                        return {"error": f"Please enter a number between 1 and {len(playlists)}"}
                except ValueError:
                    return {"error": "Please enter a valid number"}

            finally:
                # Restore normal screen mode
                self.window.stdscr.nodelay(1)  # Restore non-blocking mode
                curses.noecho()
                curses.curs_set(0)  # Hide cursor
                # Clear the input line
                self.window.stdscr.move(self.window.height - 1, 0)
                self.window.stdscr.clrtoeol()
                self.window.stdscr.refresh()

        except Exception as e:
            logger.error(f"Error in play_playlist: {str(e)}")
            return {"error": f"Failed to play playlist: {str(e)}"}

    def pause_playback(self):
        """Pause current playback."""
        response = self.api.pause_playback()
        self.display_content(response)

    def resume_playback(self):
        """Resume playback."""
        response = self.api.resume_playback()
        self.display_content(response)

    def stop_playback(self):
        """Stop playback."""
        response = self.api.stop_playback()
        self.display_content(response)

    def next_track(self):
        """Skip to next track."""
        response = self.api.next_track()
        self.display_content(response)

    def previous_track(self):
        """Go to previous track."""
        response = self.api.previous_track()
        self.display_content(response)

    def get_volume(self):
        """Get current volume."""
        response = self.api.get_volume()
        self.display_content(response)

    def set_volume(self):
        """Set volume level with improved input handling."""
        try:
            curses.echo()
            curses.curs_set(1)  # Show cursor
            try:
                self.window.stdscr.addstr(self.window.height - 1, 1, "Volume (0-100): ")
                self.window.stdscr.refresh()
                user_input = self.window.stdscr.getstr().decode().strip()

                try:
                    volume = int(user_input)
                    if 0 <= volume <= 100:
                        response = self.api.set_volume(volume)
                        self.display_content(response)
                    else:
                        self.display_content({"error": "Volume must be between 0 and 100"})
                except ValueError:
                    self.display_content({"error": "Please enter a valid number"})
            finally:
                curses.noecho()
                curses.curs_set(0)  # Hide cursor
                # Clear the input line
                self.window.stdscr.move(self.window.height - 1, 0)
                self.window.stdscr.clrtoeol()
                self.window.stdscr.refresh()

        except Exception as e:
            logger.error(f"Error in set_volume: {str(e)}")
            self.display_content({"error": f"Failed to set volume: {str(e)}"})

    def get_system_info(self):
        """Get system information."""
        response = self.api.get_system_info()
        self.display_content(response)

    def quit(self):
        """Exit the application."""
        self.running = False