import asyncio
import time
from typing import Optional

from rx.subject import Subject

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

from .nfc_hardware import NFCHardware

logger = ImprovedLogger(__name__)


class MockNFC(NFCHardware):
    """Mock implementation of NFCHardware for testing and non-hardware
    environments.

    Simulates NFC tag detection using a timer.
    """

    def __init__(self):
        self._tag_subject = Subject()
        self._running = False
        self._reader_task = None
        self._stop_event = asyncio.Event()
        self._scan_counter = 0
        logger.log(LogLevel.INFO, "Initialized Mock NFC Reader")

    async def initialize(self) -> None:
        """Méthode d'initialisation asynchrone, pour compatibilité avec
        PN532I2CNFC."""
        # Rien à initialiser pour le mock
        return

    async def _simulate_nfc_scanning(self) -> None:
        """Simulation de la boucle de lecture NFC."""
        logger.log(LogLevel.INFO, "Starting mock reader loop")
        last_info_log = 0

        while not self._stop_event.is_set():
            self._scan_counter += 1

            # Simuler un scan toutes les ~5 secondes
            if self._scan_counter % 50 == 0:
                result = await self.read_nfc()
                if result:
                    logger.log(LogLevel.INFO, f"Simulated tag detected: {result}")
            else:
                # Log INFO toutes les 5 secondes pour signaler l'attente
                now = time.time()
                if now - last_info_log > 5:
                    logger.log(LogLevel.INFO, "NFC reader waiting for tag scan...")
                    last_info_log = now

            # Attendre 100ms entre chaque cycle
            await asyncio.sleep(0.1)

    async def start_nfc_reader(self) -> None:
        """Démarre la simulation de lecture NFC."""
        self._stop_event.clear()
        self._running = True
        self._reader_task = asyncio.create_task(self._simulate_nfc_scanning())
        logger.log(LogLevel.INFO, "Started Mock NFC Reader")

    async def stop_nfc_reader(self) -> None:
        """Arrête la simulation de lecture NFC."""
        self._stop_event.set()
        if self._reader_task and not self._reader_task.done():
            try:
                await asyncio.wait_for(self._reader_task, timeout=1.0)
            except asyncio.TimeoutError:
                self._reader_task.cancel()
                try:
                    await self._reader_task
                except asyncio.CancelledError:
                    pass
        self._running = False
        logger.log(LogLevel.INFO, "Stopped Mock NFC Reader")

    async def read_nfc(self) -> Optional[bytes]:
        """Simule la lecture d'un tag NFC."""
        if time.time() % 5 < 0.1:
            mock_tag = bytes([0x04, 0xA0, 0x71, 0xA6, 0xDF, 0x61, 0x80])
            self._tag_subject.on_next(
                {
                    "uid": "04:A0:71:A6:DF:61:80",
                    "raw_uid": mock_tag,
                    "timestamp": time.time(),
                }
            )
            return mock_tag
        return None

    @property
    def tag_subject(self) -> Subject:
        return self._tag_subject

    async def cleanup(self) -> None:
        """Nettoie les ressources."""
        logger.log(LogLevel.INFO, "Cleaning up Mock NFC Reader")
        await self.stop_nfc_reader()
        logger.log(LogLevel.INFO, "Cleaned up Mock NFC Reader")
