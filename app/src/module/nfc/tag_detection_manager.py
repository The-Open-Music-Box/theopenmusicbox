"""
Tag detection manager for handling NFC tag detection logic.

This module provides a dedicated class for managing tag detection state and logic,
separating it from the hardware access concerns.
"""
from typing import Optional, Dict, Any
import time
from rx.subject import Subject
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class TagDetectionManager:
    """
    Manages tag detection logic including debouncing and state tracking.
    
    This class is responsible for determining when a tag event should be emitted
    based on timing and state information, separating this logic from hardware access.
    """
    
    def __init__(self, cooldown_period: float = 0.5, removal_threshold: float = 1.0):
        """
        Initialize the tag detection manager.
        
        Args:
            cooldown_period: Minimum time between tag detections (seconds)
            removal_threshold: Time before considering a tag removed (seconds)
        """
        self._tag_subject = Subject()
        self._last_tag = None
        self._last_read_time = 0
        self._tag_present = False
        self._last_no_tag_time = 0
        self.cooldown_period = cooldown_period
        self.removal_threshold = removal_threshold
    
    def process_tag_detection(self, uid_string: str) -> Optional[Dict[str, Any]]:
        """
        Process a raw tag detection and determine if it should emit an event.
        
        Args:
            uid_string: The UID string of the detected tag
            
        Returns:
            Tag data dictionary if an event should be emitted, None otherwise
        """
        current_time = time.time()
        emit_event = False
        
        # New tag detected
        if self._last_tag != uid_string:
            logger.log(LogLevel.INFO, f"New tag detected: {uid_string}")
            emit_event = True
            self._tag_present = True
        # Tag reappeared after being removed
        elif current_time - self._last_no_tag_time >= self.removal_threshold and not self._tag_present:
            logger.log(LogLevel.INFO, f"Tag reappeared: {uid_string}")
            emit_event = True
            self._tag_present = True
        # Rate limiting - respect minimum delay between detections
        elif current_time - self._last_read_time >= self.cooldown_period and not self._tag_present:
            logger.log(LogLevel.INFO, f"Tag detected after cooldown: {uid_string}")
            emit_event = True
            self._tag_present = True
            
        # Update states
        self._last_tag = uid_string
        self._last_read_time = current_time
            
        # Emit event if necessary
        if emit_event:
            tag_data = {
                'uid': uid_string,
                'timestamp': current_time,
                'new_detection': True  # Flag to indicate this is a detection to process
            }
            
            logger.log(LogLevel.INFO, f"Emitting tag data: {tag_data}")
            self._tag_subject.on_next(tag_data)
            return tag_data
            
        return None
    
    def process_tag_absence(self):
        """
        Process the absence of a tag.
        """
        current_time = time.time()
        if self._tag_present:
            self._tag_present = False
            self._last_no_tag_time = current_time
            logger.log(LogLevel.INFO, "Tag removed from reader")
    
    @property
    def tag_subject(self) -> Subject:
        """
        Get the tag detection subject for subscribing to tag events.
        
        Returns:
            The tag detection Subject instance
        """
        return self._tag_subject
