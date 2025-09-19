#!/usr/bin/env python3
"""
Scan tous les GPIO pour voir lesquels répondent
"""

import time
import sys

print("=" * 50)
print("🔍 SCAN DE TOUS LES GPIO")
print("=" * 50)

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("❌ RPi.GPIO non disponible")
    sys.exit(1)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pins à scanner (tous les GPIO safe sur Raspberry Pi)
# Excluant: 0,1 (I2C), 2,3 (I2C), 14,15 (UART)
safe_pins = [4, 5, 6, 12, 13, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

print(f"Test de {len(safe_pins)} pins GPIO...")
print("Appuyez sur n'importe quel bouton connecté")
print("Ctrl+C pour arrêter\n")

# Configurer tous les pins
states = {}
for pin in safe_pins:
    try:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        states[pin] = GPIO.input(pin)
        print(f"✓ GPIO {pin:2d} configuré")
    except Exception as e:
        print(f"✗ GPIO {pin:2d} erreur: {e}")

print("\n" + "-" * 50)
print("SURVEILLANCE ACTIVE - Appuyez sur vos boutons")
print("-" * 50)

try:
    while True:
        for pin in safe_pins:
            if pin in states:
                try:
                    current = GPIO.input(pin)

                    # Détecter changement
                    if current != states[pin]:
                        timestamp = time.strftime("%H:%M:%S")
                        if current == 0:
                            print(f"[{timestamp}] 🔴 GPIO {pin:2d} → BAS (bouton pressé?)")
                        else:
                            print(f"[{timestamp}] 🟢 GPIO {pin:2d} → HAUT (bouton relâché?)")

                        states[pin] = current
                except:
                    pass

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n\nNettoyage...")
    GPIO.cleanup()
    print("✅ Terminé")