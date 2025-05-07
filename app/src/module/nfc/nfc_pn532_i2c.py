from typing import Optional
import asyncio
import board
import busio
import time
from rx.subject import Subject
from adafruit_pn532.i2c import PN532_I2C

from app.src.helpers.exceptions import AppError, ErrorSeverity
from app.src.helpers.error_handler import ErrorHandler
from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.config.nfc_config import NFCConfig
from .nfc_hardware import NFCHardware
from .tag_detection_manager import TagDetectionManager

logger = ImprovedLogger(__name__)

class PN532I2CNFC(NFCHardware):
    """PN532 NFC hardware implementation using I2C communication.
    
    This class handles the low-level communication with the PN532 NFC reader
    via I2C, while delegating tag detection logic to the TagDetectionManager.
    """

    def __init__(self, lock: asyncio.Lock, config: Optional[NFCConfig] = None) -> None:
        """
        Initialize the PN532 NFC reader with I2C communication.
        
        Args:
            lock: Asyncio lock for thread-safe hardware access
            config: Optional NFC configuration parameters
        """
        self._lock = lock
        self._pn532 = None
        self._config = config or NFCConfig()  # Use default if none provided
        self._stop_event = asyncio.Event()
        self._reader_task = None
        
        # Create tag detection manager with configuration parameters
        self._tag_manager = TagDetectionManager(
            cooldown_period=self._config.tag_cooldown,
            removal_threshold=self._config.tag_removal_threshold
        )

    async def initialize(self) -> None:
        """
        Asynchronous initialization method, to be called after instance creation.
        
        Initializes the hardware and prepares the NFC reader for operation.
        """
        try:
            await self._initialize_hardware()
            logger.log(LogLevel.INFO, "NFC I2C controller initialized")
        except Exception as e:
            logger.log(LogLevel.ERROR, "NFC initialization failed", exc_info=e)
            raise ErrorHandler.create_app_error(
                error=e,
                message="Failed to initialize NFC controller",
                component="nfc",
                operation="init",
                severity=ErrorSeverity.HIGH
            )

    async def _initialize_hardware(self) -> None:
        """
        Initialize the NFC hardware components.
        
        Sets up the I2C communication and configures the PN532 chip.
        """
        try:
            async with self._lock:
                i2c = busio.I2C(board.SCL, board.SDA)
                self._pn532 = PN532_I2C(i2c, debug=False)
                ic, ver, rev, support = self._pn532.firmware_version
                logger.log(LogLevel.INFO, f"Found PN532 with firmware version: {ic} {ver}.{rev} - {support}")
                self._pn532.SAM_configuration()
        except Exception as e:
            raise ErrorHandler.create_app_error(
                error=e,
                message="Failed to initialize NFC hardware",
                component="nfc",
                operation="init_hardware",
                severity=ErrorSeverity.HIGH
            )

    async def read_nfc(self) -> Optional[str]:
        """
        Read NFC tag from the hardware.
        
        Returns:
            The UID string of the detected tag, or None if no tag is present
        """
        if not self._pn532:
            return None

        try:
            async with self._lock:
                uid = self._pn532.read_passive_target(timeout=self._config.read_timeout)
                
                # If no tag is detected
                if not uid:
                    # Process tag absence in the detection manager
                    self._tag_manager.process_tag_absence()
                    return None

                # A tag is detected, process it
                uid_string = ':'.join([f'{i:02X}' for i in uid])
                tag_data = self._tag_manager.process_tag_detection(uid_string)
                
                # Return the UID if an event was emitted
                if tag_data:
                    return uid_string
                    
                return None

        except (RuntimeError, OSError):
            # Consider as tag absence
            self._tag_manager.process_tag_absence()
            return None

        except Exception as e:
            if not str(e).startswith("No card") and "timeout" not in str(e).lower():
                ErrorHandler.log_error(e, "NFC read error")
            # Consider as tag absence in case of error
            self._tag_manager.process_tag_absence()
            return None

    async def _nfc_reader_loop(self) -> None:
        """
        Main loop for NFC tag reading.
        
        Continuously polls the NFC hardware for tag presence and handles errors.
        """
        logger.log(LogLevel.INFO, "Starting reader loop")
        error_count = 0
        last_info_log = 0

        while not self._stop_event.is_set():
            try:
                if error_count >= self._config.max_errors:
                    logger.log(LogLevel.WARNING, "Max errors reached, reinitializing hardware")
                    await self._initialize_hardware()
                    error_count = 0

                # Log the reading state
                result = await self.read_nfc()
                if result:
                    logger.log(LogLevel.INFO, f"Successfully read tag: {result}")
                    error_count = 0
                else:
                    logger.log(LogLevel.DEBUG, "No tag detected in this cycle")
                    # Log INFO every 5 seconds to signal waiting
                    now = time.time()
                    if now - last_info_log > 5:
                        logger.log(LogLevel.INFO, "NFC reader waiting for tag scan...")
                        last_info_log = now

                await asyncio.sleep(self._config.retry_delay)

            except Exception as e:
                error_count += 1
                ErrorHandler.log_error(e, f"Reader loop error #{error_count}")
                await asyncio.sleep(min(2 ** error_count, 10))

    async def start_nfc_reader(self) -> None:
        """
        Start the NFC reader loop.
        
        Creates an asyncio task that continuously polls for NFC tags.
        """
        # Reset the stop event if necessary
        self._stop_event.clear()
        # Create a new task for the reading loop
        self._reader_task = asyncio.create_task(self._nfc_reader_loop())
        logger.log(LogLevel.INFO, "Reader started")

    async def stop_nfc_reader(self) -> None:
        """
        Stop the NFC reader loop.
        
        Signals the reader loop to stop and cancels the task if necessary.
        """
        # Signal to stop
        self._stop_event.set()
        # Cancel the task if it exists
        if self._reader_task and not self._reader_task.done():
            try:
                # Give time for the loop to terminate properly
                await asyncio.wait_for(self._reader_task, timeout=1.0)
            except asyncio.TimeoutError:
                # Cancel the task if it doesn't stop in time
                self._reader_task.cancel()
                try:
                    await self._reader_task
                except asyncio.CancelledError:
                    pass
        logger.log(LogLevel.INFO, "Reader stopped")

    async def cleanup(self) -> None:
        """
        Clean up resources used by the NFC reader.
        
        Stops the reader loop and releases hardware resources.
        """
        try:
            logger.log(LogLevel.INFO, "Starting cleanup")
            await self.stop_nfc_reader()

            async with self._lock:
                if self._pn532:
                    self._pn532 = None
                    logger.log(LogLevel.INFO, "Hardware released")

        except Exception as e:
            raise ErrorHandler.create_app_error(
                error=e,
                message="Failed to cleanup NFC device",
                component="nfc",
                operation="cleanup",
                severity=ErrorSeverity.HIGH
            )

    @property
    def tag_subject(self) -> Subject:
        """
        Get the tag detection subject for subscribing to tag events.
        
        Returns:
            The tag detection Subject instance from the TagDetectionManager
        """
        return self._tag_manager.tag_subject
