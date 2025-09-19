# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""
Comprehensive tests for NFC Infrastructure layer following DDD principles.

Tests cover:
- NfcHardwareAdapter protocol compliance
- MockNfcHardwareAdapter implementation
- Legacy handler integration
- Error handling and resilience
- Protocol contract adherence
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from app.src.infrastructure.nfc.adapters.nfc_hardware_adapter import (
    NfcHardwareAdapter,
    MockNfcHardwareAdapter
)
from app.src.domain.nfc.value_objects.tag_identifier import TagIdentifier
from app.src.domain.nfc.protocols.nfc_hardware_protocol import NfcHardwareProtocol


class MockLegacyNfcHandler:
    """Mock legacy NFC handler for testing."""
    
    def __init__(self):
        self.is_started = False
        self.connection_status = True
        self.should_fail_start = False
        self.should_fail_stop = False
        self.tag_subject = Mock()
        
    async def start_reading(self):
        if self.should_fail_start:
            raise Exception("Legacy handler start failure")
        self.is_started = True
    
    async def stop_reading(self):
        if self.should_fail_stop:
            raise Exception("Legacy handler stop failure")
        self.is_started = False
    
    def get_status(self):
        return {
            "connected": self.connection_status,
            "active": self.is_started,
            "hardware": "PN532"
        }
    
    def is_connected(self):
        return self.connection_status


class TestNfcHardwareAdapter:
    """Test NfcHardwareAdapter protocol compliance and functionality."""
    
    @pytest.fixture
    def mock_legacy_handler(self):
        """Mock legacy NFC handler fixture."""
        return MockLegacyNfcHandler()
    
    @pytest.fixture
    def adapter(self, mock_legacy_handler):
        """NFC hardware adapter fixture with mock legacy handler."""
        return NfcHardwareAdapter(mock_legacy_handler)
    
    @pytest.fixture
    def adapter_no_legacy(self):
        """NFC hardware adapter fixture without legacy handler."""
        return NfcHardwareAdapter()
    
    def test_adapter_implements_protocol(self, adapter):
        """Test that adapter implements NfcHardwareProtocol."""
        assert isinstance(adapter, NfcHardwareProtocol)
    
    def test_adapter_initialization_with_legacy_handler(self, mock_legacy_handler):
        """Test adapter initialization with legacy handler."""
        adapter = NfcHardwareAdapter(mock_legacy_handler)
        
        assert adapter._legacy_handler is mock_legacy_handler
        assert not adapter._detecting
        assert adapter._tag_detected_callback is None
        assert adapter._tag_removed_callback is None
        
        # Should subscribe to legacy handler events
        mock_legacy_handler.tag_subject.subscribe.assert_called_once()
    
    def test_adapter_initialization_without_legacy_handler(self):
        """Test adapter initialization without legacy handler."""
        adapter = NfcHardwareAdapter()
        
        assert adapter._legacy_handler is None
        assert not adapter._detecting
    
    @pytest.mark.asyncio
    async def test_start_detection_with_legacy_handler(self, adapter, mock_legacy_handler):
        """Test starting detection with legacy handler."""
        await adapter.start_detection()
        
        assert adapter.is_detecting()
        assert mock_legacy_handler.is_started
    
    @pytest.mark.asyncio
    async def test_start_detection_without_legacy_handler(self, adapter_no_legacy):
        """Test starting detection without legacy handler."""
        await adapter_no_legacy.start_detection()
        
        assert adapter_no_legacy.is_detecting()
    
    @pytest.mark.asyncio
    async def test_start_detection_legacy_handler_failure(self, mock_legacy_handler):
        """Test start detection when legacy handler fails."""
        mock_legacy_handler.should_fail_start = True
        adapter = NfcHardwareAdapter(mock_legacy_handler)
        
        with pytest.raises(Exception, match="Legacy handler start failure"):
            await adapter.start_detection()
        
        assert not adapter.is_detecting()
    
    @pytest.mark.asyncio
    async def test_stop_detection_with_legacy_handler(self, adapter, mock_legacy_handler):
        """Test stopping detection with legacy handler."""
        await adapter.start_detection()
        assert adapter.is_detecting()
        
        await adapter.stop_detection()
        
        assert not adapter.is_detecting()
        assert not mock_legacy_handler.is_started
    
    @pytest.mark.asyncio
    async def test_stop_detection_without_legacy_handler(self, adapter_no_legacy):
        """Test stopping detection without legacy handler."""
        await adapter_no_legacy.start_detection()
        assert adapter_no_legacy.is_detecting()
        
        await adapter_no_legacy.stop_detection()
        
        assert not adapter_no_legacy.is_detecting()
    
    @pytest.mark.asyncio
    async def test_stop_detection_legacy_handler_failure(self, adapter, mock_legacy_handler):
        """Test stop detection when legacy handler fails."""
        await adapter.start_detection()
        mock_legacy_handler.should_fail_stop = True
        
        # Should not raise exception, just log warning
        await adapter.stop_detection()
        
        # Should still mark as not detecting
        assert not adapter.is_detecting()
    
    def test_is_detecting_initial_state(self, adapter):
        """Test is_detecting initial state."""
        assert not adapter.is_detecting()
    
    @pytest.mark.asyncio
    async def test_is_detecting_after_start(self, adapter):
        """Test is_detecting after starting detection."""
        await adapter.start_detection()
        assert adapter.is_detecting()
    
    @pytest.mark.asyncio
    async def test_is_detecting_after_stop(self, adapter):
        """Test is_detecting after stopping detection."""
        await adapter.start_detection()
        await adapter.stop_detection()
        assert not adapter.is_detecting()
    
    def test_set_tag_detected_callback(self, adapter):
        """Test setting tag detected callback."""
        callback = Mock()
        adapter.set_tag_detected_callback(callback)
        
        assert adapter._tag_detected_callback is callback
    
    def test_set_tag_removed_callback(self, adapter):
        """Test setting tag removed callback."""
        callback = Mock()
        adapter.set_tag_removed_callback(callback)
        
        assert adapter._tag_removed_callback is callback
    
    @pytest.mark.asyncio
    async def test_get_hardware_status_with_legacy_handler(self, adapter, mock_legacy_handler):
        """Test getting hardware status with legacy handler."""
        status = await adapter.get_hardware_status()
        
        expected_keys = {"detecting", "adapter_type", "legacy_handler_available", "legacy_status"}
        assert set(status.keys()) >= expected_keys
        
        assert status["detecting"] is False  # Initially not detecting
        assert status["adapter_type"] == "NfcHardwareAdapter"
        assert status["legacy_handler_available"] is True
        assert status["legacy_status"]["connected"] is True
    
    @pytest.mark.asyncio
    async def test_get_hardware_status_without_legacy_handler(self, adapter_no_legacy):
        """Test getting hardware status without legacy handler."""
        status = await adapter_no_legacy.get_hardware_status()
        
        expected_keys = {"detecting", "adapter_type", "legacy_handler_available"}
        assert set(status.keys()) >= expected_keys
        
        assert status["detecting"] is False
        assert status["adapter_type"] == "NfcHardwareAdapter"
        assert status["legacy_handler_available"] is False
        assert "legacy_status" not in status
    
    @pytest.mark.asyncio
    async def test_get_hardware_status_legacy_error(self, mock_legacy_handler):
        """Test hardware status when legacy handler throws error."""
        # Remove get_status method to cause error
        del mock_legacy_handler.get_status
        mock_legacy_handler.is_connected = Mock(side_effect=Exception("Connection error"))
        
        adapter = NfcHardwareAdapter(mock_legacy_handler)
        status = await adapter.get_hardware_status()
        
        assert "legacy_status_error" in status
        assert "Connection error" in status["legacy_status_error"]
    
    def test_on_legacy_tag_event_dict_format(self, adapter):
        """Test legacy tag event handling with dictionary format."""
        callback = Mock()
        adapter.set_tag_detected_callback(callback)
        
        tag_data = {"uid": "1234abcd", "type": "MIFARE"}
        adapter._on_legacy_tag_event(tag_data)
        
        callback.assert_called_once()
        called_tag = callback.call_args[0][0]
        assert isinstance(called_tag, TagIdentifier)
        assert called_tag.uid == "1234abcd"
    
    def test_on_legacy_tag_event_string_format(self, adapter):
        """Test legacy tag event handling with string format."""
        callback = Mock()
        adapter.set_tag_detected_callback(callback)
        
        adapter._on_legacy_tag_event("5678efgh")
        
        callback.assert_called_once()
        called_tag = callback.call_args[0][0]
        assert isinstance(called_tag, TagIdentifier)
        assert called_tag.uid == "5678efgh"
    
    def test_on_legacy_tag_event_various_uid_keys(self, adapter):
        """Test legacy tag event handling with various UID key formats."""
        callback = Mock()
        adapter.set_tag_detected_callback(callback)
        
        test_cases = [
            {"tag_id": "1111aaaa"},
            {"id": "2222bbbb"},
            {"data": "3333cccc"}
        ]
        
        for tag_data in test_cases:
            adapter._on_legacy_tag_event(tag_data)
        
        assert callback.call_count == len(test_cases)
        
        # Check all tags were processed correctly
        call_args = [call[0][0] for call in callback.call_args_list]
        expected_uids = ["1111aaaa", "2222bbbb", "3333cccc"]
        actual_uids = [tag.uid for tag in call_args]
        
        assert actual_uids == expected_uids
    
    def test_on_legacy_tag_event_missing_uid(self, adapter):
        """Test legacy tag event handling with missing UID."""
        callback = Mock()
        adapter.set_tag_detected_callback(callback)
        
        # Tag data without UID
        tag_data = {"type": "MIFARE", "size": 1024}
        adapter._on_legacy_tag_event(tag_data)
        
        # Callback should not be called
        callback.assert_not_called()
    
    def test_on_legacy_tag_event_no_callback_set(self, adapter):
        """Test legacy tag event handling when no callback is set."""
        # Should not crash when no callback is set
        tag_data = {"uid": "1234abcd"}
        adapter._on_legacy_tag_event(tag_data)
        
        # No assertion needed - test passes if no exception
    
    def test_on_legacy_tag_event_invalid_uid(self, adapter):
        """Test legacy tag event handling with invalid UID."""
        callback = Mock()
        adapter.set_tag_detected_callback(callback)
        
        # Invalid UID (too short)
        tag_data = {"uid": "ab"}
        adapter._on_legacy_tag_event(tag_data)
        
        # Callback should not be called due to TagIdentifier validation
        callback.assert_not_called()
    
    def test_inject_test_tag_success(self, adapter):
        """Test successful test tag injection."""
        callback = Mock()
        adapter.set_tag_detected_callback(callback)
        
        adapter.inject_test_tag("1234abcd")
        
        callback.assert_called_once()
        called_tag = callback.call_args[0][0]
        assert isinstance(called_tag, TagIdentifier)
        assert called_tag.uid == "1234abcd"
    
    def test_inject_test_tag_invalid_uid(self, adapter):
        """Test test tag injection with invalid UID."""
        callback = Mock()
        adapter.set_tag_detected_callback(callback)
        
        # Should handle invalid UID gracefully
        adapter.inject_test_tag("xx")  # Too short
        
        callback.assert_not_called()
    
    def test_inject_test_tag_no_callback(self, adapter):
        """Test test tag injection when no callback is set."""
        # Should not crash when no callback is set
        adapter.inject_test_tag("1234abcd")
        
        # No assertion needed - test passes if no exception
    
    @pytest.mark.asyncio
    async def test_legacy_handler_with_start_method(self):
        """Test adapter with legacy handler that has 'start' method instead of 'start_reading'."""
        legacy_handler = Mock()
        legacy_handler.start = AsyncMock()
        legacy_handler.stop = AsyncMock()
        legacy_handler.tag_subject = Mock()
        
        adapter = NfcHardwareAdapter(legacy_handler)
        
        await adapter.start_detection()
        legacy_handler.start.assert_called_once()
        
        await adapter.stop_detection()
        legacy_handler.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_legacy_handler_without_methods(self):
        """Test adapter with legacy handler that lacks start/stop methods."""
        legacy_handler = Mock()
        legacy_handler.tag_subject = Mock()
        # No start_reading or start methods
        
        adapter = NfcHardwareAdapter(legacy_handler)
        
        # Should not crash when methods are missing
        await adapter.start_detection()
        assert adapter.is_detecting()
        
        await adapter.stop_detection()
        assert not adapter.is_detecting()
    
    def test_legacy_handler_without_tag_subject(self):
        """Test adapter with legacy handler that lacks tag_subject."""
        legacy_handler = Mock()
        # No tag_subject attribute
        
        adapter = NfcHardwareAdapter(legacy_handler)
        
        # Should initialize without subscribing
        assert adapter._legacy_handler is legacy_handler


class TestMockNfcHardwareAdapter:
    """Test MockNfcHardwareAdapter implementation."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Mock NFC hardware adapter fixture."""
        return MockNfcHardwareAdapter()
    
    def test_mock_adapter_implements_protocol(self, mock_adapter):
        """Test that mock adapter implements NfcHardwareProtocol."""
        assert isinstance(mock_adapter, NfcHardwareProtocol)
    
    def test_mock_adapter_initialization(self, mock_adapter):
        """Test mock adapter initialization."""
        assert not mock_adapter._detecting
        assert mock_adapter._tag_detected_callback is None
        assert mock_adapter._tag_removed_callback is None
    
    @pytest.mark.asyncio
    async def test_mock_start_detection(self, mock_adapter):
        """Test mock detection start."""
        await mock_adapter.start_detection()
        assert mock_adapter.is_detecting()
    
    @pytest.mark.asyncio
    async def test_mock_stop_detection(self, mock_adapter):
        """Test mock detection stop."""
        await mock_adapter.start_detection()
        await mock_adapter.stop_detection()
        assert not mock_adapter.is_detecting()
    
    def test_mock_set_callbacks(self, mock_adapter):
        """Test setting callbacks on mock adapter."""
        detected_callback = Mock()
        removed_callback = Mock()
        
        mock_adapter.set_tag_detected_callback(detected_callback)
        mock_adapter.set_tag_removed_callback(removed_callback)
        
        assert mock_adapter._tag_detected_callback is detected_callback
        assert mock_adapter._tag_removed_callback is removed_callback
    
    @pytest.mark.asyncio
    async def test_mock_get_hardware_status(self, mock_adapter):
        """Test mock hardware status."""
        status = await mock_adapter.get_hardware_status()
        
        expected_keys = {"detecting", "adapter_type", "mock"}
        assert set(status.keys()) >= expected_keys
        
        assert status["detecting"] is False  # Initially not detecting
        assert status["adapter_type"] == "MockNfcHardwareAdapter"
        assert status["mock"] is True
    
    def test_mock_simulate_tag_detection(self, mock_adapter):
        """Test mock tag detection simulation."""
        callback = Mock()
        mock_adapter.set_tag_detected_callback(callback)
        
        mock_adapter.simulate_tag_detection("1234abcd")
        
        callback.assert_called_once()
        called_tag = callback.call_args[0][0]
        assert isinstance(called_tag, TagIdentifier)
        assert called_tag.uid == "1234abcd"
    
    def test_mock_simulate_tag_detection_no_callback(self, mock_adapter):
        """Test mock tag detection simulation without callback."""
        # Should not crash when no callback is set
        mock_adapter.simulate_tag_detection("1234abcd")
    
    def test_mock_simulate_tag_removal(self, mock_adapter):
        """Test mock tag removal simulation."""
        callback = Mock()
        mock_adapter.set_tag_removed_callback(callback)
        
        mock_adapter.simulate_tag_removal()
        
        callback.assert_called_once()
    
    def test_mock_simulate_tag_removal_no_callback(self, mock_adapter):
        """Test mock tag removal simulation without callback."""
        # Should not crash when no callback is set
        mock_adapter.simulate_tag_removal()


class TestNfcHardwareAdapterIntegration:
    """Test NfcHardwareAdapter integration scenarios."""
    
    def test_adapter_protocol_contract_compliance(self):
        """Test that adapter meets all protocol contract requirements."""
        adapter = NfcHardwareAdapter()
        
        # Check all required methods exist
        required_methods = [
            'start_detection', 'stop_detection', 'is_detecting',
            'set_tag_detected_callback', 'set_tag_removed_callback',
            'get_hardware_status'
        ]
        
        for method_name in required_methods:
            assert hasattr(adapter, method_name)
            assert callable(getattr(adapter, method_name))
    
    @pytest.mark.asyncio
    async def test_adapter_detection_lifecycle(self, mock_legacy_handler):
        """Test complete detection lifecycle."""
        adapter = NfcHardwareAdapter(mock_legacy_handler)
        
        # Initial state
        assert not adapter.is_detecting()
        
        # Start detection
        await adapter.start_detection()
        assert adapter.is_detecting()
        assert mock_legacy_handler.is_started
        
        # Stop detection
        await adapter.stop_detection()
        assert not adapter.is_detecting()
        assert not mock_legacy_handler.is_started
    
    def test_adapter_callback_integration(self, mock_legacy_handler):
        """Test callback integration with legacy handler."""
        adapter = NfcHardwareAdapter(mock_legacy_handler)
        
        detected_tags = []
        removed_count = 0
        
        def on_tag_detected(tag: TagIdentifier):
            detected_tags.append(tag.uid)
        
        def on_tag_removed():
            nonlocal removed_count
            removed_count += 1
        
        adapter.set_tag_detected_callback(on_tag_detected)
        adapter.set_tag_removed_callback(on_tag_removed)
        
        # Simulate legacy events
        adapter._on_legacy_tag_event({"uid": "1111aaaa"})
        adapter._on_legacy_tag_event("2222bbbb")
        
        assert detected_tags == ["1111aaaa", "2222bbbb"]
    
    @pytest.mark.asyncio
    async def test_adapter_error_resilience(self):
        """Test adapter resilience to various error conditions."""
        # Test with None legacy handler
        adapter1 = NfcHardwareAdapter(None)
        await adapter1.start_detection()
        await adapter1.stop_detection()
        
        # Test with mock that raises exceptions
        failing_handler = Mock()
        failing_handler.start_reading = AsyncMock(side_effect=Exception("Hardware error"))
        failing_handler.tag_subject = Mock()
        
        adapter2 = NfcHardwareAdapter(failing_handler)
        
        with pytest.raises(Exception, match="Hardware error"):
            await adapter2.start_detection()
    
    def test_adapter_tag_event_formats(self):
        """Test adapter handling of various tag event formats."""
        adapter = NfcHardwareAdapter()
        detected_tags = []
        
        def on_tag_detected(tag: TagIdentifier):
            detected_tags.append(tag.uid)
        
        adapter.set_tag_detected_callback(on_tag_detected)
        
        # Test various formats
        test_events = [
            {"uid": "1234abcd"},
            {"tag_id": "5678efgh"},
            {"id": "9abc defg"},  # With spaces
            {"data": "12:34:AB:CD"},  # With colons
            "direct_string_uid",
            123456789  # Numeric
        ]
        
        for event in test_events:
            try:
                adapter._on_legacy_tag_event(event)
            except Exception:
                # Some formats may cause validation errors
                pass
        
        # At least some should succeed
        assert len(detected_tags) > 0
    
    @pytest.mark.asyncio
    async def test_adapter_concurrent_operations(self):
        """Test adapter behavior under concurrent operations."""
        adapter = NfcHardwareAdapter()
        
        # Concurrent start/stop operations
        tasks = [
            adapter.start_detection(),
            adapter.stop_detection(),
            adapter.start_detection(),
            adapter.get_hardware_status()
        ]
        
        # Should handle concurrent operations gracefully
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # No exceptions should be raised
        for result in results:
            assert not isinstance(result, Exception)
        
        # Final state should be consistent
        status = await adapter.get_hardware_status()
        assert isinstance(status["detecting"], bool)
    
    def test_adapter_multiple_callback_registrations(self):
        """Test behavior when callbacks are registered multiple times."""
        adapter = NfcHardwareAdapter()
        
        callback1 = Mock()
        callback2 = Mock()
        
        # Register first callback
        adapter.set_tag_detected_callback(callback1)
        
        # Register second callback (should replace first)
        adapter.set_tag_detected_callback(callback2)
        
        # Simulate tag detection
        adapter._on_legacy_tag_event("1234abcd")
        
        # Only second callback should be called
        callback1.assert_not_called()
        callback2.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_adapter_status_consistency(self):
        """Test that adapter status remains consistent."""
        adapter = NfcHardwareAdapter()
        
        # Check initial status
        status1 = await adapter.get_hardware_status()
        assert not status1["detecting"]
        
        # Start detection
        await adapter.start_detection()
        status2 = await adapter.get_hardware_status()
        assert status2["detecting"]
        
        # Stop detection
        await adapter.stop_detection()
        status3 = await adapter.get_hardware_status()
        assert not status3["detecting"]
        
        # All statuses should have consistent structure
        common_keys = {"detecting", "adapter_type", "legacy_handler_available"}
        for status in [status1, status2, status3]:
            assert set(status.keys()) >= common_keys