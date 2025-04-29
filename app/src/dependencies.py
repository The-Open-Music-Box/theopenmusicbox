# app/src/dependencies.py
"""
Dependency providers for FastAPI DI (Depends pattern).
Provides config, container, audio, playback_subject, etc.
"""
from fastapi import Depends
from app.src.config import Config
from app.src.core.container_async import ContainerAsync

# Singleton instance or factory as needed
_config_instance = None
_container_instance = None

def get_config():
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def get_container(config=Depends(get_config)):
    global _container_instance
    if _container_instance is None:
        _container_instance = ContainerAsync(config)
    return _container_instance

def get_audio(container=Depends(get_container)):
    return container.audio

def get_playback_subject(container=Depends(get_container)):
    return container.playback_subject
