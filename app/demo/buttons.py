#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# Configuration des pins GPIO pour les boutons
BUTTON_PINS = [13, 19, 26]
BUTTON_NAMES = ["Bouton 1", "Bouton 2", "Bouton 3"]

def setup():
    # Configuration du mode GPIO
    GPIO.setmode(GPIO.BCM)
    
    # Configuration des pins comme entrées avec résistances pull-up
    for pin in BUTTON_PINS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    print("Pins GPIO configurés pour les boutons:")
    for i, pin in enumerate(BUTTON_PINS):
        print(f"- {BUTTON_NAMES[i]}: GPIO {pin}")

def monitor_buttons():
    # État initial des boutons (True avec pull-up signifie non pressé)
    button_states = [GPIO.input(pin) for pin in BUTTON_PINS]
    
    print("\nSurveillance des boutons. Appuyez sur Ctrl+C pour quitter.")
    print("État initial: 1 = non pressé, 0 = pressé")
    for i, state in enumerate(button_states):
        print(f"- {BUTTON_NAMES[i]}: {state}")
    
    try:
        while True:
            # Vérification de l'état de chaque bouton
            for i, pin in enumerate(BUTTON_PINS):
                current_state = GPIO.input(pin)
                
                # Si l'état du bouton a changé
                if current_state != button_states[i]:
                    action = "relâché" if current_state else "pressé"
                    print(f"{BUTTON_NAMES[i]} ({pin}) {action} à {time.strftime('%H:%M:%S')}")
                    
                    # Mise à jour de l'état du bouton
                    button_states[i] = current_state
            
            # Petite pause pour réduire l'utilisation du CPU
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\nSurveillance des boutons arrêtée par l'utilisateur")
    finally:
        GPIO.cleanup()
        print("GPIO nettoyé")

if __name__ == "__main__":
    setup()
    monitor_buttons()