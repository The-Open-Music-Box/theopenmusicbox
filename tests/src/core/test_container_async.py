"""Unit tests for the ContainerAsync class."""

from unittest.mock import MagicMock, patch

import pytest

from app.src.core.container_async import ContainerAsync
from app.src.services.notification_service import PlaybackSubject


class TestContainerAsync:
    """Tests for the ContainerAsync class."""

    def test_init(self, mock_config, reset_playback_subject):
        """Test the container initialization."""
        # Arrange
        with patch("app.src.services.playlist_service.PlaylistService"):
            with patch("app.src.module.audio_player.audio_factory.get_audio_player"):
                with patch(
                    "app.src.module.nfc.nfc_factory.get_nfc_handler",
                    side_effect=Exception("NFC not available"),
                ):
                    # Act
                    container = ContainerAsync(mock_config)

                    # Assert
                    assert container._config == mock_config
                    assert container._nfc_handler is None
                    assert container._led_hat is None
                    assert isinstance(container._playback_subject, PlaybackSubject)
                    assert hasattr(container, "_playlist_service")
                    assert hasattr(container, "_audio")

    @pytest.mark.asyncio
    async def test_init_with_nfc(self, mock_config, reset_playback_subject):
        """Test container initialization with NFC available."""
        # Arrange
        mock_nfc = MagicMock()

        with patch("app.src.services.playlist_service.PlaylistService"):
            with patch("app.src.module.audio_player.audio_factory.get_audio_player"):
                with patch(
                    "app.src.module.nfc.nfc_factory.get_nfc_handler",
                    return_value=mock_nfc,
                ):
                    with patch("asyncio.Lock"):
                        # Act
                        container = ContainerAsync(mock_config)
                        # Le NFC handler est initialisé dans initialize_async(), pas
                        # dans __init__()
                        await container.initialize_async()

                        # Assert
                        assert container._nfc_handler == mock_nfc

    def test_config_property(self, mock_config, reset_playback_subject):
        """Test the config property."""
        # Arrange
        with patch("app.src.services.playlist_service.PlaylistService"):
            with patch("app.src.module.audio_player.audio_factory.get_audio_player"):
                with patch(
                    "app.src.module.nfc.nfc_factory.get_nfc_handler",
                    side_effect=Exception("NFC not available"),
                ):
                    container = ContainerAsync(mock_config)

                    # Act
                    result = container.config

                    # Assert
                    assert result == mock_config

    def test_playback_subject_property(self, mock_config, reset_playback_subject):
        """Test the playback_subject property."""
        # Arrange
        with patch("app.src.services.playlist_service.PlaylistService"):
            with patch("app.src.module.audio_player.audio_factory.get_audio_player"):
                with patch(
                    "app.src.module.nfc.nfc_factory.get_nfc_handler",
                    side_effect=Exception("NFC not available"),
                ):
                    container = ContainerAsync(mock_config)

                    # Act
                    result = container.playback_subject

                    # Assert
                    assert isinstance(result, PlaybackSubject)
                    assert result == container._playback_subject

    def test_nfc_property(self, mock_config, reset_playback_subject):
        """Test the nfc property."""
        # Arrange
        mock_nfc = MagicMock()

        with patch("app.src.services.playlist_service.PlaylistService"):
            with patch("app.src.module.audio_player.audio_factory.get_audio_player"):
                with patch(
                    "app.src.module.nfc.nfc_factory.get_nfc_handler",
                    return_value=mock_nfc,
                ):
                    with patch("asyncio.Lock"):
                        container = ContainerAsync(mock_config)

                        # Act
                        result = container.nfc

                        # Assert
                        # La méthode nfc retourne maintenant _nfc_service, plus
                        # _nfc_handler
                        assert result == container._nfc_service
                        # S'assurer que le NFCService est initialisé, même si le handler
                        # n'est pas encore utilisé

    def test_audio_property(self, mock_config, reset_playback_subject):
        """Test the audio property."""
        # Arrange
        # Create a simpler mock for this test
        mock_audio = MagicMock()

        # Check if audio is properly initialized - without trying to mock the factory
        with patch("app.src.services.playlist_service.PlaylistService"):
            with patch(
                "app.src.core.container_async.get_audio_player", return_value=mock_audio
            ):
                with patch(
                    "app.src.module.nfc.nfc_factory.get_nfc_handler",
                    side_effect=Exception("NFC not available"),
                ):
                    container = ContainerAsync(mock_config)

                    # Act
                    result = container.audio

                    # Assert
                    assert result == mock_audio

    @pytest.mark.asyncio
    async def test_cleanup_async(self, mock_config, reset_playback_subject):
        """Test resource cleanup."""
        # Arrange
        with patch("app.src.services.playlist_service.PlaylistService"):
            with patch("app.src.module.audio_player.audio_factory.get_audio_player"):
                with patch(
                    "app.src.module.nfc.nfc_factory.get_nfc_handler",
                    side_effect=Exception("NFC not available"),
                ):
                    with patch("app.src.core.container_async.logger") as mock_logger:
                        container = ContainerAsync(mock_config)

                        # Act - Maintenant nous pouvons tester de manière asynchrone
                        await container.cleanup_async()

                        # Assert
                        # On vérifie simplement que la méthode s'exécute sans erreur
                        mock_logger.log.assert_called()
