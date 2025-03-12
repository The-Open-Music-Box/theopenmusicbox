# app/demo/ir.py

import RPi.GPIO as GPIO
import time

# Configuration du GPIO
IR_PIN = 20

def setup():
    # Configurer le mode de numérotation des broches
    GPIO.setmode(GPIO.BCM)
    # Configurer le pin comme entrée avec résistance pull-up
    GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print(f"Récepteur IR configuré sur GPIO {IR_PIN}")

def detect_signal():
    try:
        print("Démarrage de la détection IR. Appuyez sur Ctrl+C pour quitter.")
        prev_value = GPIO.input(IR_PIN)
        last_change = time.time()

        while True:
            # Lire l'état actuel du pin
            current_value = GPIO.input(IR_PIN)

            # Si l'état a changé, enregistrer l'événement
            if current_value != prev_value:
                now = time.time()
                duration = now - last_change
                state = "Haut" if current_value else "Bas"
                print(f"Signal {state}, durée: {duration:.6f} secondes")

                # Mettre à jour les variables pour la prochaine détection
                prev_value = current_value
                last_change = now

            # Petite pause pour réduire l'utilisation CPU
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nDétection IR arrêtée par l'utilisateur")
    finally:
        GPIO.cleanup()
        print("GPIO nettoyé")

if __name__ == "__main__":
    setup()
    detect_signal()