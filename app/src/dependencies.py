# back/app/src/dependencies.py

"""
Dependency providers for FastAPI DI (Depends pattern).
Provides config, container, audio, playback_subject, etc.
"""
from fastapi import Depends
from app.src.config import config_singleton
from app.src.core.container_async import ContainerAsync

# Singleton instance or factory as needed

_container_instance = None

def get_config():
    """Dependency provider for the global config singleton."""
    return config_singleton

def get_container(config=Depends(get_config)):
    global _container_instance
    if _container_instance is None:
        _container_instance = ContainerAsync(config)
    return _container_instance

def get_audio(container=Depends(get_container)):
    return container.audio

def get_playback_subject(container=Depends(get_container)):
    return container.playback_subject
