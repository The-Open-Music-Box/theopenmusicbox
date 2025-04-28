# app/src/module/audio_player/audio_wm8960.py

import pygame
from pathlib import Path
from typing import List, Optional, Dict
import time
import threading
import os
from mutagen.mp3 import MP3
from pydub import AudioSegment
import io

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.helpers.exceptions import AppError
from src.services.notification_service import PlaybackSubject
from src.module.audio_player.audio_hardware import AudioPlayerHardware
from src.model.track import Track
from src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class AudioPlayerWM8960(AudioPlayerHardware):
    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        super().__init__(playback_subject)
        self._playback_subject = playback_subject  # Ensure attribute is always set
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        self._progress_thread = None
        self._stop_progress = False
        self._volume = 100
        self._stream_start_time = 0
        self._audio_cache = {}
        self._initialize_audio_system()
        self._setup_event_handler()

    def _initialize_audio_system(self):
        """Initialize the audio system using Pygame"""
        try:
            # Initialize only the mixer module, not the entire pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            logger.log(LogLevel.INFO, "✓ Audio system initialized with WM8960")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize audio system: {str(e)}")
            raise AppError(f"Audio initialization failed: {str(e)}")

    def load_playlist(self, playlist_path: str) -> bool:
        """Load a playlist from a file"""
        logger.log(LogLevel.INFO, f"Loading playlist from {playlist_path}")
        return True

    def play_track(self, track_number: int) -> bool:
        """Play a specific track from the playlist"""
        try:
            # Stop current playback without clearing playlist
            self.stop(clear_playlist=False)

            if not self._playlist or not self._playlist.tracks:
                logger.log(LogLevel.WARNING, "No playlist or empty playlist")
                return False

            track = next((t for t in self._playlist.tracks if t.number == track_number), None)
            if not track:
                logger.log(LogLevel.WARNING, f"Track number {track_number} not found in playlist")
                return False

            self._current_track = track
            logger.log(LogLevel.INFO, f"Playing track: {track.title or track.filename}")

            # Notify that we're loading the track
            self._notify_playback_status('loading')

            # Play the file based on its format
            file_path = str(track.path)
            success = False

            try:
                # Load and play the audio file
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                self._stream_start_time = time.time()
                success = True
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error playing file: {str(e)}")
                success = False

            if success:
                self._is_playing = True
                self._notify_playback_status('playing')
                return True
            else:
                self._current_track = None
                self._notify_playback_status('stopped')
                return False

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Play error: {str(e)}")
            self._current_track = None
            self._notify_playback_status('stopped')
            return False

    def _notify_playback_status(self, status: str) -> None:
        """Notify playback status change"""
        if self._playback_subject:
            playlist_info = None
            track_info = None

            if status != 'stopped':
                if self._playlist:
                    playlist_info = {
                        'name': self._playlist.name,
                        'track_count': len(self._playlist.tracks) if self._playlist.tracks else 0
                    }

                if self._current_track:
                    track_info = {
                        'number': self._current_track.number,
                        'title': self._current_track.title or f'Track {self._current_track.number}',
                        'filename': self._current_track.filename,
                        'duration': self._get_track_duration(self._current_track.path)
                    }

            self._playback_subject.notify_playback_status(status, playlist_info, track_info)
            logger.log(LogLevel.INFO, f"Playback status update", extra={
                'status': status,
                'playlist': playlist_info,
                'current_track': track_info
            })

    def pause(self) -> None:
        """Pause playback"""
        if self._is_playing:
            try:
                pygame.mixer.music.pause()
                self._is_playing = False
                self._notify_playback_status('paused')
                logger.log(LogLevel.INFO, "Playback paused")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error pausing: {str(e)}")

    def resume(self) -> None:
        """Resume playback"""
        if not self._is_playing:
            try:
                pygame.mixer.music.unpause()
                self._is_playing = True
                self._notify_playback_status('playing')
                logger.log(LogLevel.INFO, "Playback resumed")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error resuming: {str(e)}")

    def stop(self, clear_playlist: bool = True) -> None:
        """Stop playback"""
        was_playing = self._is_playing
        try:
            pygame.mixer.music.stop()
            self._is_playing = False
            self._current_track = None
            if clear_playlist:
                self._playlist = None
            if was_playing:
                self._notify_playback_status('stopped')
                logger.log(LogLevel.INFO, "Playback stopped")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during stop: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Stop the progress thread
            if self._progress_thread:
                self._stop_progress = True
                try:
                    self._progress_thread.join(timeout=2.0)
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error stopping progress thread: {str(e)}")

            # Stop playback and quit pygame mixer
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except Exception as e:
                logger.log(LogLevel.WARNING, f"Error cleaning up pygame: {str(e)}")

            # Clear audio cache
            try:
                self._audio_cache.clear()
            except Exception as e:
                logger.log(LogLevel.WARNING, f"Error clearing audio cache: {str(e)}")

            logger.log(LogLevel.INFO, "All resources cleaned up successfully")

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during cleanup: {str(e)}")
        finally:
            self._is_playing = False
            self._current_track = None
            self._playlist = None
            self._progress_thread = None

    def set_playlist(self, playlist: Playlist) -> bool:
        """Set the current playlist and start playback"""
        try:
            self.stop()
            self._playlist = playlist
            if self._playlist and self._playlist.tracks:
                logger.log(LogLevel.INFO, f"Set playlist with {len(self._playlist.tracks)} tracks")
                return self.play_track(1)  # Play first track
            logger.log(LogLevel.WARNING, "Empty playlist or no tracks")
            return False
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting playlist: {str(e)}")
            return False

    def get_current_track(self) -> Optional[Track]:
        """Return the currently playing track"""
        return self._current_track

    def get_playlist(self) -> Optional[Playlist]:
        """Return the current playlist"""
        return self._playlist

    def next_track(self) -> None:
        """Play next track"""
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "No current track or playlist")
            return

        next_number = self._current_track.number + 1
        if next_number <= len(self._playlist.tracks):
            logger.log(LogLevel.INFO, f"Moving to next track: {next_number}")
            self.play_track(next_number)
        else:
            logger.log(LogLevel.INFO, "Reached end of playlist")

    def previous_track(self) -> None:
        """Play previous track"""
        if not self._current_track or not self._playlist:
            logger.log(LogLevel.WARNING, "No current track or playlist")
            return

        prev_number = self._current_track.number - 1
        if prev_number > 0:
            logger.log(LogLevel.INFO, f"Moving to previous track: {prev_number}")
            self.play_track(prev_number)
        else:
            logger.log(LogLevel.INFO, "Already at first track")

    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)"""
        try:
            self._volume = max(0, min(100, volume))
            # Convert 0-100 range to 0.0-1.0 for pygame
            pygame_volume = self._volume / 100.0
            pygame.mixer.music.set_volume(pygame_volume)
            logger.log(LogLevel.INFO, f"Volume set to {self._volume}%")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting volume: {str(e)}")
            return False

    def get_volume(self) -> int:
        """Return current volume"""
        return self._volume

    @property
    def is_playing(self) -> bool:
        """Return True if currently playing"""
        return self._is_playing

    def _setup_event_handler(self):
        """Set up event handler"""
        self._start_progress_thread()

    def _start_progress_thread(self):
        """Start progress tracking thread"""
        if self._progress_thread:
            self._stop_progress = True
            self._progress_thread.join(timeout=1.0)

        self._stop_progress = False
        self._progress_thread = threading.Thread(target=self._progress_loop)
        self._progress_thread.daemon = True
        self._progress_thread.start()

    def _progress_loop(self):
        """Progress tracking loop"""
        last_playing_state = False
        last_update_time = 0
        while not self._stop_progress:
            if self._is_playing and self._playback_subject and self._current_track:
                current_time = time.time()
                if current_time - last_update_time >= 1.0:
                    last_update_time = current_time
                    self._update_progress()

                # Check if music has stopped playing (track ended)
                current_playing_state = pygame.mixer.music.get_busy()
                if last_playing_state and not current_playing_state:
                    self._handle_track_end()
                last_playing_state = current_playing_state

            time.sleep(0.1)  # Update more frequently to catch track end

    def _update_progress(self):
        """Update and send current progress"""
        if not self._current_track or not self._playback_subject:
            return

        try:
            if pygame.mixer.music.get_busy():
                # Calculate position based on elapsed time
                elapsed = time.time() - self._stream_start_time
                total = self._get_track_duration(self._current_track.path)

                # Build track_info and playlist_info for frontend
                track_info = {
                    'number': self._current_track.number,
                    'title': getattr(self._current_track, 'title', f'Track {self._current_track.number}'),
                    'filename': getattr(self._current_track, 'filename', None),
                    'duration': total
                }
                playlist_info = self._playlist.to_dict() if self._playlist and hasattr(self._playlist, 'to_dict') else None

                # Send update
                self._playback_subject.notify_track_progress(
                    elapsed=elapsed,
                    total=total,
                    track_number=track_info.get('number'),
                    track_info=track_info,
                    playlist_info=playlist_info,
                    is_playing=self._is_playing
                )
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error updating progress: {str(e)}")

    def _get_track_duration(self, file_path: Path) -> float:
        """Get track duration in seconds"""
        try:
            if str(file_path).lower().endswith('.mp3'):
                audio = MP3(str(file_path))
                return audio.info.length
            return 0
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Error getting track duration: {str(e)}")
            return 0

    def _handle_track_end(self):
        """Handle end of track"""
        if self._is_playing and self._current_track and self._playlist:
            next_number = self._current_track.number + 1
            if next_number <= len(self._playlist.tracks):
                logger.log(LogLevel.INFO, f"Track ended, playing next: {next_number}")
                self.play_track(next_number)
            else:
                logger.log(LogLevel.INFO, "Playlist ended")
                self.stop()

    # def is_finished(self) -> bool:
    #     """Return True if playlist has finished playing"""
    #     return self._playlist_finished if hasattr(self, '_playlist_finished') else False