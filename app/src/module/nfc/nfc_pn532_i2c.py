from typing import Optional
import asyncio
import board
import busio
import time
from rx.subject import Subject
from adafruit_pn532.i2c import PN532_I2C

from app.src.helpers.exceptions import AppError, ErrorSeverity
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from .nfc_hardware import NFCHardware

logger = ImprovedLogger(__name__)

class PN532I2CNFC(NFCHardware):
    READ_TIMEOUT = 0.1
    RETRY_DELAY = 0.1
    TAG_COOLDOWN = 0.5
    MAX_ERRORS = 3

    def __init__(self, lock: asyncio.Lock) -> None:
        self._lock = lock
        self._pn532 = None
        self._tag_subject = Subject()
        self._stop_event = asyncio.Event()
        self._last_tag = None
        self._last_read_time = 0
        self._reader_task = None

    async def initialize(self) -> None:
        """Méthode d'initialisation asynchrone, à appeler après la création de l'instance"""
        try:
            await self._initialize_hardware()
            logger.log(LogLevel.INFO, "NFC I2C controller initialized")
        except Exception as e:
            logger.log(LogLevel.ERROR, "NFC initialization failed", exc_info=e)
            raise AppError.hardware_error(
                message="Failed to initialize NFC controller",
                component="nfc",
                operation="init",
                details={"error": str(e)},
                severity=ErrorSeverity.HIGH
            )

    async def _initialize_hardware(self) -> None:
        try:
            async with self._lock:
                i2c = busio.I2C(board.SCL, board.SDA)
                self._pn532 = PN532_I2C(i2c, debug=False)
                ic, ver, rev, support = self._pn532.firmware_version
                logger.log(LogLevel.INFO, f"Found PN532 with firmware version: {ic} {ver}.{rev} - {support}")
                self._pn532.SAM_configuration()
        except Exception as e:
            raise AppError.hardware_error(
                message="Failed to initialize NFC hardware",
                component="nfc",
                operation="init_hardware",
                details={"error": str(e)},
                severity=ErrorSeverity.HIGH
            )

    async def read_nfc(self) -> Optional[str]:
        if not self._pn532:
            return None

        try:
            async with self._lock:
                uid = self._pn532.read_passive_target(timeout=self.READ_TIMEOUT)
                if not uid:
                    return None

                return await self._process_tag(uid)

        except (RuntimeError, OSError):
            return None

        except Exception as e:
            if not str(e).startswith("No card") and "timeout" not in str(e).lower():
                logger.log(LogLevel.ERROR, "NFC read error", exc_info=e)
            return None

    async def _process_tag(self, uid: bytes) -> Optional[str]:
        uid_string = ':'.join([hex(i)[2:].zfill(2) for i in uid])
        current_time = time.time()

        if uid_string != self._last_tag or (current_time - self._last_read_time >= self.TAG_COOLDOWN):
            self._last_tag = uid_string
            self._last_read_time = current_time

            tag_data = {
                'uid': uid_string,
                'timestamp': current_time
            }

            logger.log(LogLevel.INFO, f"Emitting tag data: {tag_data}")
            self._tag_subject.on_next(tag_data)
            return uid_string

        return None

    async def _nfc_reader_loop(self) -> None:
        logger.log(LogLevel.INFO, "Starting reader loop")
        error_count = 0
        last_info_log = 0

        while not self._stop_event.is_set():
            try:
                if error_count >= self.MAX_ERRORS:
                    logger.log(LogLevel.WARNING, "Max errors reached, reinitializing hardware")
                    await self._initialize_hardware()
                    error_count = 0

                # Log l'état de la lecture
                result = await self.read_nfc()
                if result:
                    logger.log(LogLevel.INFO, f"Successfully read tag: {result}")
                    error_count = 0
                else:
                    logger.log(LogLevel.DEBUG, "No tag detected in this cycle")
                    # Log INFO toutes les 5 secondes pour signaler l'attente
                    now = time.time()
                    if now - last_info_log > 5:
                        logger.log(LogLevel.INFO, "NFC reader waiting for tag scan...")
                        last_info_log = now

                await asyncio.sleep(self.RETRY_DELAY)

            except Exception as e:
                error_count += 1
                logger.log(LogLevel.ERROR, f"Reader loop error #{error_count}: {str(e)}")
                await asyncio.sleep(min(2 ** error_count, 10))

    async def start_nfc_reader(self) -> None:
        # Reset l'événement stop si nécessaire
        self._stop_event.clear()
        # Créer une nouvelle tâche pour la boucle de lecture
        self._reader_task = asyncio.create_task(self._nfc_reader_loop())
        logger.log(LogLevel.INFO, "Reader started")

    async def stop_nfc_reader(self) -> None:
        # Signaler l'arrêt
        self._stop_event.set()
        # Annuler la tâche si elle existe
        if self._reader_task and not self._reader_task.done():
            try:
                # Laisser le temps à la boucle de se terminer proprement
                await asyncio.wait_for(self._reader_task, timeout=1.0)
            except asyncio.TimeoutError:
                # Annuler la tâche si elle ne s'arrête pas à temps
                self._reader_task.cancel()
                try:
                    await self._reader_task
                except asyncio.CancelledError:
                    pass
        logger.log(LogLevel.INFO, "Reader stopped")

    async def cleanup(self) -> None:
        try:
            logger.log(LogLevel.INFO, "Starting cleanup")
            await self.stop_nfc_reader()

            async with self._lock:
                if self._pn532:
                    self._pn532 = None
                    logger.log(LogLevel.INFO, "Hardware released")

        except Exception as e:
            raise AppError.hardware_error(
                message="Failed to cleanup NFC device",
                component="nfc",
                operation="cleanup",
                details={"error": str(e)},
                severity=ErrorSeverity.HIGH
            )

    @property
    def tag_subject(self) -> Subject:
        return self._tag_subject
