# pylint: disable=redefined-outer-name, protected-access
import pytest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path

from app.src.services.youtube.downloader import YouTubeDownloader  # pylint: disable=import-error
from app.src.monitoring.logging.log_level import LogLevel  # pylint: disable=import-error


@pytest.fixture
def mock_logger():
    # Using the actual logger path from the downloader module
    with patch('app.src.services.youtube.downloader.logger', autospec=True) as mock_log:
        yield mock_log

@pytest.fixture
def mock_progress_callback():
    return MagicMock()

@pytest.fixture
def downloader(tmp_path, mock_logger, mock_progress_callback):
    # tmp_path is a pytest fixture providing a temporary directory unique to the test invocation
    # mock_logger is injected into the test function scope but not directly into YouTubeDownloader constructor
    print(f"DEBUG: mock_logger in fixture: id={id(mock_logger)}") 
    return YouTubeDownloader(
        upload_folder=str(tmp_path),  # Corrected argument name as per class __init__
        progress_callback=mock_progress_callback
        # Logger is not passed here, will need to be patched differently
    )


def test_youtube_downloader_initialization(downloader, tmp_path, mock_progress_callback):
    assert downloader.upload_folder == Path(tmp_path) # Ensure it's a Path object as in __init__
    assert downloader.progress_callback == mock_progress_callback
    assert downloader._last_percentage == 0


def test_handle_progress_status_not_downloading(downloader, mock_logger, mock_progress_callback):
    """Test that no action is taken if progress status is not 'downloading'."""
    progress_data = {'status': 'finished', 'total_bytes': 1000, 'downloaded_bytes': 1000}
    downloader._handle_progress(progress_data)
    mock_logger.log.assert_not_called()
    mock_progress_callback.assert_not_called()

def test_handle_progress_no_total_bytes(downloader, mock_logger, mock_progress_callback):
    """Test that no action is taken if total_bytes is missing or zero."""
    progress_data = {'status': 'downloading', 'downloaded_bytes': 100}
    downloader._handle_progress(progress_data)
    mock_logger.log.assert_not_called()
    mock_progress_callback.assert_not_called()

    progress_data_zero = {'status': 'downloading', 'total_bytes': 0, 'downloaded_bytes': 100}
    downloader._handle_progress(progress_data_zero)
    mock_logger.log.assert_not_called()
    mock_progress_callback.assert_not_called()


def test_handle_progress_logs_and_callbacks_at_intervals(downloader, mock_logger, mock_progress_callback):
    """Test logging and callback invocations at various progress percentages."""
    total_b = 1000
    downloader._last_percentage = 0 # Ensure starting from 0 for consistent testing

    # Test at 5% (no log, callback expected)
    progress_data_5 = {'status': 'downloading', 'total_bytes': total_b, 'downloaded_bytes': 50}
    downloader._handle_progress(progress_data_5)
    mock_logger.log.assert_not_called()
    mock_progress_callback.assert_called_once_with({
        'status': 'downloading', 'progress': 5,
        'downloaded_bytes': 50, 'total_bytes': total_b
    })
    mock_progress_callback.reset_mock()
    # _last_percentage should not update yet as 5 is not > 0 + 9
    assert downloader._last_percentage == 0 

    # Test at 10% (log and callback expected)
    progress_data_10 = {'status': 'downloading', 'total_bytes': total_b, 'downloaded_bytes': 100}
    downloader._handle_progress(progress_data_10)
    mock_logger.log.assert_called_once_with(LogLevel.INFO, "Download progress: 10%")
    mock_progress_callback.assert_called_once_with({
        'status': 'downloading', 'progress': 10,
        'downloaded_bytes': 100, 'total_bytes': total_b
    })
    mock_logger.reset_mock()
    mock_progress_callback.reset_mock()
    assert downloader._last_percentage == 10

    # Test at 15% (no log, callback expected, _last_percentage remains 10)
    progress_data_15 = {'status': 'downloading', 'total_bytes': total_b, 'downloaded_bytes': 150}
    downloader._handle_progress(progress_data_15)
    mock_logger.log.assert_not_called()
    mock_progress_callback.assert_called_once_with({
        'status': 'downloading', 'progress': 15,
        'downloaded_bytes': 150, 'total_bytes': total_b
    })
    mock_progress_callback.reset_mock()
    assert downloader._last_percentage == 10

    # Test at 20% (log and callback expected, _last_percentage updates to 20)
    progress_data_20 = {'status': 'downloading', 'total_bytes': total_b, 'downloaded_bytes': 200}
    downloader._handle_progress(progress_data_20)
    mock_logger.log.assert_called_once_with(LogLevel.INFO, "Download progress: 20%")
    mock_progress_callback.assert_called_once_with({
        'status': 'downloading', 'progress': 20,
        'downloaded_bytes': 200, 'total_bytes': total_b
    })
    assert downloader._last_percentage == 20

def test_handle_progress_uses_total_bytes_estimate(downloader, mock_logger, mock_progress_callback):
    """Test that total_bytes_estimate is used if total_bytes is zero."""
    downloader._last_percentage = 0 # Reset for this test
    progress_data = {
        'status': 'downloading',
        'total_bytes': 0, 
        'total_bytes_estimate': 500,
        'downloaded_bytes': 50 # This is 10% of 500
    }
    downloader._handle_progress(progress_data)
    mock_logger.log.assert_called_once_with(LogLevel.INFO, "Download progress: 10%")
    mock_progress_callback.assert_called_once_with({
        'status': 'downloading', 'progress': 10,
        'downloaded_bytes': 50, 'total_bytes': 500
    })
    assert downloader._last_percentage == 10


@pytest.fixture
def mock_yt_dlp_instances():
    # This fixture provides configured mock instances for yt_dlp.YoutubeDL context manager
    mock_info_instance = MagicMock(spec_set=['extract_info']) # Use spec_set for stricter mocking
    mock_download_instance = MagicMock(spec_set=['extract_info'])

    # The mock for the class itself, to be patched
    mock_YoutubeDL_class = MagicMock()
    # Configure what happens when yt_dlp.YoutubeDL() is called and used in a 'with' statement
    # __enter__ should return the instance, __exit__ handles cleanup
    # Ensure __enter__ returns a new mock each time if side_effect is a list of mocks
    mock_YoutubeDL_class.return_value.__enter__.side_effect = [mock_info_instance, mock_download_instance]
    # __exit__ must be a callable that accepts three arguments (exc_type, exc_val, exc_tb)
    mock_YoutubeDL_class.return_value.__exit__.return_value = False # Typical return for successful exit

    return {
        "class_mock": mock_YoutubeDL_class,
        "info_instance_mock": mock_info_instance,
        "download_instance_mock": mock_download_instance
    }


# Test for the download method
def test_download_single_video_no_chapters(downloader, tmp_path, mock_logger, mock_yt_dlp_instances):
    url = "http://example.com/video_single"
    video_title = "Test Video Single Title"
    video_id = "test_video_id_single"
    video_duration = 120
    # Corrected: Simulate the safe title generation from the downloader *exactly*
    safe_video_title = "".join([c if c.isalnum() or c in " -_" else "_" for c in video_title])

    # Configure mock return values for extract_info
    # First call (download=False for info gathering)
    mock_yt_dlp_instances['info_instance_mock'].extract_info.return_value = {
        'title': video_title,
        'id': video_id,
        'duration': video_duration,
        # No 'chapters', no 'entries' for a simple single video info call
    }
    # Second call (download=True for actual download)
    # This info is used by the downloader to build its final result dictionary.
    mock_yt_dlp_instances['download_instance_mock'].extract_info.return_value = {
        'title': video_title,
        'id': video_id,
        'duration': video_duration,
        'chapters': [], # yt-dlp might return empty chapters for a single file after processing
        'entries': []   # Or empty entries
    }

    # Patch yt_dlp.YoutubeDL within the downloader module for the scope of this test
    with patch('app.src.services.youtube.downloader.logger', new=mock_logger):
        with patch('app.src.services.youtube.downloader.yt_dlp.YoutubeDL', mock_yt_dlp_instances['class_mock']):
            result = downloader.download(url)

    # 1. Assert yt_dlp.YoutubeDL class was instantiated correctly
    # It's called twice, once for info, once for download.
    assert mock_yt_dlp_instances['class_mock'].call_count == 2
    
    expected_ydl_opts_info = {'quiet': True, 'no_warnings': True}
    # Construct the expected path for outtmpl and paths.home using tmp_path from the downloader fixture
    expected_playlist_folder_path_str = str(tmp_path / safe_video_title)
    expected_ydl_opts_download = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'outtmpl': str(Path(expected_playlist_folder_path_str) / '%(title)s.%(ext)s'),
        'split_chapters': True,
        'paths': {'home': expected_playlist_folder_path_str},
        'progress_hooks': [downloader._handle_progress], # Check the hook is present
        'force_overwrites': True,
        'quiet': True,
        'no_warnings': True,
        'logger': None, # yt-dlp's internal logger disabled
        'noprogress': True # yt-dlp's progress bar disabled, but hooks should still run
    }
    mock_yt_dlp_instances['class_mock'].assert_any_call(expected_ydl_opts_info)
    mock_yt_dlp_instances['class_mock'].assert_any_call(expected_ydl_opts_download)

    # Assert __enter__ and __exit__ were called for context management
    assert mock_yt_dlp_instances['class_mock'].return_value.__enter__.call_count == 2
    assert mock_yt_dlp_instances['class_mock'].return_value.__exit__.call_count == 2

    # 2. Assert extract_info was called correctly on the mock instances
    mock_yt_dlp_instances['info_instance_mock'].extract_info.assert_called_once_with(url, download=False)
    mock_yt_dlp_instances['download_instance_mock'].extract_info.assert_called_once_with(url, download=True)

    # 3. Assert folder creation (downloader uses tmp_path for upload_folder)
    expected_folder_path_obj = tmp_path / safe_video_title
    assert expected_folder_path_obj.exists()
    assert expected_folder_path_obj.is_dir()

    # 4. Assert the structure and content of the result dictionary
    # Based on the downloader's logic for single files without chapters
    expected_result_chapters = [{
        'title': video_title,
        'start_time': 0,
        'end_time': video_duration,
        'filename': f"{video_title}.mp3" # Filename generated by the downloader logic
    }]
    expected_result = {
        'title': video_title,
        'id': video_id,
        'folder': safe_video_title, # Ensure this uses the corrected safe_video_title
        'chapters': expected_result_chapters
    }
    assert result == expected_result

    # 5. Assert no critical errors were logged by the downloader's own logger
    # The download method logs errors only in its except block.
    error_logs = [c for c in mock_logger.log.call_args_list if c[0][0] == LogLevel.ERROR]
    assert not error_logs, f"Unexpected ERROR logs: {error_logs}"

def test_download_video_with_chapters(downloader, tmp_path, mock_logger, mock_yt_dlp_instances):
    url = "http://example.com/video_with_chapters"
    video_title = "Test Video With Chapters"
    video_id = "test_video_id_chapters"
    safe_video_title = "".join([c if c.isalnum() or c in " -_" else "_" for c in video_title])

    chapter1_title = "Chapter 1 Title"
    chapter2_title = "Chapter 2 Title With Filename"
    chapter2_filename = "Custom Chapter 2 Filename.mp3"

    raw_chapters_info = [
        {'title': chapter1_title, 'start_time': 0, 'end_time': 60},
        {'title': chapter2_title, 'start_time': 60, 'end_time': 120, 'filename': chapter2_filename}
    ]

    # Mock return for info gathering (download=False)
    mock_yt_dlp_instances['info_instance_mock'].extract_info.return_value = {
        'title': video_title,
        'id': video_id,
        'chapters': raw_chapters_info # Chapters present during info gathering
    }

    # Mock return for actual download (download=True)
    # yt-dlp might pass through the chapters if split_chapters is True
    mock_yt_dlp_instances['download_instance_mock'].extract_info.return_value = {
        'title': video_title,
        'id': video_id,
        'chapters': raw_chapters_info, # Assume chapters are returned after download processing
        'entries': []
    }

    with patch('app.src.services.youtube.downloader.logger', new=mock_logger):
        with patch('app.src.services.youtube.downloader.yt_dlp.YoutubeDL', mock_yt_dlp_instances['class_mock']):
            result = downloader.download(url)

    # Assertions similar to the single video test, adapted for chapters
    assert mock_yt_dlp_instances['class_mock'].call_count == 2
    mock_yt_dlp_instances['info_instance_mock'].extract_info.assert_called_once_with(url, download=False)
    mock_yt_dlp_instances['download_instance_mock'].extract_info.assert_called_once_with(url, download=True)

    expected_folder_path_obj = tmp_path / safe_video_title
    assert expected_folder_path_obj.exists()
    assert expected_folder_path_obj.is_dir()

    expected_chapters_result = [
        {
            'title': chapter1_title, 'start_time': 0, 'end_time': 60,
            'filename': f"{chapter1_title}.mp3" # Generated by downloader
        },
        {
            'title': chapter2_title, 'start_time': 60, 'end_time': 120,
            'filename': chapter2_filename # Provided in original chapter info
        }
    ]

    expected_result = {
        'title': video_title,
        'id': video_id,
        'folder': safe_video_title,
        'chapters': expected_chapters_result
    }
    assert result == expected_result

    error_logs = [c for c in mock_logger.log.call_args_list if c[0][0] == LogLevel.ERROR]
    assert not error_logs, f"Unexpected ERROR logs: {error_logs}"

def test_download_playlist_as_chapters(downloader, tmp_path, mock_logger, mock_yt_dlp_instances):
    url = "http://example.com/playlist"
    playlist_title = "Test Playlist Title"
    playlist_id = "test_playlist_id"
    safe_playlist_title = "".join([c if c.isalnum() or c in " -_" else "_" for c in playlist_title])

    entry1_title = "Playlist Entry 1"
    entry1_id = "entry1_video_id"
    entry2_title = "Playlist Entry 2"
    entry2_id = "entry2_video_id"

    playlist_entries = [
        {'title': entry1_title, 'id': entry1_id, 'duration': 180},
        {'title': entry2_title, 'id': entry2_id, 'duration': 240},
    ]

    # Mock return for info gathering (download=False)
    mock_yt_dlp_instances['info_instance_mock'].extract_info.return_value = {
        'title': playlist_title,
        'id': playlist_id,
        'entries': playlist_entries, # Key part for playlist detection
        'chapters': None # Explicitly no top-level chapters
    }

    # Mock return for actual download (download=True)
    # Assume yt-dlp returns a similar structure, downloader processes entries
    mock_yt_dlp_instances['download_instance_mock'].extract_info.return_value = {
        'title': playlist_title,
        'id': playlist_id,
        'entries': playlist_entries,
        'chapters': None
    }

    with patch('app.src.services.youtube.downloader.logger', new=mock_logger):
        with patch('app.src.services.youtube.downloader.yt_dlp.YoutubeDL', mock_yt_dlp_instances['class_mock']):
            result = downloader.download(url)

    # Assertions
    assert mock_yt_dlp_instances['class_mock'].call_count == 2
    mock_yt_dlp_instances['info_instance_mock'].extract_info.assert_called_once_with(url, download=False)
    mock_yt_dlp_instances['download_instance_mock'].extract_info.assert_called_once_with(url, download=True)

    expected_folder_path_obj = tmp_path / safe_playlist_title
    assert expected_folder_path_obj.exists()
    assert expected_folder_path_obj.is_dir()

    expected_chapters_result = [
        {
            'title': entry1_title, 'start_time': 0, 'end_time': 180,
            'filename': f"{entry1_title}.mp3"
        },
        {
            'title': entry2_title, 'start_time': 0, 'end_time': 240,
            'filename': f"{entry2_title}.mp3"
        }
    ]

    expected_result = {
        'title': playlist_title,
        'id': playlist_id,
        'folder': safe_playlist_title,
        'chapters': expected_chapters_result
    }
    assert result == expected_result

    log_method_calls = mock_logger.log.call_args_list
    # Temporary print for debugging
    print(f"DEBUG: In test_download_playlist_as_chapters, mock_logger.log.call_args_list = {log_method_calls}")

    expected_log_message = f"Playlist '{playlist_title}' (ID: {playlist_id}): No explicit chapters found. Processing {len(playlist_entries)} entries as individual chapters."
    found_debug_message = any(
        call_obj.args[0] == LogLevel.DEBUG and
        call_obj.args[1] == expected_log_message
        for call_obj in log_method_calls
    )
    assert found_debug_message, f"Expected log message '{expected_log_message}' not found. Actual calls: {log_method_calls}"

    error_logs_found = any(
        call_obj.args[0] == LogLevel.ERROR
        for call_obj in log_method_calls
    )
    assert not error_logs_found, f"Unexpected ERROR logs found: {[c.args[1] for c in log_method_calls if c.args[0] == LogLevel.ERROR]}"
