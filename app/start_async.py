# app/start_async.py
"""
Script de démarrage pour la stack FastAPI/Socket.IO async.
Lit la configuration du port/host dans .env et démarre Uvicorn avec l'environnement virtuel venv.
"""
import os
from dotenv import load_dotenv
import uvicorn

if __name__ == "__main__":
    # Charger les variables d'environnement depuis .env
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    host = os.getenv("SOCKETIO_HOST", "127.0.0.1")
    port = int(os.getenv("SOCKETIO_PORT", 5000))

    # Lancer Uvicorn programmatique avec la bonne app
    uvicorn.run(
        "app.main_async:app_sio",
        host=host,
        port=port,
        reload=True,
        factory=False,
    )
