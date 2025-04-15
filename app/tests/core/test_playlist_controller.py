# app/tests/core/test_playlist_controller.py

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import json
from pathlib import Path

from app.src.core.playlist_controller import PlaylistController
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.model.playlist import Playlist
from src.model.track import Track

class TestPlaylistController(unittest.TestCase):
    def setUp(self):
        # Créer les mocks pour les dépendances
        self.audio_player_mock = Mock()
        self.audio_player_mock.is_playing = False
        self.audio_player_mock.is_finished = Mock(return_value=False)

        self.playlist_service_mock = Mock()

        # Configuration simulée
        self.config_mock = Mock()
        self.config_mock.upload_folder = "/tmp/uploads"

        # Créer le contrôleur avec des mocks
        self.controller = PlaylistController(
            self.audio_player_mock,
            self.playlist_service_mock,
            self.config_mock
        )

        # Sample playlist data pour les tests
        self.sample_tag = "ABCD1234"
        self.sample_playlist_data = {
            "id": "playlist1",
            "title": "Test Playlist",
            "path": "playlist_folder",
            "nfc_tag": self.sample_tag,
            "tracks": [
                {
                    "number": 1,
                    "title": "Track 1",
                    "filename": "track1.mp3"
                },
                {
                    "number": 2,
                    "title": "Track 2",
                    "filename": "track2.mp3"
                }
            ]
        }

        # Préparer le mock pour le service de playlist
        self.playlist_service_mock.get_playlist_by_nfc_tag.return_value = self.sample_playlist_data

        # Créer un modèle Playlist pour le mock
        self.model_playlist = Playlist(name="Test Playlist")
        track1 = Track(number=1, title="Track 1", filename="track1.mp3", path=Path("/tmp/uploads/playlist_folder/track1.mp3"))
        track2 = Track(number=2, title="Track 2", filename="track2.mp3", path=Path("/tmp/uploads/playlist_folder/track2.mp3"))
        self.model_playlist.tracks = [track1, track2]

        # Configurer to_model pour retourner le modèle Playlist
        self.playlist_service_mock.to_model.return_value = self.model_playlist

        # Patch les méthodes Path.exists
        patcher = patch("pathlib.Path.exists")
        self.mock_exists = patcher.start()
        self.mock_exists.return_value = True
        self.addCleanup(patcher.stop)

        # Mock repository
        self.playlist_service_mock.repository = Mock()

    def test_handle_tag_scanned_new_tag(self):
        """Test la détection d'un nouveau tag NFC"""
        # Configurer le comportement du audio_player pour un nouveau tag
        self.audio_player_mock.set_playlist.return_value = True

        # Appeler la méthode à tester
        self.controller.handle_tag_scanned(self.sample_tag)

        # Vérifier que les bonnes méthodes ont été appelées
        self.playlist_service_mock.get_playlist_by_nfc_tag.assert_called_once_with(self.sample_tag)
        self.playlist_service_mock.to_model.assert_called_once_with(self.sample_playlist_data)
        self.audio_player_mock.set_playlist.assert_called_once()
        self.playlist_service_mock.repository.update_playlist.assert_called_once()

    def test_handle_tag_scanned_resume_playback(self):
        """Test la reprise de lecture avec le même tag"""
        # Configurer l'état initial pour simuler un tag déjà vu
        self.controller._current_tag = self.sample_tag
        self.audio_player_mock.is_playing = False

        # Appeler la méthode à tester
        self.controller.handle_tag_scanned(self.sample_tag)

        # Vérifier que la lecture a repris
        self.audio_player_mock.resume.assert_called_once()
        # Vérifier que _process_new_tag n'a pas été appelé
        self.playlist_service_mock.get_playlist_by_nfc_tag.assert_not_called()

    def test_handle_tag_scanned_no_playlist(self):
        """Test la détection d'un tag sans playlist associée"""
        # Configurer le service pour retourner None (aucune playlist)
        self.playlist_service_mock.get_playlist_by_nfc_tag.return_value = None

        # Appeler la méthode à tester
        self.controller.handle_tag_scanned("UNKNOWN_TAG")

        # Vérifier que l'audio player n'a pas été appelé
        self.audio_player_mock.set_playlist.assert_not_called()

    def test_handle_tag_scanned_with_exception(self):
        """Test la gestion d'erreur dans handle_tag_scanned"""
        # Forcer une exception lors de la récupération de la playlist
        self.playlist_service_mock.get_playlist_by_nfc_tag.side_effect = Exception("Test error")

        # Vérifier que l'exception est capturée et ne remonte pas
        try:
            self.controller.handle_tag_scanned(self.sample_tag)
        except Exception:
            self.fail("handle_tag_scanned ne devrait pas lever d'exception")

    def test_play_playlist_with_no_valid_tracks(self):
        """Test la lecture d'une playlist sans pistes valides"""
        # Configurer le mock pour simuler des fichiers inexistants
        self.mock_exists.return_value = False

        # Appeler la méthode à tester
        self.controller.handle_tag_scanned(self.sample_tag)

        # Vérifier que set_playlist n'a pas été appelé
        self.audio_player_mock.set_playlist.assert_not_called()

    def test_tag_monitor_pause_on_tag_removal(self):
        """Test la mise en pause automatique quand un tag est retiré"""
        # Configurer le contrôleur pour simuler un tag détecté récemment
        self.controller._current_tag = self.sample_tag
        self.controller._tag_last_seen = time.time() - 2.0  # 2 secondes avant maintenant
        self.controller._pause_threshold = 1.0  # Pause après 1 seconde
        self.audio_player_mock.is_playing = True

        # Accéder directement à la fonction de surveillance
        monitor_func = self.controller._monitor_thread._target

        # Patcher time.sleep pour éviter d'attendre
        with patch('time.sleep'):
            # Permettre au thread de surveillance de s'exécuter une fois
            monitor_func()

            # Vérifier que la lecture a été mise en pause
            self.audio_player_mock.pause.assert_called_once()

    def test_update_playback_status_callback(self):
        """Test la mise à jour du compteur de lecture"""
        # Créer un mock de piste en cours
        track = Mock()
        track.id = "track1"
        track.number = 1

        # Configurer le contrôleur avec un tag actif
        self.controller._current_tag = self.sample_tag

        # Appeler la méthode à tester
        self.controller.update_playback_status_callback(track, "playing")

        # Vérifier que le compteur a été mis à jour
        self.playlist_service_mock.repository.update_track_counter.assert_called_once_with(
            self.sample_playlist_data["id"], 1
        )

    def test_handle_finished_playlist(self):
        """Test la gestion d'une playlist terminée"""
        # Configurer le contrôleur avec un tag actif
        self.controller._current_tag = self.sample_tag

        # Indiquer que la playlist est terminée
        self.audio_player_mock.is_finished.return_value = True

        # Appeler la méthode à tester avec le même tag
        self.controller.handle_tag_scanned(self.sample_tag)

        # Vérifier que _process_new_tag a été appelé malgré le même tag
        self.playlist_service_mock.get_playlist_by_nfc_tag.assert_called_once_with(self.sample_tag)

if __name__ == '__main__':
    unittest.main()