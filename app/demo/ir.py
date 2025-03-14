# app/demo/ir.py

import RPi.GPIO as GPIO
import time

# GPIO configuration
IR_PIN = 20

def setup():
    # Configure pin numbering mode
    GPIO.setmode(GPIO.BCM)
    # Configure the pin as an input with pull-up resistor
    GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print(f"Récepteur IR configuré sur GPIO {IR_PIN}")

def detect_signal():
    try:
        print("Démarrage de la détection IR. Appuyez sur Ctrl+C pour quitter.")
        prev_value = GPIO.input(IR_PIN)
        last_change = time.time()

        while True:
            # Read current pin status
            current_value = GPIO.input(IR_PIN)

            # If the state has changed, log the event
            if current_value != prev_value:
                now = time.time()
                duration = now - last_change
                state = "Haut" if current_value else "Bas"
                print(f"Signal {state}, durée: {duration:.6f} secondes")

                # Update variables for next detection
                prev_value = current_value
                last_change = now

            # Short pause to reduce CPU usage
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nDétection IR arrêtée par l'utilisateur")
    finally:
        GPIO.cleanup()
        print("GPIO nettoyé")

if __name__ == "__main__":
    setup()
    detect_signal()