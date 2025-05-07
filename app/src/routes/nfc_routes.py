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
    def __init__(self, app, socketio, nfc_service: NFCService):
        self.app = app
        self.socketio = socketio
        self.nfc_service = nfc_service
        self.router = APIRouter(prefix="/api/nfc", tags=["nfc"])
        self._register_routes()

    def register(self):
        self.app.include_router(self.router)

    def _register_routes(self):
        @self.router.post("/observe")
        async def observe_nfc(request: Request, config=Depends(get_config), nfc_service: NFCService = Depends(get_nfc_service)):
            try:
                # We depend on the NFC service to be initialized with a handler
                if not nfc_service or not hasattr(nfc_service, "_nfc_handler") or not nfc_service._nfc_handler:
                    logger.log(LogLevel.WARNING, "NFC reader not available")
                    return JSONResponse(status_code=503, content={"error": "NFC reader not available"})
                
                # Utiliser la méthode start_observe du service NFC
                # Elle initialisera le lecteur NFC et mettra le service en mode observation
                result = await nfc_service.start_observe(playlist_id=None)
                
                if result.get("status") == "ok":
                    logger.log(LogLevel.INFO, "NFC hardware reader started in observation mode")
                    return {"status": "ok"}
                else:
                    logger.log(LogLevel.ERROR, f"Failed to start NFC observation: {result.get('message', 'Unknown error')}")
                    return JSONResponse(status_code=500, content={"error": result.get('message', 'Unknown error')})
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Failed to start NFC observation: {e}")
                return JSONResponse(status_code=500, content={"error": f"Failed to start NFC observation: {str(e)}"})


        @self.router.post("/link")
        async def link_nfc_tag(request: Request, config=Depends(get_config), nfc_service: NFCService = Depends(get_nfc_service)):
            """Associate an NFC tag to a playlist (with override option)"""
            try:
                data = await request.json()
                playlist_id = data.get('playlist_id')
                tag_id = data.get('tag_id')
                override = data.get('override', False)
                if not playlist_id or not tag_id:
                    return JSONResponse({'error': 'playlist_id and tag_id are required'}, status_code=400)
                playlist_service = PlaylistService(config)
                # Vérifie si le tag est déjà associé à une playlist
                existing_playlist = playlist_service.get_playlist_by_nfc_tag(tag_id)
                if existing_playlist:
                    if existing_playlist['id'] == playlist_id:
                        await self.socketio.emit('nfc_link_success', {'playlist_id': playlist_id, 'tag_id': tag_id})
                        return JSONResponse({'status': 'already_linked', 'playlist_id': playlist_id, 'tag_id': tag_id}, status_code=200)
                    if not override:
                        await self.socketio.emit('nfc_tag_already_linked', {
                            'tag_id': tag_id,
                            'playlist_id': existing_playlist['id'],
                            'playlist_title': existing_playlist.get('title', '')
                        })
                        return JSONResponse({'error': 'Tag already associated', 'playlist_id': existing_playlist['id'], 'playlist_title': existing_playlist.get('title', '')}, status_code=409)
                    # Override demandé : désassocier puis associer atomiquement
                    playlist_service.disassociate_nfc_tag(existing_playlist['id'])
                # Associe le tag à la nouvelle playlist
                success = playlist_service.associate_nfc_tag(playlist_id, tag_id)
                if success:
                    await self.socketio.emit('nfc_link_success', {'playlist_id': playlist_id, 'tag_id': tag_id})
                    return JSONResponse({'status': 'association_complete', 'playlist_id': playlist_id, 'tag_id': tag_id}, status_code=200)
                else:
                    await self.socketio.emit('nfc_link_error', {'error': 'Failed to associate tag'})
                    return JSONResponse({'error': 'Failed to associate tag'}, status_code=500)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error associating NFC tag: {str(e)}")
                await self.socketio.emit('nfc_link_error', {'error': str(e)})
                return JSONResponse({'error': str(e)}, status_code=500)

        @self.router.post("/cancel")
        async def cancel_nfc_observation(request: Request, nfc_service: NFCService = Depends(get_nfc_service)):
            """Cancel NFC observation (by user or timeout)"""
            try:
                # Utiliser la méthode asynchrone stop_listening
                await nfc_service.stop_listening()
                await self.socketio.emit('nfc_cancelled', {})
                return JSONResponse({'status': 'cancelled'}, status_code=200)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error cancelling NFC observation: {str(e)}")
                await self.socketio.emit('nfc_link_error', {'error': str(e)})
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
                # Utiliser la méthode asynchrone start_nfc_reader
                await nfc_service.start_nfc_reader()
                return JSONResponse({'status': 'success', 'message': 'NFC listening started'}, status_code=200)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error starting NFC listening: {str(e)}")
                return JSONResponse({'status': 'error', 'message': 'Internal server error'}, status_code=500)

        # Route to stop NFC listening
        @self.router.post("/stop")
        async def stop_nfc_listening(nfc_service: NFCService = Depends(get_nfc_service)):
            """Stop current NFC listening"""
            try:
                # Utiliser la méthode asynchrone stop_listening
                await nfc_service.stop_listening()
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
                # Utiliser la méthode asynchrone handle_tag_detected
                success = await nfc_service.handle_tag_detected(tag_id)
                if success:
                    return JSONResponse({'status': 'success', 'message': f'Tag {tag_id} processed successfully'}, status_code=200)
                else:
                    return JSONResponse({'status': 'error', 'message': 'Tag not processed or already associated'}, status_code=409)
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error simulating NFC detection: {str(e)}")
                return JSONResponse({'status': 'error', 'message': 'Internal server error'}, status_code=500)