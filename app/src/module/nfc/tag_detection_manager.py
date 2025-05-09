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
        
        Détecte quand un tag n'est plus présent et émet un événement d'absence
        qui sera traité par le PlaylistController pour mettre en pause la lecture.
        """
        current_time = time.time()
        
        # Vérifie si un tag était présent et est maintenant absent
        if self._tag_present:
            # Marquer comme absent et enregistrer l'horodatage
            self._tag_present = False
            self._last_no_tag_time = current_time
            
            # Calculer le temps de présence du tag (utile pour le débogage)
            duration_present = 0
            if hasattr(self, '_last_tag_detection_time') and self._last_tag_detection_time > 0:
                duration_present = current_time - self._last_tag_detection_time
                logger.log(LogLevel.DEBUG, f"Tag présent pendant {duration_present:.2f} secondes")
            
            # Journal et notification d'absence
            logger.log(LogLevel.INFO, f"Tag removed from reader (was present for {duration_present:.2f}s)")
            
            # Construire un événement d'absence complet avec les données de contexte
            absence_event = {
                'absence': True,
                'timestamp': current_time,
                'last_tag': self._last_tag,  # Inclure l'ID du dernier tag pour référence
                'duration_present': duration_present
            }
            
            # Émettre l'événement d'absence à tous les observateurs
            self._tag_subject.on_next(absence_event)
            
            # Réinitialiser le dernier tag vu mais conserver sa valeur pour référence
            # self._last_tag reste inchangé pour permettre la comparaison lors d'une réapparition

    
    def force_redetect(self, uid_string: str) -> Optional[Dict[str, Any]]:
        """
        Force re-detection of a tag that's already present on the reader.
        
        This is used to force the system to re-process a tag that's still 
        physically present after a mode change (e.g., from association to playback).
        
        Args:
            uid_string: The UID string of the tag to re-detect
            
        Returns:
            Tag data dictionary that was emitted
        """
        logger.log(LogLevel.INFO, f"Forcing re-detection of tag: {uid_string}")
        
        current_time = time.time()
        tag_data = {
            'uid': uid_string,
            'timestamp': current_time,
            'new_detection': True,  # Critical flag to ensure the tag is processed as new
            'forced': True  # Flag to indicate this was a forced re-detection
        }
        
        # Emit the tag data event
        self._tag_subject.on_next(tag_data)
        
        # Update internal state to reflect the re-detection
        self._last_tag = uid_string
        self._last_read_time = current_time
        self._tag_present = True
        
        return tag_data
        
    @property
    def tag_subject(self) -> Subject:
        """
        Get the tag detection subject for subscribing to tag events.
        
        Returns:
            The tag detection Subject instance
        """
        return self._tag_subject
