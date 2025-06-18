from unittest.mock import patch

import pytest

from app.src.module.nfc.tag_detection_manager import TagDetectionManager


@pytest.fixture
def tag_detection_manager():
    """Create a TagDetectionManager instance for testing."""
    return TagDetectionManager(cooldown_period=0.1, removal_threshold=0.2)


@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_tag_detection_initial_state(tag_detection_manager):
    """Test the initial state of the TagDetectionManager."""
    assert tag_detection_manager._last_tag is None
    assert tag_detection_manager._tag_present is False
    assert tag_detection_manager._last_read_time == 0
    assert tag_detection_manager._last_no_tag_time == 0
    assert tag_detection_manager.cooldown_period == 0.1
    assert tag_detection_manager.removal_threshold == 0.2


@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_process_tag_detection_new_tag():
    """Test processing a new tag detection."""
    manager = TagDetectionManager(cooldown_period=0.1, removal_threshold=0.2)

    # Mock time.time() to return a fixed value
    with patch("time.time", return_value=100.0):
        # Simulate a new tag detection
        tag_id = "04:A2:B3:C4"

        # Process the tag
        result = manager.process_tag_detection(tag_id)

        # Verify the result
        assert result is not None
        assert result["uid"] == tag_id
        assert result["timestamp"] == 100.0
        assert result["new_detection"] is True
        assert manager._last_tag == tag_id
        assert manager._tag_present is True
        assert manager._last_read_time == 100.0


@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_process_tag_detection_same_tag():
    """Test processing the same tag multiple times."""
    manager = TagDetectionManager(cooldown_period=0.1, removal_threshold=0.2)

    # First detection at time 100.0
    with patch("time.time", return_value=100.0):
        tag_id = "04:A2:B3:C4"
        result1 = manager.process_tag_detection(tag_id)
        assert result1 is not None
        assert manager._tag_present is True

    # Second detection of the same tag immediately after (no cooldown passed)
    with patch("time.time", return_value=100.05):
        result2 = manager.process_tag_detection(tag_id)
        # Should not emit an event due to cooldown
        assert result2 is None
        assert manager._last_tag == tag_id
        assert manager._tag_present is True


@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_process_tag_absence():
    """Test processing tag absence."""
    manager = TagDetectionManager(cooldown_period=0.1, removal_threshold=0.2)

    # First detect a tag
    with patch("time.time", return_value=100.0):
        tag_id = "04:A2:B3:C4"
        manager.process_tag_detection(tag_id)
        assert manager._tag_present is True

    # Then process tag absence
    with patch("time.time", return_value=100.5):
        manager.process_tag_absence()
        assert manager._tag_present is False
        assert manager._last_no_tag_time == 100.5
        assert manager._last_tag == tag_id  # Last tag ID should still be stored


@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_process_tag_detection_new_tag_after_removal():
    """Test processing a new tag after a previous tag was removed."""
    manager = TagDetectionManager(cooldown_period=0.1, removal_threshold=0.2)

    # First detect a tag
    with patch("time.time", return_value=100.0):
        tag_id1 = "04:A2:B3:C4"
        manager.process_tag_detection(tag_id1)
        assert manager._tag_present is True

    # Process tag absence
    with patch("time.time", return_value=100.5):
        manager.process_tag_absence()
        assert manager._tag_present is False

    # Detect a different tag
    with patch("time.time", return_value=101.0):
        tag_id2 = "05:D6:E7:F8"
        result = manager.process_tag_detection(tag_id2)

        # Verify the result
        assert result is not None
        assert result["uid"] == tag_id2
        assert manager._last_tag == tag_id2
        assert manager._tag_present is True


@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_process_tag_detection_with_cooldown():
    """Test tag detection with cooldown period."""
    manager = TagDetectionManager(cooldown_period=0.2, removal_threshold=0.2)

    # First detection at time 100.0
    with patch("time.time", return_value=100.0):
        tag_id = "04:A2:B3:C4"
        result1 = manager.process_tag_detection(tag_id)
        assert result1 is not None
        assert manager._tag_present is True

    # Tag is removed
    with patch("time.time", return_value=100.1):
        manager.process_tag_absence()
        assert manager._tag_present is False

    # Tag is detected again before cooldown expires
    with patch("time.time", return_value=100.15):
        result2 = manager.process_tag_detection(tag_id)
        # Should not emit an event due to cooldown
        assert result2 is None

    # Tag is detected after cooldown expires
    with patch("time.time", return_value=100.3):
        result3 = manager.process_tag_detection(tag_id)
        # Should emit an event now
        assert result3 is not None
        assert result3["uid"] == tag_id
        assert manager._tag_present is True


@pytest.mark.timeout(5)  # Add timeout to prevent test hanging
def test_tag_subject_property():
    """Test the tag_subject property."""
    manager = TagDetectionManager(cooldown_period=0.1, removal_threshold=0.2)
    subject = manager.tag_subject

    # Verify the subject is accessible
    assert subject is not None
    assert subject == manager._tag_subject

    # Test that events are emitted to the subject
    events = []
    subject.subscribe(lambda x: events.append(x))

    with patch("time.time", return_value=100.0):
        tag_id = "04:A2:B3:C4"
        manager.process_tag_detection(tag_id)

    # Verify an event was emitted to the subject
    assert len(events) == 1
    assert events[0]["uid"] == tag_id
    assert events[0]["timestamp"] == 100.0
    assert events[0]["new_detection"] is True
