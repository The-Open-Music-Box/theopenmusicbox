# app/demo/vol.py

import RPi.GPIO as GPIO
import time

# Configuration des pins GPIO
CLK_PIN = 22     # Signal d'horloge (A)
DT_PIN = 27     # Signal de données (B)
SW_PIN = 4      # Bouton-poussoir

def main():
    try:
        # Configuration des pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # États initiaux
        clk_last = GPIO.input(CLK_PIN)
        sw_last = GPIO.input(SW_PIN)
        volume = 50

        print("Test Encodeur Rotatif - Ctrl+C pour quitter")
        print("-------------------------------------------")
        print(f"Volume initial: {volume}")

        while True:
            # Lire les états actuels
            clk_current = GPIO.input(CLK_PIN)
            dt_current = GPIO.input(DT_PIN)
            sw_current = GPIO.input(SW_PIN)

            # Détection de rotation
            if clk_current != clk_last:
                if dt_current != clk_current:
                    volume += 1
                    print(f"Rotation droite: {volume}")
                else:
                    volume -= 1
                    print(f"Rotation gauche: {volume}")

            # Détection du bouton
            if sw_current != sw_last:
                if sw_current == 0:
                    print("Bouton pressé")
                else:
                    print("Bouton relâché")

            clk_last = clk_current
            sw_last = sw_current
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nProgramme arrêté")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()