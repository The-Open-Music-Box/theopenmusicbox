"""Dependency providers for FastAPI DI (Depends pattern).

Provides config, container, audio, playback_subject, etc.
"""

from fastapi import Depends, Request

from app.src.config import config
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


def get_config():
    """Dependency provider for the global config singleton."""
    return config


def get_container(request: Request):
    """Get the container from the FastAPI app instance.

    This ensures we use the same container that was initialized in
    main.py.
    """
    container = getattr(request.app, "container", None)
    if not container:
        logger.log(
            LogLevel.ERROR,
            "Container not found on app instance. This is a critical error.",
        )
        raise RuntimeError(
            "Container not available. Application may not have initialized properly."
        )
    return container


def get_audio(container=Depends(get_container)):
    return container.audio


def get_playback_subject(container=Depends(get_container)):
    return container.playback_subject
