# app/src/module/light_sensor/light_bh1750_i2c.py

import eventlet
from eventlet.semaphore import Semaphore
from eventlet import Event, spawn_n
from rx.subject import Subject
import board
import busio
import adafruit_bh1750

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel
from app.src.helpers.exceptions import AppError
from .light_sensor_hardware import LightSensorHardware, LightLevel

logger = ImprovedLogger(__name__)

class Bh1750I2cLightSensor(LightSensorHardware):
    I2C_ADDRESS = 0x23
    MONITOR_INTERVAL = 1.0
    MAX_CONSECUTIVE_ERRORS = 3

    def __init__(self, lock: Semaphore):
        self._lock = lock
        self._sensor = None
        self._light_subject = Subject()
        self._stop_event = Event()
        self._last_reading = None

        try:
            self._initialize_hardware()
            self._start_monitoring()
            logger.log(LogLevel.INFO, "Light sensor initialized")
        except Exception as e:
            logger.log(LogLevel.ERROR, "Light sensor initialization failed", exc_info=e)
            self.cleanup()
            raise AppError.hardware_error("Light sensor initialization failed", "light_sensor", "init")

    def _initialize_hardware(self) -> None:
        try:
            with self._lock:
                i2c = busio.I2C(board.SCL, board.SDA)
                self._sensor = adafruit_bh1750.BH1750(i2c, address=self.I2C_ADDRESS)
                logger.log(LogLevel.INFO, "Light sensor hardware ready")
        except Exception as e:
            raise AppError.hardware_error(
                message=f"Light sensor hardware not available: {str(e)}",
                component="light_sensor",
                operation="init_hardware"
            )

    def _read_sensor(self) -> float:
        try:
            with self._lock:
                return self._sensor.lux
        except Exception as e:
            if self._last_reading:
                return self._last_reading.lux
            raise AppError.hardware_error(
                message=f"Failed to read sensor: {str(e)}",
                component="light_sensor",
                operation="read"
            )

    def _monitor_loop(self):
        consecutive_errors = 0
        while not self._stop_event.ready():
            try:
                lux = self._read_sensor()
                self._last_reading = LightLevel(lux=lux)
                self._light_subject.on_next(self._last_reading)
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                logger.log(LogLevel.ERROR, f"Monitor error #{consecutive_errors}: {str(e)}", exc_info=e)
                if consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    logger.log(LogLevel.ERROR, "Too many consecutive errors, stopping monitor")
                    break
            eventlet.sleep(self.MONITOR_INTERVAL)

    def _start_monitoring(self):
        spawn_n(self._monitor_loop)
        logger.log(LogLevel.INFO, "Monitoring started")

    @property
    def light_level_stream(self) -> Subject:
        return self._light_subject

    def cleanup(self):
        self._stop_event.send(True)
        logger.log(LogLevel.INFO, "Cleanup completed")
