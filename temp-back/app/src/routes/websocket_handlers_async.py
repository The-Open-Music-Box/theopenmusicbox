# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

import socketio

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.notification_service import PlaybackSubject

logger = ImprovedLogger(__name__)


class WebSocketHandlersAsync:
    """Registers and manages asynchronous WebSocket event handlers for TheOpenMusicBox backend.

    This class sets up all Socket.IO event handlers for playback status, playlist control,
    NFC association, and client connection management. It provides dependency injection for
    NFC services and ensures event routing for all real-time features.
    """
    def __init__(self, sio: socketio.AsyncServer, app, nfc_service=None):
        self.sio = sio
        self.app = app
        self.nfc_service = nfc_service

        # Fournir l'instance de socketio au PlaybackSubject pour la communication directe
        # C'est la seule chose nécessaire maintenant - les événements seront
        # envoyés directement
        PlaybackSubject.set_socketio(self.sio)
        logger.log(
            LogLevel.INFO,
            "[WebSocketHandlersAsync] SocketIO instance provided to PlaybackSubject",
        )

    def register(self):
        """Register all asynchronous Socket.IO event handlers for this backend."""
        @self.sio.event
        async def connect(sid, environ):
            logger.log(LogLevel.INFO, f"Client connected: {sid}")
            await self.sio.emit(
                "connection_status", {"status": "connected", "sid": sid}, room=sid
            )

            # Utiliser le singleton PlaybackSubject
            playback_subject = PlaybackSubject.get_instance()
            logger.log(
                LogLevel.INFO,
                f"[SOCKET.IO] Connect: using PlaybackSubject singleton (id: {id(playback_subject)})",
            )

            try:
                # Récupérer et envoyer les derniers événements au client qui vient de se
                # connecter
                status_event = playback_subject.get_last_status_event()
                progress_event = playback_subject.get_last_progress_event()

                if status_event:
                    logger.log(
                        LogLevel.INFO,
                        f"[SOCKET.IO] Sending last status to new client: {status_event.data['status']}",
                    )
                    # Utiliser await avec les méthodes asynchrones pour s'assurer
                    # qu'elles sont exécutées
                    await self.sio.emit("playback_status", status_event.data, room=sid)

                if progress_event:
                    current_time = progress_event.data.get("current_time", 0)
                    duration = progress_event.data.get("duration", 0)
                    logger.log(
                        LogLevel.INFO,
                        f"[SOCKET.IO] Sending last progress to new client: {current_time:.1f}/{duration:.1f}",
                    )
                    # Utiliser await avec les méthodes asynchrones pour s'assurer
                    # qu'elles sont exécutées
                    await self.sio.emit("track_progress", progress_event.data, room=sid)

                # Log de confirmation que les événements ont bien été envoyés
                logger.log(
                    LogLevel.INFO, f"[SOCKET.IO] Initial events sent to client {sid}"
                )
            except Exception as e:
                logger.log(
                    LogLevel.ERROR,
                    f"[SOCKET.IO] Error sending last events to client: {e}",
                )

        @self.sio.event
        async def disconnect(sid):
            logger.log(LogLevel.INFO, f"Client disconnected: {sid}")
            # If the disconnecting client was in association mode, stop NFC listening
            if self.nfc_service and self.nfc_service.is_listening():
                # Only stop if the association was started by this sid
                if getattr(self.nfc_service, "_sid", None) == sid:
                    logger.log(
                        LogLevel.INFO,
                        f"[SOCKET.IO] Stopping NFC association mode for disconnected client: {sid}",
                    )
                    await self.nfc_service.stop_listening()

        @self.sio.on("set_playlist")
        async def handle_set_playlist(sid, data):
            try:
                logger.log(LogLevel.INFO, f"[SOCKET.IO] set_playlist received: {data}")
                # Reconstruire la playlist mock à partir des données reçues
                from app.src.model.playlist import Playlist
                from app.src.model.track import Track

                playlist = Playlist(
                    id=data.get("id"),
                    name=data.get("name"),
                    tracks=[
                        Track(
                            number=track.get("number"),
                            title=track.get("title"),
                            filename=track.get("filename"),
                            path=track.get("filename"),
                            duration=track.get("duration"),
                        )
                        for track in data.get("tracks", [])
                    ],
                )
                # Affecter la playlist au player du container
                player = getattr(self.app.container, "audio", None)
                if player:
                    player.set_playlist(playlist)
                    await self.sio.emit(
                        "playlist_set",
                        {"status": "ok", "playlist_id": playlist.id},
                        room=sid,
                    )
                    logger.log(
                        LogLevel.INFO,
                        f"[SOCKET.IO] Playlist set for player: {playlist}",
                    )
                else:
                    await self.sio.emit(
                        "playlist_set",
                        {"status": "error", "message": "No audio player found"},
                        room=sid,
                    )
            except Exception as e:
                logger.log(
                    LogLevel.ERROR, f"[SOCKET.IO] Error in set_playlist: {str(e)}"
                )
                await self.sio.emit(
                    "playlist_set", {"status": "error", "message": str(e)}, room=sid
                )

        @self.sio.on("play_track")
        async def handle_play_track(sid, data):
            try:
                playlist_id = data.get("playlist_id")
                track_number = data.get("track_number")
                logger.log(
                    LogLevel.INFO,
                    f"[SOCKET.IO] play_track received: playlist_id={playlist_id}, track_number={track_number}",
                )
                player = getattr(self.app.container, "audio", None)
                if player and hasattr(player, "play_track"):
                    player.play_track(track_number)
                    await self.sio.emit(
                        "track_played",
                        {"status": "ok", "track_number": track_number},
                        room=sid,
                    )
                    logger.log(
                        LogLevel.INFO,
                        f"[SOCKET.IO] Started playback for track {track_number}",
                    )
                else:
                    await self.sio.emit(
                        "track_played",
                        {
                            "status": "error",
                            "message": "No audio player or play_track method",
                        },
                        room=sid,
                    )
            except Exception as e:
                logger.log(LogLevel.ERROR, f"[SOCKET.IO] Error in play_track: {str(e)}")
                await self.sio.emit(
                    "track_played", {"status": "error", "message": str(e)}, room=sid
                )

        @self.sio.on("start_nfc_link")
        async def handle_start_nfc_link(sid, data):
            playlist_id = data.get("playlist_id") if data else None
            if not playlist_id:
                await self.sio.emit(
                    "nfc_error",
                    {"type": "error", "message": "playlist_id missing"},
                    room=sid,
                )
                return

            logger.log(
                LogLevel.INFO,
                f"[SOCKET.IO] start_nfc_link received for playlist: {playlist_id}",
            )

            try:
                if self.nfc_service.is_listening():
                    await self.sio.emit(
                        "nfc_error",
                        {
                            "type": "error",
                            "message": "NFC already in association mode for another request",
                        },
                        room=sid,
                    )
                    return

                # Start the association process
                await self.nfc_service.start_listening(playlist_id, sid)
                logger.log(
                    LogLevel.INFO,
                    f"[SOCKET.IO] NFC association mode started for playlist: {playlist_id}",
                )

                # No need to send status here, the NFC service will emit appropriate
                # events

            except Exception as e:
                logger.log(
                    LogLevel.ERROR, f"[SOCKET.IO] Error in start_nfc_link: {str(e)}"
                )
                await self.sio.emit(
                    "nfc_error", {"type": "error", "message": str(e)}, room=sid
                )

        @self.sio.on("stop_nfc_link")
        async def handle_stop_nfc_link(sid, data):
            logger.log(
                LogLevel.INFO, f"[SOCKET.IO] stop_nfc_link received from client: {sid}"
            )

            try:
                if not self.nfc_service.is_listening():
                    await self.sio.emit(
                        "nfc_status",
                        {
                            "type": "nfc_status",
                            "status": "not_listening",
                            "message": "No active NFC association to stop",
                        },
                        room=sid,
                    )
                    return

                # Stop the association process
                await self.nfc_service.stop_listening()
                logger.log(
                    LogLevel.INFO,
                    f"[SOCKET.IO] NFC association stopped by client: {sid}",
                )

            except Exception as e:
                logger.log(
                    LogLevel.ERROR, f"[SOCKET.IO] Error in stop_nfc_link: {str(e)}"
                )
                await self.sio.emit(
                    "nfc_error", {"type": "error", "message": str(e)}, room=sid
                )

        @self.sio.on("override_nfc_tag")
        async def handle_override_tag(sid):
            logger.log(
                LogLevel.INFO,
                f"[SOCKET.IO] override_nfc_tag received from client: {sid}",
            )
            try:
                if not self.nfc_service or not self.nfc_service.is_listening():
                    await self.sio.emit(
                        "nfc_error",
                        {"type": "error", "message": "Not in NFC association mode"},
                        room=sid,
                    )
                    return

                # Enable override mode for the NFC association
                await self.nfc_service.set_override_mode(True)
                logger.log(
                    LogLevel.INFO,
                    f"[SOCKET.IO] Override mode enabled for client: {sid}",
                )

                # Optionally, you may want to re-process the last detected tag if needed
                # If you want to force immediate re-association, trigger it here
                # Example (pseudo):
                # if self.nfc_service._last_tag_info:
                #     await self.nfc_service.handle_tag_association(self.nfc_service._last_tag_info['uid'], self.nfc_service._last_tag_info)
                # The NFC service should emit appropriate status updates as it processes
                # the override

            except Exception as e:
                logger.log(
                    LogLevel.ERROR, f"[SOCKET.IO] Error in override_nfc_tag: {str(e)}"
                )
                await self.sio.emit(
                    "nfc_error", {"type": "error", "message": str(e)}, room=sid
                )
