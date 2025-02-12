# app/src/services/notification_service.py

from typing import Dict, Any
import eventlet

class DownloadNotifier:
    def __init__(self, socketio, download_id: str):
        self.socketio = socketio
        self.download_id = download_id

    def notify(self, status: str, **data):
        self.socketio.emit('download_progress', {
            'download_id': self.download_id,
            'status': status,
            **data
        })
        eventlet.sleep(0)