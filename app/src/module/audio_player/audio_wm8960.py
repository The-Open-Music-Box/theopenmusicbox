# app/src/module/audio_player/audio_wm8960.py

import pyaudio
from pathlib import Path
from typing import List, Optional, Dict
import time
import wave
import threading
import os
from mutagen.mp3 import MP3
from pydub import AudioSegment
import io
import numpy as np

from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.helpers.exceptions import AppError
from src.services.notification_service import PlaybackSubject
from src.module.audio_player.audio_interface import AudioPlayerInterface
from src.model.track import Track
from src.model.playlist import Playlist

logger = ImprovedLogger(__name__)

class AudioPlayerWM8960(AudioPlayerInterface):
    CHUNK_SIZE = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100

    def __init__(self, playback_subject: Optional[PlaybackSubject] = None):
        super().__init__(playback_subject)
        self._is_playing = False
        self._playlist = None
        self._current_track = None
        self._progress_thread = None
        self._stop_progress = False
        self._volume = 100
        self._pyaudio = None
        self._device_index = None
        self._stream = None
        self._stream_start_time = 0
        self._initialize_audio_system()

    def _initialize_audio_system(self):
        """Initialise le système audio en donnant la priorité à la carte WM8960"""
        try:
            self._pyaudio = pyaudio.PyAudio()
            device_count = self._pyaudio.get_device_count()
            logger.log(LogLevel.INFO, f"Found {device_count} audio devices")

            # Afficher tous les périphériques pour le débogage
            for i in range(device_count):
                try:
                    device_info = self._pyaudio.get_device_info_by_index(i)
                    logger.log(LogLevel.INFO, f"Device {i}: {device_info['name']}")
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error getting device info for index {i}: {str(e)}")

            # Chercher la carte WM8960 en priorité
            device_index = self._find_wm8960_device()

            if device_index is not None:
                logger.log(LogLevel.INFO, f"Found WM8960 device at index {device_index}")
                # Tester si le périphérique trouvé fonctionne
                if self._test_audio_device(device_index):
                    self._device_index = device_index
                    logger.log(LogLevel.INFO, f"WM8960 Audio Player initialized using device index {device_index}")
                    return
                else:
                    logger.log(LogLevel.WARNING, f"WM8960 device at index {device_index} failed test")
            else:
                logger.log(LogLevel.WARNING, "WM8960 not found in audio devices")

            # Si on arrive ici, soit pas de WM8960, soit WM8960 trouvé mais test échoué
            # Test de tous les périphériques disponibles jusqu'à en trouver un qui fonctionne
            logger.log(LogLevel.INFO, "Searching for a working audio device")
            for i in range(device_count):
                if self._test_audio_device(i):
                    self._device_index = i
                    logger.log(LogLevel.INFO, f"Found working alternative device at index {i}")
                    return

            # Si aucun périphérique ne fonctionne, utiliser le périphérique 0 par défaut
            logger.log(LogLevel.WARNING, "No working audio device found, defaulting to device 0")
            self._device_index = 0

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to initialize audio system: {str(e)}")
            # En dernier recours, utiliser device 0
            self._device_index = 0
            logger.log(LogLevel.WARNING, "Using device 0 as last resort")

    def _find_wm8960_device(self) -> Optional[int]:
        """Recherche le périphérique WM8960 dans la liste des périphériques audio"""
        try:
            # 1. D'abord, vérifier dans /proc/asound/cards
            alsa_cards = self._get_alsa_card_info()
            wm8960_alsa_card = None
            wm8960_keywords = ['wm8960', 'soundcard']

            # Log toutes les cartes ALSA pour le débogage
            logger.log(LogLevel.INFO, f"ALSA cards found: {alsa_cards}")

            # Chercher la carte WM8960 dans les cartes ALSA
            for card_num, card_name in alsa_cards.items():
                if any(keyword in card_name.lower() for keyword in wm8960_keywords):
                    logger.log(LogLevel.INFO, f"Found WM8960 ALSA card: {card_num} - {card_name}")
                    wm8960_alsa_card = card_num
                    break

            # 2. Si trouvé dans ALSA, chercher dans les périphériques PyAudio
            if wm8960_alsa_card is not None:
                for i in range(self._pyaudio.get_device_count()):
                    try:
                        device_info = self._pyaudio.get_device_info_by_index(i)
                        device_name = device_info['name'].lower()

                        # Rechercher par nom ou par alias
                        if "wm8960" in device_name or f"card {wm8960_alsa_card}" in device_name:
                            if device_info['maxOutputChannels'] > 0:
                                logger.log(LogLevel.INFO, f"Found matching WM8960 device at index {i}")
                                return i
                    except Exception as e:
                        logger.log(LogLevel.WARNING, f"Error checking device {i}: {str(e)}")

                # Si on a trouvé la carte dans ALSA mais pas dans PyAudio par nom,
                # on cherche un périphérique qui correspond à l'index de carte ALSA
                for i in range(self._pyaudio.get_device_count()):
                    try:
                        device_info = self._pyaudio.get_device_info_by_index(i)
                        if device_info['maxOutputChannels'] > 0:
                            # Vérifier si le device contient l'indice de la carte ALSA
                            device_str = str(device_info)
                            if f"card={wm8960_alsa_card}" in device_str or f"card {wm8960_alsa_card}" in device_str:
                                logger.log(LogLevel.INFO, f"Found device with matching ALSA card index {wm8960_alsa_card} at index {i}")
                                return i
                    except Exception:
                        pass

            # 3. Si pas trouvé via ALSA, recherche directe dans PyAudio
            for i in range(self._pyaudio.get_device_count()):
                try:
                    device_info = self._pyaudio.get_device_info_by_index(i)
                    device_name = device_info['name'].lower()
                    if "wm8960" in device_name and device_info['maxOutputChannels'] > 0:
                        logger.log(LogLevel.INFO, f"Found WM8960 device at index {i} via direct search")
                        return i
                except Exception:
                    pass

            # Aucun périphérique WM8960 trouvé
            return None

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error in _find_wm8960_device: {str(e)}")
            return None

    def _get_alsa_card_info(self):
        """Lit directement /proc/asound/cards pour obtenir les informations des cartes ALSA"""
        cards = {}
        try:
            with open('/proc/asound/cards', 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if '[' in line and ']' in line:
                        parts = line.strip().split(' ', 1)
                        if parts and parts[0].isdigit():
                            card_num = int(parts[0])
                            card_name = line.split('[')[1].split(']')[0]
                            cards[card_num] = card_name
                            logger.log(LogLevel.INFO, f"ALSA card {card_num}: {card_name}")
            return cards
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Failed to read ALSA card info: {str(e)}")
            return {}

    def _test_audio_device(self, device_index: int) -> bool:
        """Teste un périphérique audio pour vérifier qu'il fonctionne correctement"""
        test_stream = None
        try:
            device_info = self._pyaudio.get_device_info_by_index(device_index)
            logger.log(LogLevel.INFO, f"Testing device {device_index}: {device_info}")  # Log complet

            # Vérifier que le périphérique a des canaux de sortie
            if device_info['maxOutputChannels'] <= 0:
                logger.log(LogLevel.WARNING, f"Device {device_index} has no output channels")
                return False

            # Commencer par essayer en mono, plus simple et plus fiable
            channels = 1

            # Créer le stream de test
            test_stream = self._pyaudio.open(
                format=self.FORMAT,
                channels=channels,
                rate=44100,  # Fréquence standard
                output=True,
                output_device_index=device_index,
                frames_per_buffer=1024  # Plus petit buffer pour un test rapide
            )

            # Générer un buffer silencieux pour le test
            silence = b'\x00' * (1024 * channels * 2)  # 2 octets par échantillon
            test_stream.write(silence, exception_on_underflow=False)
            logger.log(LogLevel.INFO, f"Successfully tested audio device {device_index}")
            return True

        except Exception as e:
            logger.log(LogLevel.WARNING, f"Failed to test audio device {device_index} in mono mode: {str(e)}")

            # Si le test mono échoue et que le device a 2+ canaux, essayer en stéréo
            try:
                if test_stream:
                    test_stream.stop_stream()
                    test_stream.close()
                    test_stream = None

                device_info = self._pyaudio.get_device_info_by_index(device_index)
                if device_info['maxOutputChannels'] >= 2:
                    test_stream = self._pyaudio.open(
                        format=self.FORMAT,
                        channels=2,
                        rate=44100,
                        output=True,
                        output_device_index=device_index,
                        frames_per_buffer=1024
                    )
                    silence = b'\x00' * (1024 * 2 * 2)
                    test_stream.write(silence, exception_on_underflow=False)
                    logger.log(LogLevel.INFO, f"Successfully tested audio device {device_index} in stereo mode")
                    return True
            except Exception as stereo_e:
                logger.log(LogLevel.ERROR, f"Failed to test audio device {device_index} in stereo mode: {str(stereo_e)}")

            return False

        finally:
            if test_stream:
                try:
                    test_stream.stop_stream()
                    test_stream.close()
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error closing test stream: {str(e)}")

    def _create_audio_stream(self, format, channels, rate, callback=None):
        """Crée un stream audio avec gestion d'erreur améliorée"""
        try:
            # Vérifier si le périphérique existe
            if self._device_index is None:
                self._device_index = 0
                logger.log(LogLevel.WARNING, "No device index set, defaulting to 0")

            # Limiter aux valeurs supportées par la carte WM8960
            channels = min(2, max(1, channels))  # 1 ou 2 canaux

            # Log complet des paramètres du stream
            logger.log(LogLevel.INFO, f"Creating audio stream with: device={self._device_index}, format={format}, channels={channels}, rate={rate}")

            # Créer le stream audio
            stream = self._pyaudio.open(
                format=format,
                channels=channels,
                rate=rate,
                output=True,
                output_device_index=self._device_index,
                stream_callback=callback,
                frames_per_buffer=self.CHUNK_SIZE
            )

            logger.log(LogLevel.INFO, f"Created audio stream successfully")
            return stream

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error creating audio stream: {str(e)}")
            # Réessayer avec des paramètres par défaut si ça échoue
            try:
                logger.log(LogLevel.INFO, "Retrying with conservative default parameters")
                stream = self._pyaudio.open(
                    format=self.FORMAT,
                    channels=1,  # Essayer d'abord en mono
                    rate=44100,
                    output=True,
                    output_device_index=self._device_index,
                    stream_callback=callback,
                    frames_per_buffer=self.CHUNK_SIZE
                )
                logger.log(LogLevel.INFO, "Created audio stream with mono parameters")
                return stream
            except Exception as mono_e:
                logger.log(LogLevel.ERROR, f"Mono fallback failed: {str(mono_e)}")
                try:
                    # Dernier essai avec stéréo (si le premier essai n'était pas déjà en stéréo)
                    stream = self._pyaudio.open(
                        format=self.FORMAT,
                        channels=2,
                        rate=44100,
                        output=True,
                        output_device_index=self._device_index,
                        stream_callback=callback,
                        frames_per_buffer=self.CHUNK_SIZE
                    )
                    logger.log(LogLevel.INFO, "Created audio stream with stereo parameters")
                    return stream
                except Exception as fallback_e:
                    logger.log(LogLevel.ERROR, f"All stream creation attempts failed: {str(fallback_e)}")
                    raise

    def load_playlist(self, playlist_path: str) -> bool:
        """Charge une playlist depuis un fichier"""
        logger.log(LogLevel.INFO, f"Loading playlist from {playlist_path}")
        # Implementation for loading playlist
        return True

    def play_track(self, track_number: int) -> bool:
        """Joue un morceau spécifique de la playlist"""
        try:
            if not self._playlist or not self._playlist.tracks:
                logger.log(LogLevel.WARNING, "No playlist or empty playlist")
                return False

            track = next((t for t in self._playlist.tracks if t.number == track_number), None)
            if not track:
                logger.log(LogLevel.WARNING, f"Track number {track_number} not found in playlist")
                return False

            self._current_track = track
            logger.log(LogLevel.INFO, f"Playing track: {track.title or track.filename}")

            # Fermer le stream existant s'il y en a un
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error closing existing stream: {str(e)}")
                self._stream = None

            # Déterminer le format du fichier et créer le stream approprié
            file_path = str(track.path)
            if file_path.lower().endswith('.wav'):
                return self._play_wav_file(track.path)
            elif file_path.lower().endswith('.mp3'):
                return self._play_mp3_file(track.path)
            else:
                logger.log(LogLevel.ERROR, f"Unsupported audio format: {track.path}")
                return False

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Play error: {str(e)}")
            return False

    def _play_wav_file(self, file_path: Path) -> bool:
        """Joue un fichier WAV avec gestion d'erreur améliorée"""
        try:
            # Vérifier que le fichier existe
            if not file_path.exists():
                logger.log(LogLevel.ERROR, f"WAV file not found: {file_path}")
                return False

            # Ouvrir le fichier WAV
            wf = wave.open(str(file_path), 'rb')

            # Obtenir les propriétés du fichier
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            rate = wf.getframerate()

            logger.log(LogLevel.INFO, f"WAV properties: channels={channels}, width={width}, rate={rate}")

            # Callback pour lire les données audio avec gestion d'erreur améliorée
            def callback(in_data, frame_count, time_info, status):
                try:
                    data = wf.readframes(frame_count)
                    if not data or len(data) == 0:
                        # Fin du fichier
                        logger.log(LogLevel.INFO, "End of file reached")
                        # Utiliser un thread séparé pour appeler _handle_track_end pour éviter un deadlock
                        threading.Thread(target=self._handle_track_end).start()
                        return (bytes(frame_count * channels * width), pyaudio.paComplete)

                    if len(data) < frame_count * channels * width:
                        # Données insuffisantes, compléter avec du silence
                        silence = b'\x00' * (frame_count * channels * width - len(data))
                        data += silence

                    return (data, pyaudio.paContinue)

                except Exception as e:
                    logger.log(LogLevel.ERROR, f"WAV callback error: {str(e)}")
                    # Retourner du silence en cas d'erreur pour éviter un crash
                    return (bytes(frame_count * channels * width), pyaudio.paComplete)

            # Créer le stream audio
            try:
                format_code = self._pyaudio.get_format_from_width(width)
                self._stream = self._create_audio_stream(
                    format=format_code,
                    channels=channels,
                    rate=rate,
                    callback=callback
                )

                # Démarrer la lecture
                self._stream_start_time = time.time()
                self._stream.start_stream()
                self._is_playing = True
                self._notify_playback_status('playing')
                logger.log(LogLevel.INFO, f"Playing: {file_path}")
                return True

            except Exception as e:
                logger.log(LogLevel.ERROR, f"Failed to create WAV stream: {str(e)}")
                # Fermer le fichier en cas d'erreur
                wf.close()
                return False

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error opening WAV file: {str(e)}")
            return False

    def _play_mp3_file(self, file_path: Path) -> bool:
        """Joue un fichier MP3 en le convertissant en PCM via pydub"""
        try:
            # Charger le fichier MP3 avec pydub
            logger.log(LogLevel.INFO, f"Loading MP3 file: {file_path}")
            audio = AudioSegment.from_mp3(str(file_path))

            # Convertir en format compatible avec PyAudio
            audio = audio.set_frame_rate(self.RATE)
            audio = audio.set_channels(self.CHANNELS)
            audio = audio.set_sample_width(pyaudio.get_sample_size(self.FORMAT))

            # Obtenir les données audio brutes
            raw_data = audio.raw_data

            # Calculer la taille du chunk en octets
            bytes_per_sample = audio.sample_width * audio.channels
            chunk_bytes = self.CHUNK_SIZE * bytes_per_sample

            # Créer un générateur pour lire les données par chunks
            def audio_chunks():
                for i in range(0, len(raw_data), chunk_bytes):
                    yield raw_data[i:i + chunk_bytes]

            chunks_iterator = audio_chunks()

            # Callback pour la lecture audio
            def callback(in_data, frame_count, time_info, status):
                try:
                    chunk = next(chunks_iterator, None)
                    if chunk is None or len(chunk) == 0:
                        # Fin du fichier
                        logger.log(LogLevel.INFO, "End of MP3 file reached")
                        # Utiliser un thread séparé pour appeler _handle_track_end
                        threading.Thread(target=self._handle_track_end).start()
                        return (bytes(frame_count * self.CHANNELS * 2), pyaudio.paComplete)

                    # Si le chunk est plus petit que prévu, le compléter avec du silence
                    if len(chunk) < chunk_bytes:
                        chunk = chunk + b'\x00' * (chunk_bytes - len(chunk))

                    return (chunk, pyaudio.paContinue)
                except Exception as e:
                    logger.log(LogLevel.ERROR, f"MP3 callback error: {str(e)}")
                    return (bytes(frame_count * self.CHANNELS * 2), pyaudio.paComplete)

            # Créer et démarrer le stream audio
            self._stream = self._create_audio_stream(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                callback=callback
            )

            # Démarrer la lecture
            self._stream_start_time = time.time()
            self._stream.start_stream()
            self._is_playing = True
            self._notify_playback_status('playing')
            logger.log(LogLevel.INFO, f"Playing MP3: {file_path}")
            return True

        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error playing MP3 file: {str(e)}")
            return False

    def _notify_playback_status(self, status: str) -> None:
        """Notifie le changement d'état de lecture"""
        if self._playback_subject:
            playlist_info = None
            track_info = None

            if self._playlist:
                playlist_info = {'name': self._playlist.name}

            if self._current_track:
                track_info = {
                    'number': self._current_track.number,
                    'title': self._current_track.title or f'Track {self._current_track.number}',
                    'filename': self._current_track.filename
                }

            self._playback_subject.notify_playback_status(status, playlist_info, track_info)
            logger.log(LogLevel.INFO, f"Playback status update", extra={
                'status': status,
                'playlist': playlist_info,
                'current_track': track_info
            })

    def pause(self) -> None:
        """Met en pause la lecture"""
        if self._is_playing and self._stream:
            try:
                self._stream.stop_stream()
                self._is_playing = False
                self._notify_playback_status('paused')
                logger.log(LogLevel.INFO, "Playback paused")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error pausing: {str(e)}")

    def resume(self) -> None:
        """Reprend la lecture"""
        if not self._is_playing and self._stream and not self._stream.is_stopped():
            try:
                self._stream.start_stream()
                self._is_playing = True
                self._notify_playback_status('playing')
                logger.log(LogLevel.INFO, "Playback resumed")
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error resuming: {str(e)}")

    def stop(self) -> None:
        """Arrête la lecture"""
        try:
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error stopping stream: {str(e)}")
            self._stream = None
            self._is_playing = False
            self._playlist = None
            self._current_track = None
            self._notify_playback_status('stopped')
            logger.log(LogLevel.INFO, "Playback stopped")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during stop: {str(e)}")

    def cleanup(self) -> None:
        """Libère toutes les ressources audio"""
        try:
            self.stop()
            if self._pyaudio:
                try:
                    self._pyaudio.terminate()
                except Exception as e:
                    logger.log(LogLevel.WARNING, f"Error terminating PyAudio: {str(e)}")
            logger.log(LogLevel.INFO, "Resources cleaned up")
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error during cleanup: {str(e)}")

    def set_playlist(self, playlist: Playlist) -> bool:
        """Définit la playlist actuelle et commence la lecture"""
        try:
            self.stop()
            self._playlist = playlist
            if self._playlist and self._playlist.tracks:
                logger.log(LogLevel.INFO, f"Set playlist with {len(self._playlist.tracks)} tracks")
                return self.play_track(1)  # Jouer le premier morceau
            logger.log(LogLevel.WARNING, "Empty playlist or no tracks")
            return False
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting playlist: {str(e)}")
            return False

    def get_current_track(self) -> Optional[Track]:
        """Retourne le morceau en cours de lecture"""
        return self._current_track

    def get_playlist(self) -> Optional[Playlist]:
        """Retourne la playlist actuelle"""
        return self._playlist

    def next_track(self) -> None:
        """Passe au morceau suivant"""
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
        """Passe au morceau précédent"""
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
        """Définit le volume (0-100)"""
        try:
            self._volume = max(0, min(100, volume))
            logger.log(LogLevel.INFO, f"Volume set to {self._volume}%")
            # Note: L'implémentation matérielle dépendra de la carte WM8960
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error setting volume: {str(e)}")
            return False

    def get_volume(self) -> int:
        """Retourne le volume actuel"""
        return self._volume

    @property
    def is_playing(self) -> bool:
        """Indique si la lecture est en cours"""
        return self._is_playing

    def _handle_track_end(self):
        """Gère la fin d'un morceau"""
        if self._is_playing and self._current_track and self._playlist:
            next_number = self._current_track.number + 1
            if next_number <= len(self._playlist.tracks):
                logger.log(LogLevel.INFO, f"Track ended, playing next: {next_number}")
                self.play_track(next_number)
            else:
                logger.log(LogLevel.INFO, "Playlist ended")
                self.stop()

    def _setup_event_handler(self):
        """Configure le gestionnaire d'événements"""
        self._start_progress_thread()

    def _start_progress_thread(self):
        """Démarre le thread de suivi de progression"""
        if self._progress_thread:
            self._stop_progress = True
            self._progress_thread.join(timeout=1.0)

        self._stop_progress = False
        self._progress_thread = threading.Thread(target=self._progress_loop)
        self._progress_thread.daemon = True
        self._progress_thread.start()

    def _progress_loop(self):
        """Boucle de suivi de progression"""
        while not self._stop_progress:
            if self._is_playing and self._playback_subject and self._current_track:
                self._update_progress()
            time.sleep(0.5)  # Mettre à jour toutes les 500ms

    def _update_progress(self):
        """Met à jour et envoie la progression actuelle"""
        if not self._current_track or not self._playback_subject:
            return

        try:
            if self._stream and self._stream.is_active():
                # Calculer la position en se basant sur le temps écoulé
                elapsed = time.time() - self._stream_start_time

                # Obtenir la durée totale du fichier
                total = 0
                file_path = str(self._current_track.path)

                if file_path.lower().endswith('.wav'):
                    with wave.open(file_path, 'rb') as wf:
                        total = wf.getnframes() / wf.getframerate()
                elif file_path.lower().endswith('.mp3'):
                    try:
                        audio = MP3(file_path)
                        total = audio.info.length
                    except Exception as e:
                        logger.log(LogLevel.WARNING, f"Error getting MP3 duration: {str(e)}")

                # Envoyer la mise à jour
                self._playback_subject.notify_track_progress(
                    elapsed=elapsed,
                    total=total,
                    track_number=self._current_track.number
                )
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Error updating progress: {str(e)}")