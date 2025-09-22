# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""NFC Association Domain Service."""

from typing import Optional, Dict, List, TYPE_CHECKING
from datetime import datetime, timezone

from ..entities.nfc_tag import NfcTag
from ..entities.association_session import AssociationSession, SessionState
from ..value_objects.tag_identifier import TagIdentifier
from ..protocols.nfc_hardware_protocol import NfcRepositoryProtocol
from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel

# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from app.src.domain.repositories.playlist_repository_interface import PlaylistRepositoryProtocol
from app.src.domain.decorators.error_handler import handle_domain_errors as handle_service_errors

logger = get_logger(__name__)


class NfcAssociationService:
    """Domain service for NFC tag association business logic.

    Handles the core business rules for associating NFC tags with playlists,
    managing association sessions, and enforcing business constraints.
    """

    def __init__(
        self,
        nfc_repository: NfcRepositoryProtocol,
        playlist_repository: Optional["PlaylistRepositoryProtocol"] = None,
    ):
        """Initialize the association service.

        Args:
            nfc_repository: Repository for NFC tag persistence
            playlist_repository: Repository for playlist sync (optional)
        """
        self._nfc_repository = nfc_repository
        self._playlist_repository = playlist_repository
        self._active_sessions: Dict[str, AssociationSession] = {}

    async def start_association_session(
        self, playlist_id: str, timeout_seconds: int = 60
    ) -> AssociationSession:
        """Start a new association session for a playlist.

        Args:
            playlist_id: ID of playlist to associate with tag
            timeout_seconds: Session timeout in seconds

        Returns:
            New association session

        Raises:
            ValueError: If playlist_id is invalid or session already exists
        """
        if not playlist_id:
            raise ValueError("Playlist ID is required")

        # Check if there's already an active session for this playlist
        existing_session = self._find_active_session_for_playlist(playlist_id)
        if existing_session:
            raise ValueError(f"Association session already active for playlist {playlist_id}")

        # Create new session
        session = AssociationSession(playlist_id=playlist_id, timeout_seconds=timeout_seconds)

        self._active_sessions[session.session_id] = session

        logger.log(
            LogLevel.INFO,
            f"✅ Started association session {session.session_id} for playlist {playlist_id}",
        )
        return session

    async def process_tag_detection(
        self, tag_identifier: TagIdentifier, session_id: Optional[str] = None
    ) -> Dict[str, any]:
        """Process a detected NFC tag.

        Args:
            tag_identifier: Detected tag identifier
            session_id: Optional specific session to process for

        Returns:
            Dictionary with processing result
        """
        # Find or create tag
        tag = await self._nfc_repository.find_by_identifier(tag_identifier)
        if not tag:
            tag = NfcTag(identifier=tag_identifier)

        tag.mark_detected()

        # If specific session provided, process only that session
        if session_id:
            session = self._active_sessions.get(session_id)
            if session and session.is_active():
                return await self._process_tag_for_session(tag, session)

        # Otherwise, process for all active sessions
        results = []
        for session in list(self._active_sessions.values()):
            if session.is_active():
                result = await self._process_tag_for_session(tag, session)
                results.append(result)

        # If no active sessions, just save the tag detection
        if not results:
            await self._nfc_repository.save_tag(tag)
            return {
                "action": "tag_detected",
                "tag_id": str(tag_identifier),
                "associated_playlist": tag.get_associated_playlist_id(),
                "no_active_sessions": True,
            }

        return results[0] if len(results) == 1 else {"multiple_sessions": results}

    async def _process_tag_for_session(
        self, tag: NfcTag, session: AssociationSession
    ) -> Dict[str, any]:
        """Process a tag detection for a specific session.

        Args:
            tag: Detected NFC tag
            session: Association session to process for

        Returns:
            Processing result dictionary
        """
        session.detect_tag(tag.identifier)

        # Check if tag is already associated with another playlist
        if tag.is_associated() and tag.get_associated_playlist_id() != session.playlist_id:
            session.mark_duplicate(tag.get_associated_playlist_id())
            logger.log(
                LogLevel.WARNING,
                f"🔄 Tag {tag.identifier} already associated with playlist {tag.get_associated_playlist_id()}",
            )

            return {
                "action": "duplicate_association",
                "session_id": session.session_id,
                "playlist_id": session.playlist_id,
                "tag_id": str(tag.identifier),
                "existing_playlist_id": tag.get_associated_playlist_id(),
                "session_state": session.state.value,
            }

        # Associate tag with playlist
        tag.associate_with_playlist(session.playlist_id)
        session.mark_successful()

        # Save the association in NFC repository
        await self._nfc_repository.save_tag(tag)

        # Synchronize with playlist repository for persistence
        if self._playlist_repository:
            sync_success = await self._playlist_repository.update_nfc_tag_association(
                session.playlist_id, str(tag.identifier)
            )
            if sync_success:
                logger.log(
                    LogLevel.INFO,
                    f"🔄 NFC-Playlist sync successful for tag {tag.identifier} -> playlist {session.playlist_id}",
                )
            else:
                logger.log(LogLevel.WARNING, f"⚠️ NFC-Playlist sync failed for tag {tag.identifier}")
        logger.log(
            LogLevel.INFO,
            f"✅ Successfully associated tag {tag.identifier} with playlist {session.playlist_id}",
        )

        # Remove successful session from active sessions after a short delay
        # This allows the UI to see the SUCCESS state briefly before cleanup
        import asyncio

        asyncio.create_task(self._cleanup_successful_session(session.session_id))

        return {
            "action": "association_success",
            "session_id": session.session_id,
            "playlist_id": session.playlist_id,
            "tag_id": str(tag.identifier),
            "session_state": session.state.value,
        }

    async def stop_association_session(self, session_id: str) -> bool:
        """Stop an association session.

        Args:
            session_id: ID of session to stop

        Returns:
            True if session was stopped, False if not found
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return False

        session.mark_stopped()
        logger.log(LogLevel.INFO, f"🛑 Stopped association session {session_id}")
        return True

    async def get_association_session(self, session_id: str) -> Optional[AssociationSession]:
        """Get an association session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Association session if found, None otherwise
        """
        return self._active_sessions.get(session_id)

    def get_active_sessions(self) -> List[AssociationSession]:
        """Get all active association sessions.

        Returns:
            List of active sessions
        """
        return [session for session in self._active_sessions.values() if session.is_active()]

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired association sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_count = 0
        expired_sessions = []

        for session_id, session in self._active_sessions.items():
            if session.is_expired() and session.state == SessionState.LISTENING:
                session.mark_timeout()
                expired_sessions.append(session_id)
                expired_count += 1

        for session_id in expired_sessions:
            logger.log(LogLevel.INFO, f"🕒 Association session {session_id} timed out")

        return expired_count

    def _find_active_session_for_playlist(self, playlist_id: str) -> Optional[AssociationSession]:
        """Find active session for a playlist.

        Args:
            playlist_id: Playlist ID to search for

        Returns:
            Active session if found, None otherwise
        """
        for session in self._active_sessions.values():
            if session.playlist_id == playlist_id and session.is_active():
                return session
        return None

    async def dissociate_tag(self, tag_identifier: TagIdentifier) -> bool:
        """Dissociate a tag from its playlist.

        Args:
            tag_identifier: Tag to dissociate

        Returns:
            True if dissociated, False if tag not found
        """
        tag = await self._nfc_repository.find_by_identifier(tag_identifier)
        if not tag:
            return False

        old_playlist_id = tag.get_associated_playlist_id()
        tag.dissociate_from_playlist()
        await self._nfc_repository.save_tag(tag)

        logger.log(
            LogLevel.INFO, f"✅ Dissociated tag {tag_identifier} from playlist {old_playlist_id}"
        )
        return True

    async def _cleanup_successful_session(self, session_id: str) -> None:
        """Clean up a successful association session after a short delay.

        Args:
            session_id: ID of session to clean up
        """
        import asyncio

        # Wait 2 seconds to allow UI to show success state
        await asyncio.sleep(2.0)

        session = self._active_sessions.get(session_id)
        if session and session.state == SessionState.SUCCESS:
            # Remove from active sessions
            del self._active_sessions[session_id]
            logger.log(LogLevel.INFO, f"🧹 Cleaned up successful association session {session_id}")
        elif session:
            logger.log(
                LogLevel.DEBUG, f"Session {session_id} not cleaned up - state: {session.state}"
            )
        else:
            logger.log(LogLevel.DEBUG, f"Session {session_id} not found for cleanup")
