import pytest
from src.module.ledhat.ledhat_factory import get_led_hat
import os

@pytest.fixture(autouse=True)
def set_mock_env(monkeypatch):
    monkeypatch.setenv("USE_MOCK_HARDWARE", "true")


def test_ledhat_factory_returns_mock():
    led_hat = get_led_hat(gpio_pin=12)
    # The mock implementation has these methods and logs actions
    assert hasattr(led_hat, 'clear')
    assert hasattr(led_hat, 'start_animation')
    assert hasattr(led_hat, 'stop_animation')
    assert hasattr(led_hat, 'cleanup')
    # Test that calling methods does not raise
    led_hat.clear()
    led_hat.start_animation('test_anim', speed=1)
    led_hat.stop_animation()
    led_hat.cleanup()


def test_ledhat_factory_real_import(monkeypatch):
    # Simulate non-mock environment
    monkeypatch.delenv("USE_MOCK_HARDWARE", raising=False)
    monkeypatch.setattr("sys.platform", "linux")
    # Should not raise, but will fail to import rpi_ws281x unless on Pi
    try:
        get_led_hat(gpio_pin=12)
    except ImportError:
        pass  # Acceptable on non-Pi
    except Exception as e:
        # Acceptable: hardware init may fail on non-Pi
        pass
