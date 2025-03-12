import RPi.GPIO as GPIO
import time

# Désactivation des avertissements GPIO
GPIO.setwarnings(False)

# Configuration des ports GPIO
RED_PIN = 9
GREEN_PIN = 11
BLUE_PIN = 10

# Initialisation des ports GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)
GPIO.setup(BLUE_PIN, GPIO.OUT)

# Configuration de PWM sur les ports GPIO
red_pwm = GPIO.PWM(RED_PIN, 1000)  # Fréquence de 1 kHz
green_pwm = GPIO.PWM(GREEN_PIN, 1000)  # Fréquence de 1 kHz
blue_pwm = GPIO.PWM(BLUE_PIN, 1000)  # Fréquence de 1 kHz

# Démarrage de PWM avec un cycle de service initial de 0 (LED éteinte)
red_pwm.start(0)
green_pwm.start(0)
blue_pwm.start(0)

def set_color(red_intensity, green_intensity, blue_intensity):
    """Définit les intensités des couleurs rouge, verte et bleue.

    Arguments:
    red_intensity -- Intensité de la couleur rouge (0 à 100)
    green_intensity -- Intensité de la couleur verte (0 à 100)
    blue_intensity -- Intensité de la couleur bleue (0 à 100)
    """
    red_pwm.ChangeDutyCycle(red_intensity)
    green_pwm.ChangeDutyCycle(green_intensity)
    blue_pwm.ChangeDutyCycle(blue_intensity)

try:
    while True:
        # Rouge
        set_color(100, 0, 0)
        print("Couleur actuelle: Rouge")
        time.sleep(1)

        # Vert
        set_color(0, 100, 0)
        print("Couleur actuelle: Vert")
        time.sleep(1)

        # Bleu
        set_color(0, 0, 100)
        print("Couleur actuelle: Bleu")
        time.sleep(1)

except KeyboardInterrupt:
    pass
finally:
    # Arrêt du PWM et nettoyage des ports GPIO
    red_pwm.stop()
    green_pwm.stop()
    blue_pwm.stop()
    GPIO.cleanup()
