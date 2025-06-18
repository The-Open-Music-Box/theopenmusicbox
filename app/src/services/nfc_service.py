"""
nfc_service.py

Service layer for NFC tag handling in TheMusicBox backend.
Provides business logic for NFC tag detection, association, event emission,
and integration with playlist management and playback.
"""

import asyncio
from typing import Any, Dict, List, Optional

from rx.subject import Subject
from socketio import AsyncServer

from app.src.helpers.error_handler import ErrorHandler
from app.src.module.nfc.nfc_handler import NFCHandler
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class NFCService:
    """
    Service for managing NFC tag operations, including detection,
    association with playlists, event emission to clients, and playback integration.
    """
    def __init__(
        self,
        socketio: Optional[AsyncServer] = None,
        nfc_handler: Optional[NFCHandler] = None,
    ):
        """Initialize the NFC service.

        Args:
            socketio: SocketIO instance for emitting events
            nfc_handler: Optional NFCHandler instance for NFC operations
        """
        self.socketio = socketio
        self.waiting_for_tag = False
        self.current_playlist_id: Optional[str] = None
        self._playlists: List[Dict[str, Any]] = []
        self._nfc_handler = nfc_handler
        self._association_mode = False
        self._sid = None  # Socket ID of the client requesting tag association
        self._scan_status_task = None
        self._last_tag_info = None
        self._allow_override = False
        self._playlist_controller = None  # Added attribute

        # Create a subject for playback events
        self._playback_subject = Subject()

        # Subscribe to tag events from the NFC handler
        if self._nfc_handler and hasattr(self._nfc_handler, "tag_subject"):
            self._nfc_handler.tag_subject.subscribe(self._on_tag_subject)

    def _on_tag_subject(self, tag_data):
        """
        Handle tag detection events from the NFC handler.

        Args:
            tag_data: Tag data received from the NFC handler.
        """
        try:
            # Handle tag absence event
            if isinstance(tag_data, dict) and tag_data.get("absence"):
                if self._playlist_controller:
                    self._playlist_controller.handle_tag_absence()
                return
            if isinstance(tag_data, dict) and "uid" in tag_data:
                tag_id = tag_data["uid"]
                # Launch the coroutine in the event loop with complete data
                asyncio.create_task(self.handle_tag_detected(tag_id, tag_data))
            else:
                # Fallback for the old method
                tag_id = tag_data
                asyncio.create_task(self.handle_tag_detected(tag_id))
        except Exception as e:
            ErrorHandler.log_error(e, "Error handling tag subject event")

    def load_mapping(self, mapping: List[Dict[str, Any]]) -> None:
        """
        Load the playlist mapping into the service.

        Args:
            mapping: List of playlist dictionaries.
        """
        self._playlists = mapping

    async def start_observe(self, playlist_id: Optional[str] = None) -> dict:
        """
        Start observation mode for NFC tag detection without a specific playlist.
        Used for the 'observe' route in the NFC API.

        Args:
            playlist_id: Optional ID of the playlist to associate with scanned tag.
        Returns:
            Dictionary with operation status.
        """
        try:
            # Start the hardware first
            if self._nfc_handler:
                await self._nfc_handler.start_nfc_reader()
                logger.log(
                    LogLevel.INFO, "NFC hardware reader started in observation mode"
                )

                # Set waiting status
                self.waiting_for_tag = True
                self.current_playlist_id = playlist_id

                if self.socketio:
                    await self.socketio.emit(
                        "nfc_status",
                        {
                            "type": "nfc_status",
                            "status": "observing",
                            "message": "Observing NFC tags...",
                        },
                    )

                return {"status": "ok"}
            else:
                logger.log(
                    LogLevel.ERROR, "NFC reader not available for observation mode"
                )
                return {"status": "error", "message": "NFC reader not available"}
        except Exception as e:
            ErrorHandler.log_error(e, "Error starting NFC observation")
            return {"status": "error", "message": str(e)}

    async def start_nfc_reader(self) -> None:
        """
        Start the NFC reader hardware (called by the routes).
        Delegates to start_listening with the current playlist ID.
        """
        try:
            if self._nfc_handler:
                await self._nfc_handler.start_nfc_reader()
                logger.log(LogLevel.INFO, "NFC hardware reader started")

                # If we have a current playlist ID, use it for listening
                if self.current_playlist_id:
                    await self.start_listening(self.current_playlist_id, self._sid)

                return {"status": "ok"}
            else:
                logger.log(LogLevel.ERROR, "NFC reader not available")
                return {"status": "error", "message": "NFC reader not available"}
        except Exception as e:
            ErrorHandler.log_error(e, "Error starting NFC reader")
            return {"status": "error", "message": str(e)}

    async def start_listening(
        self, playlist_id: str, sid: Optional[str] = None
    ) -> None:
        """
        Start listening for NFC tag association.

        Args:
            playlist_id: ID of the playlist to associate with scanned tag
            sid: Socket ID of the client requesting the tag association
        """
        # Store the playlist ID and socket ID
        self.current_playlist_id = playlist_id
        self._sid = sid

        # Set association mode
        self._association_mode = True
        self.waiting_for_tag = True

        # Start the NFC reader if not already started
        if self._nfc_handler and not self._nfc_handler.is_running():
            try:
                await self._nfc_handler.start_nfc_reader()
                logger.log(
                    LogLevel.INFO,
                    f"NFC hardware reader started for playlist {playlist_id}",
                )
            except Exception as e:
                ErrorHandler.log_error(e, "Error starting NFC reader for listening")
                if self.socketio and self._sid:
                    await self.socketio.emit(
                        "nfc_status",
                        {
                            "type": "nfc_status",
                            "status": "error",
                            "message": f"Error starting NFC reader: {str(e)}",
                        },
                        room=self._sid,
                    )
                return

        # Start sending periodic status updates
        await self._start_scan_status_updates()

        # Emit status to the client
        if self.socketio and self._sid:
            await self.socketio.emit(
                "nfc_status",
                {
                    "type": "nfc_status",
                    "status": "listening",
                    "message": "Listening for NFC tag...",
                    "playlist_id": playlist_id,
                },
                room=self._sid,
            )

        logger.log(
            LogLevel.INFO,
            f"Started listening for NFC tag association with playlist {playlist_id}",
        )

    async def stop_listening(self) -> None:
        """
        Stop listening for NFC tags.
        """
        # Stop scan status updates
        await self._stop_scan_status_updates()

        # Reset association mode
        self._association_mode = False
        self.waiting_for_tag = False

        # Emit status to the client
        status_update = {
            "type": "nfc_status",
            "status": "stopped",
            "message": "NFC tag listening stopped",
        }

        if self.socketio:
            if self._sid:
                await self.socketio.emit("nfc_status", status_update, room=self._sid)
            else:
                await self.socketio.emit("nfc_status", status_update)

        self._sid = None
        self._last_tag_info = None
        logger.log(LogLevel.INFO, "Stopped NFC listening")

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current NFC service status.

        Returns:
            A dictionary with the current NFC status information
        """
        status = {
            "hardware_available": self._nfc_handler is not None,
            "listening": self.waiting_for_tag,
            "current_playlist_id": self.current_playlist_id,
        }
        return status

    async def handle_tag_detected(
        self, tag_id: str, tag_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle detected NFC tag.

        Args:
            tag_id: Detected NFC tag ID
            tag_data: Complete tag data including timing and flag information

        Returns:
            True if tag was successfully processed
        """
        logger.log(LogLevel.INFO, f"Tag NFC detected: {tag_id}")

        # Save the last tag info for reference
        self._last_tag_info = {
            "tag_id": tag_id,
            "timestamp": asyncio.get_event_loop().time(),
        }

        # Log current mode for debugging
        logger.log(
            LogLevel.INFO,
            f"Handling tag in {'association' if self._association_mode else 'playback'} mode",
        )

        # If not in association mode, handle as playback tag
        if not self._association_mode:
            # Only propagate the event to the controller if we're not in association
            # mode
            return await self._handle_playback_tag(tag_id, tag_data)

        # From here on, we're in association mode
        # Emit an event to inform the client that a tag has been detected while in
        # association mode
        if self.socketio and self._sid:
            await self.socketio.emit(
                "nfc_tag_detected",
                {
                    "type": "nfc_tag_detected",
                    "status": "tag_detected",
                    "message": f"Tag detected: {tag_id}",
                    "timestamp": asyncio.get_event_loop().time(),
                    "tag_id": tag_id,
                    "playlist_id": self.current_playlist_id,
                },
                room=self._sid,
            )
            logger.log(
                LogLevel.INFO, f"Emitted nfc_tag_detected event to client {self._sid}"
            )

        # If not waiting for a tag, ignore
        if not self.waiting_for_tag:
            logger.log(
                LogLevel.WARNING, "Tag detected but not waiting for tag association"
            )
            return False

        # Process the tag association
        logger.log(LogLevel.INFO, f"Processing tag association for {tag_id}")
        association_result = await self.handle_tag_association(tag_id, tag_data)

        # If association was successful, also emit the nfc_status event that the frontend expects
        if (
            association_result.get("status") == "success"
            and self.socketio
            and self._sid
        ):
            # Find current playlist in the mapping
            current_playlist = next(
                (p for p in self._playlists if p["id"] == self.current_playlist_id),
                None,
            )

            if current_playlist:
                status_update = {
                    "type": "nfc_status",
                    "status": "success",
                    "message": f'Tag {tag_id} successfully associated with playlist "{current_playlist.get("title", "Unknown")}"',
                    "tag_id": tag_id,
                    "playlist_id": self.current_playlist_id,
                    "playlist_title": current_playlist.get("title", "Unknown"),
                }

                await self.socketio.emit("nfc_status", status_update, room=self._sid)
                logger.log(
                    LogLevel.INFO, f"Emitted 'success' status to client {self._sid}"
                )

                # Reset association mode flags
                self.waiting_for_tag = False
                self._association_mode = False

                # Stop scan status updates
                await self._stop_scan_status_updates()

        return association_result.get("status") == "success"

        # Association mode logic - check if tag is already associated with any playlist
        associated_playlist = None
        for item in self._playlists:
            if item.get("nfc_tag") == tag_id:
                associated_playlist = item
                break

        # If the tag is already associated with another playlist
        if (
            associated_playlist
            and associated_playlist["id"] != self.current_playlist_id
        ):
            status_update = {
                "type": "nfc_status",
                "status": "already_associated",
                "message": f'Tag already associated with playlist "{associated_playlist.get("title", "Unknown")}"',
                "tag_id": tag_id,
                "current_playlist_id": self.current_playlist_id,
                "associated_playlist_id": associated_playlist["id"],
                "associated_playlist_title": associated_playlist.get(
                    "title", "Unknown"
                ),
            }

            if self.socketio and self._sid:
                await self.socketio.emit(
                    "nfc_status", status_update, room=self._sid
                )
                logger.log(
                    LogLevel.INFO,
                    f"Emitted 'already_associated' status to client {self._sid}",
                )

            logger.log(
                LogLevel.WARNING,
                f"Tag {tag_id} already associated with playlist {associated_playlist['id']}",
            )
            return False

        # If tag is free or we're overriding, associate it with the current playlist
        if self.current_playlist_id and (
            self._allow_override or not associated_playlist
        ):
            # Find current playlist in the mapping
            current_playlist = next(
                (p for p in self._playlists if p["id"] == self.current_playlist_id),
                None,
            )
            if current_playlist:
                # If we're overriding a previous association, clear it
                if associated_playlist and self._allow_override:
                    old_playlist_title = associated_playlist.get("title", "Unknown")
                    associated_playlist["nfc_tag"] = None
                    logger.log(
                        LogLevel.INFO,
                        f"Removed tag {tag_id} from playlist {old_playlist_title}",
                    )

                # Set the tag on the current playlist in memory
                current_playlist["nfc_tag"] = tag_id

                # Get access to a playlist service instance to persist the association
                try:
                    # Create a new instance of the playlist service
                    from app.src.services.playlist_service import PlaylistService

                    playlist_service = PlaylistService()

                    # Persist the association to the database
                    if playlist_service:
                        result = playlist_service.associate_nfc_tag(
                            self.current_playlist_id, tag_id
                        )
                        if result:
                            logger.log(
                                LogLevel.INFO,
                                f"Tag {tag_id} successfully persisted to database for playlist {self.current_playlist_id}",
                            )
                        else:
                            logger.log(
                                LogLevel.ERROR,
                                f"Failed to persist tag {tag_id} association in database",
                            )
                    else:
                        logger.log(
                            LogLevel.ERROR,
                            "Could not access playlist service to persist NFC tag association",
                        )
                except Exception as e:
                    ErrorHandler.log_error(e, "Error persisting NFC tag association")

                status_update = {
                    "type": "nfc_status",
                    "status": "success",
                    "message": f'Tag {tag_id} successfully associated with playlist "{current_playlist.get("title", "Unknown")}"',
                    "tag_id": tag_id,
                    "playlist_id": self.current_playlist_id,
                    "playlist_title": current_playlist.get("title", "Unknown"),
                }

                if self.socketio and self._sid:
                    await self.socketio.emit(
                        "nfc_status", status_update, room=self._sid
                    )
                    logger.log(
                        LogLevel.INFO, f"Emitted 'success' status to client {self._sid}"
                    )

                logger.log(
                    LogLevel.INFO,
                    f"Tag {tag_id} associated with playlist {self.current_playlist_id}",
                )

                # After successful association, we should reset the association mode
                # to allow immediate playback if the same tag is scanned again
                self.waiting_for_tag = False
                self._association_mode = False

                # Note: We're keeping self.current_playlist_id and self._sid
                # to allow proper UI updates to finish

                # Stop scan status updates
                await self._stop_scan_status_updates()

                logger.log(
                    LogLevel.INFO, "Association successful, returning to playback mode"
                )

                # Store the tag ID before switching modes, so we can force re-detection
                detected_tag_id = tag_id

                # Force re-detection of the tag if it's still present on the reader
                # This will trigger a new tag detection event which will start playback
                if self._nfc_handler and hasattr(
                    self._nfc_handler, "tag_detection_manager"
                ):
                    try:
                        # Small delay to ensure mode transition is complete
                        await asyncio.sleep(0.3)

                        # Force re-detection of the tag that was just associated
                        logger.log(
                            LogLevel.INFO,
                            f"Forcing re-detection of tag {detected_tag_id} after association",
                        )
                        self._nfc_handler.tag_detection_manager.force_redetect(
                            detected_tag_id
                        )
                    except Exception as e:
                        ErrorHandler.log_error(
                            e, "Error forcing tag re-detection after association"
                        )

                return True

        return False

    def is_listening(self) -> bool:
        """
        Check if service is currently listening for NFC tags.

        Returns:
            True if in listening mode.
        """
        return self.waiting_for_tag

    def is_in_association_mode(self) -> bool:
        """
        Check if the service is in tag association mode.

        Returns:
            True if in association mode, False otherwise.
        """
        return self._association_mode

    async def set_override_mode(self, allow_override: bool = True) -> None:
        """
        Set whether to allow overriding existing tag associations.

        Args:
            allow_override: Whether to allow overriding existing associations
        """
        self._allow_override = allow_override
        logger.log(LogLevel.INFO, f"Override mode set to: {allow_override}")

        if self._last_tag_info and self.waiting_for_tag:
            # Re-process the last detected tag with the new override setting
            asyncio.create_task(self.handle_tag_detected(self._last_tag_info["tag_id"]))

    async def _handle_playback_tag(
        self, tag_id: str, tag_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Handle a tag detected in playback mode (not association mode).

        Args:
            tag_id: Detected NFC tag ID
            tag_data: Complete tag data including timing and flag information

        Returns:
            True if tag was successfully processed for playback
        """
        # Double-check we're actually in playback mode
        if self._association_mode:
            logger.log(
                LogLevel.WARNING,
                "Association mode detected in _handle_playback_tag - this should not happen",
            )
            return False

        # Emit the event to the playback subject
        try:
            logger.log(
                LogLevel.INFO,
                f"Playback mode: Emitting tag {tag_id} to playback subject",
            )
            self._playback_subject.on_next((tag_id, tag_data))
            return True
        except Exception as e:
            ErrorHandler.log_error(e, "Error emitting tag to playback subject")
            return False

    async def _start_scan_status_updates(self) -> None:
        """
        Start sending periodic scan status updates to connected clients.
        """
        if self._scan_status_task and not self._scan_status_task.done():
            return

        async def send_scanning_updates():
            try:
                while self.waiting_for_tag and self._association_mode:
                    if self.socketio and self._sid:
                        status_update = {
                            "type": "nfc_scanning",
                            "status": "scanning",
                            "message": "Scanning for NFC tag...",
                            "playlist_id": self.current_playlist_id,
                            "timestamp": asyncio.get_event_loop().time(),
                            "mode": "association",  # Explicitly state we're in association mode
                        }

                        # Add last tag info if available
                        if self._last_tag_info:
                            status_update["last_tag_id"] = self._last_tag_info["tag_id"]
                            status_update["last_tag_timestamp"] = self._last_tag_info[
                                "timestamp"
                            ]

                        await self.socketio.emit(
                            "nfc_scanning", status_update, room=self._sid
                        )
                    await asyncio.sleep(1.0)  # Send updates every second
            except Exception as e:
                ErrorHandler.log_error(e, "Error in scan status updates")

        self._scan_status_task = asyncio.create_task(send_scanning_updates())
        logger.log(LogLevel.INFO, "Started sending periodic scanning status updates")

    async def _stop_scan_status_updates(self) -> None:
        """
        Stop sending scan status updates.
        """
        if self._scan_status_task and not self._scan_status_task.done():
            self._scan_status_task.cancel()
            try:
                await self._scan_status_task
            except asyncio.CancelledError:
                pass
            self._scan_status_task = None

    @property
    def tag_subject(self):
        """
        Expose the tag_subject from the underlying NFCHandler.

        Returns:
            The tag_subject from the NFCHandler, or None if no handler is available.
        """
        if self._nfc_handler and hasattr(self._nfc_handler, "tag_subject"):
            return self._nfc_handler.tag_subject
        return None

    @property
    def playback_subject(self) -> Subject:
        """
        Get the playback subject for subscribing to playback tag events.

        Returns:
            The playback Subject instance
        """
        return self._playback_subject

    def set_playlist_controller(self, playlist_controller):
        """
        Set the playlist controller for this NFC service.

        Args:
            playlist_controller: The playlist controller instance.
        """
        self._playlist_controller = playlist_controller

    async def handle_tag_association(
        self, tag_id: str, tag_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a tag detected in association mode.

        Args:
            tag_id: Detected NFC tag ID
            tag_data: Optional tag data

        Returns:
            Dictionary with operation status
        """
        if not self._association_mode or not self.current_playlist_id:
            logger.log(
                LogLevel.WARNING,
                "Tag association attempted but not in association mode",
            )
            return {"status": "error", "message": "Not in association mode"}

        # Record the tag info for status updates
        self._last_tag_info = {
            "tag_id": tag_id,
            "timestamp": asyncio.get_event_loop().time(),
        }

        # Check if this tag is already associated with a playlist
        existing_playlist = None
        for playlist in self._playlists:
            if playlist.get("nfc_tag") == tag_id:
                existing_playlist = playlist
                break

        # If tag is already associated and we don't allow override
        if existing_playlist and not self._allow_override:
            logger.log(
                LogLevel.WARNING,
                f"Tag {tag_id} already associated with playlist {existing_playlist.get('id')}",
            )

            if self.socketio and self._sid:
                await self.socketio.emit(
                    "nfc_association_result",
                    {
                        "status": "error",
                        "message": f"Tag already associated with playlist '{existing_playlist.get('title', 'Unknown')}'.",
                        "tag_id": tag_id,
                        "playlist_id": existing_playlist.get("id"),
                    },
                    room=self._sid,
                )

            return {
                "status": "error",
                "message": "Tag already associated",
                "tag_id": tag_id,
                "playlist_id": existing_playlist.get("id"),
            }

        # Associate the tag with the playlist
        try:
            # Use the playlist service directly to associate the tag
            from app.src.services.playlist_service import PlaylistService

            playlist_service = PlaylistService()
            success = playlist_service.associate_nfc_tag(
                self.current_playlist_id, tag_id
            )

            if success:
                # Update the in-memory playlist mapping
                for playlist in self._playlists:
                    if playlist.get("id") == self.current_playlist_id:
                        playlist["nfc_tag"] = tag_id
                        break

                # Send success response
                result = {
                    "status": "success",
                    "message": f"Tag successfully associated with playlist",
                    "tag_id": tag_id,
                    "playlist_id": self.current_playlist_id,
                }

                if self.socketio and self._sid:
                    await self.socketio.emit(
                        "nfc_association_result",
                        {
                            "status": "success",
                            "message": f"Tag successfully associated with playlist.",
                            "tag_id": tag_id,
                            "playlist_id": self.current_playlist_id,
                        },
                        room=self._sid,
                    )

                return result
            else:
                # Send error response
                error_result = {
                    "status": "error",
                    "message": "Failed to associate tag with playlist",
                    "tag_id": tag_id,
                    "playlist_id": self.current_playlist_id,
                }

                if self.socketio and self._sid:
                    await self.socketio.emit(
                        "nfc_association_result",
                        {
                            "status": "error",
                            "message": "Failed to associate tag with playlist.",
                            "tag_id": tag_id,
                            "playlist_id": self.current_playlist_id,
                        },
                        room=self._sid,
                    )

                return error_result
        except Exception as e:
            # Log and return error
            ErrorHandler.log_error(e, "Error associating tag with playlist")

            error_result = {
                "status": "error",
                "message": f"Error: {str(e)}",
                "tag_id": tag_id,
                "playlist_id": self.current_playlist_id,
            }

            if self.socketio and self._sid:
                await self.socketio.emit(
                    "nfc_association_result",
                    {
                        "status": "error",
                        "message": f"Error: {str(e)}",
                        "tag_id": tag_id,
                        "playlist_id": self.current_playlist_id,
                    },
                    room=self._sid,
                )

            return error_result
