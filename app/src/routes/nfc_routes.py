from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.src.services.nfc_service import NFCService
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services import PlaylistService
from app.src.dependencies import get_config

logger = ImprovedLogger(__name__)

def get_nfc_service(request: Request) -> NFCService:
    return request.app.container.nfc

class NFCRoutes:
    def __init__(self, app, nfc_service: NFCService):
        self.app = app
        self.nfc_service = nfc_service
        self.router = APIRouter(prefix="/api/nfc", tags=["nfc"])
        self._register_routes()

    def register(self):
        self.app.include_router(self.router)

    def _register_routes(self):
        @self.router.post("/associate/initiate")
        async def initiate_nfc_association(request: Request, nfc_service: NFCService = Depends(get_nfc_service)):
            """Initiate NFC association for a playlist (activate NFC reader)"""
            try:
                data = await request.json()
                playlist_id = data.get('playlist_id') if data else None
                if not playlist_id:
                    return JSONResponse({'error': 'playlist_id is required'}, status_code=400)
                started = nfc_service.start_association_mode(playlist_id)
                if not started:
                    return JSONResponse({'error': 'NFC association already in progress'}, status_code=409)
                return JSONResponse({'status': 'association_initiated', 'playlist_id': playlist_id}, status_code=200)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error initiating NFC association: {str(e)}")
                return JSONResponse({'error': str(e)}, status_code=500)

        @self.router.post("/associate/complete")
        async def complete_nfc_association(request: Request, nfc_service: NFCService = Depends(get_nfc_service)):
            """Complete association after tag scan (called by NFC service or frontend when tag is read)"""
            try:
                data = await request.json()
                playlist_id = data.get('playlist_id') if data else None
                tag_id = data.get('nfc_tag') if data else None
                if not playlist_id or not tag_id:
                    return JSONResponse({'error': 'playlist_id and nfc_tag are required'}, status_code=400)
                result = nfc_service.complete_association(playlist_id, tag_id)
                if result == 'already_associated':
                    return JSONResponse({'error': 'NFC tag already associated'}, status_code=409)
                if result == 'playlist_not_found':
                    return JSONResponse({'error': 'Playlist not found'}, status_code=404)
                if result == 'success':
                    return JSONResponse({'status': 'association_complete', 'playlist_id': playlist_id, 'nfc_tag': tag_id}, status_code=200)
                return JSONResponse({'error': 'Failed to associate tag'}, status_code=500)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error completing NFC association: {str(e)}")
                return JSONResponse({'error': str(e)}, status_code=500)

        @self.router.post("/disassociate")
        async def disassociate_nfc_tag(request: Request, nfc_service: NFCService = Depends(get_nfc_service)):
            """Disassociate an NFC tag from a playlist"""
            try:
                data = await request.json()
                playlist_id = data.get('playlist_id') if data else None
                tag_id = data.get('nfc_tag') if data else None
                if not playlist_id or not tag_id:
                    return JSONResponse({'error': 'playlist_id and nfc_tag are required'}, status_code=400)
                result = nfc_service.disassociate_tag(playlist_id, tag_id)
                if result == 'not_associated':
                    return JSONResponse({'error': 'Tag not associated with playlist'}, status_code=404)
                if result == 'success':
                    return JSONResponse({'status': 'disassociated', 'playlist_id': playlist_id, 'nfc_tag': tag_id}, status_code=200)
                return JSONResponse({'error': 'Failed to disassociate tag'}, status_code=500)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"NFC tag dissociation error: {str(e)}")
                return JSONResponse({'error': str(e)}, status_code=500)

        @self.router.get("/status")
        async def nfc_status(nfc_service: NFCService = Depends(get_nfc_service)):
            """Get current NFC association/listening status"""
            try:
                status = nfc_service.get_status()
                return JSONResponse(status, status_code=200)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error getting NFC status: {str(e)}")
                return JSONResponse({'error': str(e)}, status_code=500)

        # Route to start NFC listening
        @self.router.post("/listen/{playlist_id}")
        async def start_nfc_listening(playlist_id: str, config=Depends(get_config), nfc_service: NFCService = Depends(get_nfc_service)):
            """Start NFC listening for a given playlist"""
            try:
                if nfc_service.is_listening():
                    return JSONResponse({'status': 'error', 'message': 'An NFC listening session is already active'}, status_code=409)
                playlist_service = PlaylistService(config)
                playlist = playlist_service.get_playlist_by_id(playlist_id)
                if not playlist:
                    return JSONResponse({'status': 'error', 'message': 'Playlist not found'}, status_code=404)
                playlists = playlist_service.get_all_playlists()
                nfc_service.load_mapping(playlists)
                nfc_service.start_listening(playlist_id)
                return JSONResponse({'status': 'success', 'message': 'NFC listening started'}, status_code=200)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error starting NFC listening: {str(e)}")
                return JSONResponse({'status': 'error', 'message': 'Internal server error'}, status_code=500)

        # Route to stop NFC listening
        @self.router.post("/stop")
        async def stop_nfc_listening(nfc_service: NFCService = Depends(get_nfc_service)):
            """Stop current NFC listening"""
            try:
                nfc_service.stop_listening()
                return JSONResponse({'status': 'success', 'message': 'NFC listening stopped'}, status_code=200)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error stopping NFC listening: {str(e)}")
                return JSONResponse({'status': 'error', 'message': 'Internal server error'}, status_code=500)

        # Route to simulate tag detection (useful for testing)
        @self.router.post("/simulate_tag")
        async def simulate_tag_detection(request: Request, nfc_service: NFCService = Depends(get_nfc_service)):
            """Simulate NFC tag detection (for testing)"""
            try:
                data = await request.json()
                if not data or 'tag_id' not in data:
                    return JSONResponse({'status': 'error', 'message': 'tag_id missing'}, status_code=400)
                tag_id = data['tag_id']
                success = nfc_service.handle_tag_detected(tag_id)
                if success:
                    return JSONResponse({'status': 'success', 'message': f'Tag {tag_id} processed successfully'}, status_code=200)
                else:
                    return JSONResponse({'status': 'error', 'message': 'Tag not processed or already associated'}, status_code=409)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error simulating NFC detection: {str(e)}")
                return JSONResponse({'status': 'error', 'message': 'Internal server error'}, status_code=500)