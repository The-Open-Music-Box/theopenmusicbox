# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Event bus protocol for dependency injection."""

from typing import Protocol, Callable, Any, Type, TypeVar, Optional
from abc import ABC

EventType = TypeVar("EventType")


class AudioEvent(ABC):
    """Base class for all audio events."""

    def __init__(self, source_component: str, timestamp: Optional[float] = None):
        self.source_component = source_component
        self.timestamp = timestamp or __import__("time").time()


class EventBusProtocol(Protocol):
    """Protocol defining the interface for event bus."""

    def subscribe(self, event_type: Type[EventType], handler: Callable[[EventType], Any]) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
        """
        ...

    def unsubscribe(self, event_type: Type[EventType], handler: Callable[[EventType], Any]) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        ...

    async def publish(self, event: EventType) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event instance to publish
        """
        ...

    def get_subscriber_count(self, event_type: Type[EventType]) -> int:
        """Get number of subscribers for an event type.

        Args:
            event_type: Event type to check

        Returns:
            int: Number of subscribers
        """
        ...
