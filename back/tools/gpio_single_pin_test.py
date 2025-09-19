#!/usr/bin/env python3
"""
Test ultra-simple d'un seul GPIO
"""

import sys

# Pin à tester (changez selon besoin)
PIN = 16  # Next button (détection réelle)

print(f"Test GPIO {PIN}")
print("-" * 30)

try:
    import RPi.GPIO as GPIO

    # Config
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print(f"GPIO {PIN} configuré")
    print("Appuyez sur le bouton...")
    print("Ctrl+C pour arrêter\n")

    # Boucle simple
    last = 1
    while True:
        val = GPIO.input(PIN)
        if val == 0 and last == 1:
            print(f"🔘 BOUTON PRESSÉ!")
        last = val

except ImportError:
    print("❌ RPi.GPIO non installé")
except KeyboardInterrupt:
    print("\nArrêt")
    GPIO.cleanup()
except Exception as e:
    print(f"Erreur: {e}")