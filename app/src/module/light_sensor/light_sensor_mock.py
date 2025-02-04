# app/src/module/light_sensor/light_sensor_mock.py

import random
import eventlet
from eventlet import Event, spawn_n
from rx.subject import Subject
from .light_sensor_interface import LightSensorInterface, LightLevel
from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

class MockLightSensor(LightSensorInterface):
    def __init__(self):
        self._light_subject = Subject()
        self._stop_event = Event()
        self._monitor_greenlet = None
        self._start_monitoring()
        logger.log(LogLevel.INFO, "Mock light sensor initialized")

    def _start_monitoring(self):
        def monitor():
            while not self._stop_event.send():
                try:
                    lux = random.uniform(100, 1000)
                    self._light_subject.on_next(LightLevel(lux=lux))
                    logger.log(LogLevel.DEBUG, "Light level reading", extra={
                        "lux": f"{lux:.1f}"
                    })
                    eventlet.sleep(1.0)
                except Exception as e:
                    logger.log(LogLevel.ERROR, "Monitoring error", exc_info=e)
                    eventlet.sleep(1.0)

        self._monitor_greenlet = spawn_n(monitor)
        logger.log(LogLevel.INFO, "Monitoring started")

    @property
    def light_level_stream(self) -> Subject:
        return self._light_subject

    def cleanup(self):
        try:
            logger.log(LogLevel.INFO, "Starting cleanup")
            self._stop_event.send()

            with eventlet.Timeout(2, False):
                if self._monitor_greenlet is not None:
                    self._monitor_greenlet.wait()

            logger.log(LogLevel.INFO, "Cleanup completed")
        except Exception as e:
            logger.log(LogLevel.ERROR, "Cleanup failed", exc_info=e)
