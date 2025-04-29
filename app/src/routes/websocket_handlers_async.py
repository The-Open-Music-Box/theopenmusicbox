import socketio
from fastapi import Request
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class WebSocketHandlersAsync:
    def __init__(self, sio: socketio.AsyncServer, app, nfc_service=None):
        self.sio = sio
        self.app = app
        self.nfc_service = nfc_service
        self._setup_progress_subscription()

    def _setup_progress_subscription(self):
        async def handle_track_progress(event):
            logger.log(LogLevel.INFO, f"Track progress event: {event.data}")
            await self.sio.emit('track_progress', event.data)
        # Subscribe to progress events
        if hasattr(self.app, 'container') and self.app.container.playback_subject:
            self.app.container.playback_subject.progress_stream.subscribe(
                lambda event: self.sio.start_background_task(handle_track_progress, event)
            )

    def register(self):
        @self.sio.event
        async def connect(sid, environ):
            logger.log(LogLevel.INFO, f"Client connected: {sid}")
            await self.sio.emit('connection_status', {'status': 'connected', 'sid': sid}, room=sid)
            playback_subject = getattr(self.app.container, 'playback_subject', None)
            if playback_subject:
                status_event = playback_subject.get_last_status_event()
                progress_event = playback_subject.get_last_progress_event()
                if status_event:
                    await self.sio.emit('playback_status', status_event.data, room=sid)
                if progress_event:
                    await self.sio.emit('track_progress', progress_event.data, room=sid)

        @self.sio.event
        async def disconnect(sid):
            logger.log(LogLevel.INFO, f"Client disconnected: {sid}")

        @self.sio.on('start_nfc_link')
        async def handle_start_nfc_link(sid, data):
            playlist_id = data.get('playlist_id') if data else None
            if not playlist_id:
                await self.sio.emit('nfc_error', {'message': 'playlist_id missing'}, room=sid)
                return
            try:
                if self.nfc_service.is_listening():
                    await self.sio.emit('nfc_error', {'message': 'NFC already listening'}, room=sid)
                    return
                self.nfc_service.start_listening(playlist_id)
                await self.sio.emit('nfc_status', {'status': 'waiting'}, room=sid)
                # Simulate NFC detection (replace with real callback in prod)
                import asyncio
                async def on_tag_detected():
                    await asyncio.sleep(2)
                    await self.sio.emit('nfc_linked', {'playlist_id': playlist_id}, room=sid)
                self.sio.start_background_task(on_tag_detected)
            except Exception as e:
                await self.sio.emit('nfc_error', {'message': str(e)}, room=sid)
