# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.

"""Mock NFC Hardware Implementation for Testing and Development."""

import asyncio
import time
from typing import Optional, Dict, Any
from rx.subject import Subject

from app.src.monitoring import get_logger
from app.src.monitoring.logging.log_level import LogLevel
from .nfc_hardware_interface import NFCHardwareInterface
from app.src.services.error.unified_error_decorator import handle_errors

logger = get_logger(__name__)


class MockNFCHardware(NFCHardwareInterface):
    """Mock implementation of NFC hardware for testing and development.

    This implementation simulates NFC tag detection using a timer-based approach
    and provides all the event mechanisms that the real hardware would provide.
    """

    def __init__(self):
        """Initialize the Mock NFC hardware."""
        self._tag_subject = Subject()
        self._running = False
        self._reader_task = None
        self._stop_event = asyncio.Event()
        self._scan_counter = 0
        self._last_simulated_tag = None
        self._simulation_cycle = 0

        logger.log(LogLevel.INFO, "✅ Mock NFC Hardware initialized")

    @property
    def tag_subject(self) -> Subject:
        """Get the RxPy Subject for tag detection events."""
        return self._tag_subject

    async def initialize(self) -> None:
        """Initialize the mock hardware (no-op for mock)."""
        logger.log(LogLevel.INFO, "🔧 Mock NFC Hardware initialized (no-op)")

    async def start_nfc_reader(self) -> None:
        """Start the mock NFC reader simulation."""
        if self._running:
            logger.log(LogLevel.WARNING, "⚠️ Mock NFC reader already running")
            return

        self._stop_event.clear()
        self._running = True
        self._reader_task = asyncio.create_task(self._simulate_nfc_scanning())
        logger.log(LogLevel.INFO, "🚀 Mock NFC Reader started - scanning for tags...")

    async def stop_nfc_reader(self) -> None:
        """Stop the mock NFC reader simulation."""
        if not self._running:
            return

        self._stop_event.set()
        self._running = False

        if self._reader_task and not self._reader_task.done():
            try:
                await asyncio.wait_for(self._reader_task, timeout=1.0)
            except asyncio.TimeoutError:
                self._reader_task.cancel()
                try:
                    await self._reader_task
                except asyncio.CancelledError:
                    pass

        logger.log(LogLevel.INFO, "⏹️ Mock NFC Reader stopped")

    def is_running(self) -> bool:
        """Check if the mock reader is running."""
        return self._running

    async def read_nfc(self) -> Optional[Dict[str, Any]]:
        """Simulate reading an NFC tag directly.

        This method simulates finding a tag occasionally for direct reads.
        """
        # Simulate finding a tag 20% of the time for direct reads
        if self._scan_counter % 5 == 0:
            tag_data = self._generate_mock_tag()
            logger.log(LogLevel.DEBUG, f"📱 Direct NFC read: {tag_data}")
            return tag_data
        return None

    def cleanup(self) -> None:
        """Clean up mock hardware resources."""
        if self._running:
            # Schedule stop for async cleanup
            asyncio.create_task(self.stop_nfc_reader())

        logger.log(LogLevel.INFO, "🧹 Mock NFC Hardware cleaned up")

    @handle_errors("_simulate_nfc_scanning")
    async def _simulate_nfc_scanning(self) -> None:
        """Main simulation loop for NFC tag detection."""
        logger.log(LogLevel.INFO, "🔄 Mock NFC scanning loop started")
        last_info_log = 0

        while not self._stop_event.is_set():
            self._scan_counter += 1
            self._simulation_cycle = (self._simulation_cycle + 1) % 100
            # Simulate tag detection every ~8-12 seconds with some randomness
            should_simulate_tag = self._simulation_cycle % 80 == 0 or (  # Every 8 seconds
                self._simulation_cycle % 120 == 0 and self._scan_counter % 3 == 0
            )  # Random extra detection
            if should_simulate_tag:
                await self._simulate_tag_detection()
            # Log status every 5 seconds to show activity
            now = time.time()
            if now - last_info_log > 5:
                logger.log(
                    LogLevel.INFO,
                    f"📡 Mock NFC: Waiting for tag... (cycle {self._simulation_cycle}, scans: {self._scan_counter})",
                )
                last_info_log = now
            # 100ms scan interval
            await asyncio.sleep(0.1)

    @handle_errors("_simulate_tag_detection")
    async def _simulate_tag_detection(self) -> None:
        """Simulate detecting an NFC tag and emit the event."""
        tag_data = self._generate_mock_tag()
        self._last_simulated_tag = tag_data

        logger.log(LogLevel.INFO, f"🏷️ Mock tag detected: {tag_data['uid']}")

        # Emit the tag detection event through the subject
        self._tag_subject.on_next(tag_data)
        logger.log(LogLevel.DEBUG, "📤 Tag detection event emitted successfully")

    def _generate_mock_tag(self) -> Dict[str, Any]:
        """Generate mock NFC tag data."""
        # Cycle through different mock tag IDs
        mock_tags = [
            "mock_tag_001",
            "mock_tag_002",
            "mock_tag_003",
            "test_nfc_tag",
            "demo_playlist_tag",
        ]

        tag_index = (self._scan_counter // 50) % len(mock_tags)
        tag_uid = mock_tags[tag_index]

        return {
            "uid": tag_uid,
            "present": True,
            "timestamp": time.time(),
            "scan_count": self._scan_counter,
            "mock_data": True,
            "hardware": "MockNFC",
        }

    # Additional method for manual tag simulation (for testing)
    def simulate_tag_manually(self, tag_uid: str = "manual_test_tag") -> None:
        """Manually trigger a tag detection event (for testing)."""
        if not self._running:
            logger.log(LogLevel.WARNING, "⚠️ Cannot simulate tag - Mock NFC reader not running")
            return

        tag_data = {
            "uid": tag_uid,
            "present": True,
            "timestamp": time.time(),
            "scan_count": self._scan_counter,
            "mock_data": True,
            "hardware": "MockNFC",
            "manual": True,
        }

        logger.log(LogLevel.INFO, f"🎯 Manually triggering tag detection: {tag_uid}")
        self._tag_subject.on_next(tag_data)
