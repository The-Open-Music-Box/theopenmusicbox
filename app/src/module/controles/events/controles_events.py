"""Controls Events Module.

Defines event types and event objects for the controls system. These
events are emitted by physical control devices and propagated through
the system via RxPy observables.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class ControlesEventType(Enum):
    """Enumeration of control event types.

    These represent the different actions that can be triggered by
    physical controls.
    """

    # Playback control events
    PLAY_PAUSE = auto()
    NEXT_TRACK = auto()
    PREVIOUS_TRACK = auto()

    # Volume control events
    VOLUME_UP = auto()
    VOLUME_DOWN = auto()

    # Other events
    BUTTON_PRESS = auto()
    BUTTON_RELEASE = auto()
    ROTARY_CLOCKWISE = auto()
    ROTARY_COUNTERCLOCKWISE = auto()


@dataclass
class ControlesEvent:
    """Control event object.

    Represents an event from a physical control device with metadata.
    """

    event_type: ControlesEventType
    source: str
    metadata: Optional[dict] = None

    def __post_init__(self):
        """Ensure metadata is never None."""
        if self.metadata is None:
            self.metadata = {}
