#!/usr/bin/env python3
"""
Test simple avec gpiozero (plus moderne)
"""

import time
from signal import pause

print("=" * 50)
print("🎯 TEST GPIO AVEC GPIOZERO")
print("=" * 50)

try:
    from gpiozero import Button
    print("✅ gpiozero importé")
except ImportError:
    print("❌ gpiozero non disponible")
    print("   Installez avec: pip3 install gpiozero")
    exit(1)

# Configuration des boutons (selon détection réelle)
buttons = {
    16: "Next",
    26: "Previous",
    23: "Play/Pause"
}

# Créer les objets Button
button_objects = {}

for pin, name in buttons.items():
    try:
        btn = Button(pin, pull_up=True, bounce_time=0.3)

        # Créer une fonction callback pour ce bouton
        def make_callback(button_name, pin_num):
            def callback():
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] 🔘 {button_name} pressé! (GPIO {pin_num})")
            return callback

        btn.when_pressed = make_callback(name, pin)
        button_objects[pin] = btn
        print(f"✅ GPIO {pin:2d} configuré ({name})")

    except Exception as e:
        print(f"❌ GPIO {pin:2d} erreur: {e}")

print("\n📍 Appuyez sur les boutons...")
print("   Ctrl+C pour arrêter")
print("-" * 50)

try:
    pause()  # Attendre indéfiniment les événements
except KeyboardInterrupt:
    print("\n🛑 Arrêt...")
    for btn in button_objects.values():
        btn.close()
    print("✅ Nettoyage terminé")