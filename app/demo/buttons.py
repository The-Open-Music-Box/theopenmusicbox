# app/demo/buttons.py

import RPi.GPIO as GPIO
import time

# Configuring GPIO pins for buttons
BUTTON_PINS = [13, 19, 26]
BUTTON_NAMES = ["Bouton 1", "Bouton 2", "Bouton 3"]

def setup():
    # GPIO mode configuration
    GPIO.setmode(GPIO.BCM)

    # Pin configuration as inputs with pull-up resistors
    for pin in BUTTON_PINS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print("GPIO pins configured for buttons:")
    for i, pin in enumerate(BUTTON_PINS):
        print(f"- {BUTTON_NAMES[i]}: GPIO {pin}")

def monitor_buttons():
    # Initial button status (True with pull-up means not pressed)
    button_states = [GPIO.input(pin) for pin in BUTTON_PINS]

    print("\nButton monitoring. Press Ctrl+C to exit.")
    print("Initial state: 1 = not pressed, 0 = pressed")
    for i, state in enumerate(button_states):
        print(f"- {BUTTON_NAMES[i]}: {state}")

    try:
        while True:
            # Checking the status of each button
            for i, pin in enumerate(BUTTON_PINS):
                current_state = GPIO.input(pin)

                # If the state of the button has changed
                if current_state != button_states[i]:
                    action = "relâché" if current_state else "pressé"
                    print(f"{BUTTON_NAMES[i]} ({pin}) {action} à {time.strftime('%H:%M:%S')}")

                    # Update button status
                    button_states[i] = current_state

            # Short pause to reduce CPU usage
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nButton monitoring stopped by user")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned")

if __name__ == "__main__":
    setup()
    monitor_buttons()