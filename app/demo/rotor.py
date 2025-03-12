# app/demo/rotor.py

import time
import RPi.GPIO as GPIO

# Configuration
MOTOR_PINS = [16, 23, 24, 25]  # Pins BCM pour le moteur
DIRECTION = 1  # 1 pour sens horaire, -1 pour sens anti-horaire
STEP_DELAY = 0.01  # Délai plus long pour debug
STEPS = 2048  # Moitié du tour pour test

# Séquence pour le moteur (mode demi-pas pour plus de couple)
SEQUENCE = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

def setup():
    # Reset complet du GPIO
    GPIO.cleanup()

    # Configuration en mode BCM
    GPIO.setmode(GPIO.BCM)

    # Configuration des pins
    for pin in MOTOR_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)
        print(f"Pin {pin} configuré en sortie")

    print("Moteur initialisé, attente 2 secondes...")
    time.sleep(2)

def cleanup():
    for pin in MOTOR_PINS:
        GPIO.output(pin, False)
    GPIO.cleanup()
    print("Ressources libérées")

def test_pins():
    # Test individuel de chaque pin
    for pin in MOTOR_PINS:
        print(f"Test du pin {pin}")
        GPIO.output(pin, True)
        time.sleep(0.5)
        GPIO.output(pin, False)
        time.sleep(0.2)

def rotate_motor(steps, direction=DIRECTION):
    sequence_index = 0
    steps_taken = 0

    try:
        print(f"Début rotation: {steps} pas, direction: {direction}")
        while steps_taken < steps:
            sequence = SEQUENCE[sequence_index]

            # Afficher les états pour debug
            if steps_taken % 100 == 0:
                print(f"Pas {steps_taken}: {sequence}")

            # Appliquer la séquence sur les pins
            for pin, value in zip(MOTOR_PINS, sequence):
                GPIO.output(pin, bool(value))

            # Avancer dans la séquence selon la direction
            sequence_index = (sequence_index + direction) % len(SEQUENCE)
            steps_taken += 1

            time.sleep(STEP_DELAY)

        print(f"Rotation terminée: {steps_taken} pas effectués")

    except KeyboardInterrupt:
        print("\nRotation interrompue")
    finally:
        # Arrêt du moteur (courant coupé)
        for pin in MOTOR_PINS:
            GPIO.output(pin, False)

if __name__ == "__main__":
    try:
        setup()

        print("Test des pins individuels...")
        test_pins()

        print("Rotation du moteur...")
        rotate_motor(STEPS)

    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        cleanup()