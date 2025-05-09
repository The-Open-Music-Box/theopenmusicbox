import threading
import time
from typing import Optional, Dict, Any, Callable
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.services.notification_service import PlaybackSubject

logger = ImprovedLogger(__name__)

# MARK: - Audio Progress Tracker Class
class AudioProgressTracker:
    """Tracks audio playback progress and sends notifications."""
    
    # MARK: - Initialization
    def __init__(self, 
                 state_manager,  # AudioStateManager
                 playback_subject: Optional[PlaybackSubject] = None,
                 is_busy_callback: Optional[Callable[[], bool]] = None):
        self._state_manager = state_manager
        self._playback_subject = playback_subject
        self._is_busy_callback = is_busy_callback  # Function to check if playback is active
        self._progress_thread = None
        self._stop_progress = False
        self._track_end_callback = None
    
    # MARK: - Thread Management
    def start_tracking(self) -> None:
        """Start the progress tracking thread."""
        self._stop_progress = False
        if self._progress_thread is None or not self._progress_thread.is_alive():
            self._progress_thread = threading.Thread(target=self._progress_loop, daemon=True)
            self._progress_thread.start()
            logger.log(LogLevel.INFO, "Progress tracking thread started")
    
    def stop_tracking(self) -> None:
        """Stop the progress tracking thread."""
        self._stop_progress = True
        if self._progress_thread and self._progress_thread.is_alive():
            self._progress_thread.join(timeout=1.0)
            logger.log(LogLevel.INFO, "Progress tracking thread stopped")
        self._progress_thread = None
    
    def set_track_end_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback to be called when a track ends."""
        self._track_end_callback = callback
    
    # MARK: - Progress Loop
    def _progress_loop(self) -> None:
        """Progress tracking loop that runs in a separate thread."""
        last_playing_state = False
        tick = 0
        
        while not self._stop_progress:
            tick += 1
            if self._state_manager.is_playing:
                # Update and send progress information
                self._update_progress()
                
                # Check for track end
                current_playing_state = self._is_busy_callback() if self._is_busy_callback else False
                if last_playing_state and not current_playing_state:
                    logger.log(LogLevel.INFO, f"[PROGRESS_LOOP] Detected track end at tick={tick}")
                    self._handle_track_end()
                last_playing_state = current_playing_state
            time.sleep(0.1)  # Update frequently to catch track end
    
    # MARK: - Progress Updates
    def _update_progress(self) -> None:
        """Update and send current progress."""
        if not self._state_manager.current_track or not self._playback_subject:
            return
            
        try:
            # Check if playback is active
            busy = self._is_busy_callback() if self._is_busy_callback else False
            
            # If internal state indicates 'playing' but hardware says it's stopped, this is an error
            if self._state_manager.is_playing and not busy:
                logger.log(LogLevel.WARNING, "Audio state mismatch: state indicates playing but hardware says it's not")
                return
                
            # Get current position and track duration
            elapsed = self._state_manager.current_position
            total = self._state_manager.get_track_duration(self._state_manager.current_track.path)
            
            # Validate position values
            if elapsed < 0:
                elapsed = 0
            if total > 0 and elapsed > total:
                elapsed = total
                
            # Get track and playlist information
            track_info = self._state_manager.get_track_info()
            playlist_info = self._state_manager.playlist.to_dict() if self._state_manager.playlist and hasattr(self._state_manager.playlist, 'to_dict') else None
            
            # Only send updates when in playback mode
            if self._state_manager.is_playing:
                self._playback_subject.notify_track_progress(
                    elapsed=elapsed,
                    total=total,
                    track_number=track_info.get('number'),
                    track_info=track_info,
                    playlist_info=playlist_info,
                    is_playing=self._state_manager.is_playing
                )
                
                # Log only periodically to avoid log overload
                if int(elapsed) % 10 == 0 or int(elapsed) == 0 or int(elapsed) == int(total):
                    logger.log(LogLevel.INFO, f"[UPDATE_PROGRESS] notify_track_progress called (elapsed={elapsed:.2f} / {total:.2f})")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error updating progress: {str(e)}")
    
    # MARK: - Track End Handling
    def _handle_track_end(self) -> None:
        """Handle end of track notification."""
        if self._track_end_callback:
            self._track_end_callback()
        elif self._playback_subject:
            # If no callback is set, at least notify that the track ended
            self._playback_subject.notify_playback_status('ended')
