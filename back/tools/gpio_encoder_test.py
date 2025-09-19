#!/usr/bin/env python3
"""
Test intelligent de l'encodeur rotatif et des boutons
Analyse l'ordre des signaux pour déterminer la direction
"""

import time
import sys
from collections import deque

print("=" * 60)
print("🎛️  TEST ENCODEUR ROTATIF INTELLIGENT")
print("=" * 60)

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("❌ RPi.GPIO non disponible")
    sys.exit(1)

# Configuration selon hardware_config.py
ENCODER_CLK = 8   # GPIO 8
ENCODER_DT = 21   # GPIO 21
BTN_NEXT = 16     # GPIO 16
BTN_PREV = 26     # GPIO 26
BTN_SWITCH = 23   # GPIO 23 (bouton de l'encodeur)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Configuration des pins
pins = {
    ENCODER_CLK: "Encoder CLK",
    ENCODER_DT: "Encoder DT",
    BTN_NEXT: "Next Button",
    BTN_PREV: "Previous Button",
    BTN_SWITCH: "Encoder Switch"
}

for pin, name in pins.items():
    try:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"✅ GPIO {pin:2d} configuré ({name})")
    except Exception as e:
        print(f"❌ GPIO {pin:2d} erreur: {e}")

print("\n📊 Correspondances détectées:")
print(f"   Encodeur: CLK={ENCODER_CLK}, DT={ENCODER_DT}")
print(f"   Boutons: Next={BTN_NEXT}, Prev={BTN_PREV}, Switch={BTN_SWITCH}")

# Variables pour l'encodeur
encoder_state = {
    'last_clk': GPIO.input(ENCODER_CLK),
    'last_dt': GPIO.input(ENCODER_DT),
    'position': 0,
    'last_change': 0
}

# Historique pour détecter les patterns
event_history = deque(maxlen=4)

def detect_rotation_pattern():
    """Analyse l'historique pour détecter la direction de rotation"""
    if len(event_history) < 2:
        return None

    # Chercher le pattern de changement
    # Rotation droite: DT change avant CLK
    # Rotation gauche: CLK change avant DT
    first_down = None
    for event in event_history:
        if event[1] == 'down':
            first_down = event[0]
            break

    if first_down == ENCODER_DT:
        return "DROITE (Volume+)"
    elif first_down == ENCODER_CLK:
        return "GAUCHE (Volume-)"

    return None

print("\n🎯 Surveillance active...")
print("   • Tournez l'encodeur pour ajuster le volume")
print("   • Appuyez sur les boutons pour naviguer")
print("   • Ctrl+C pour arrêter")
print("-" * 60)

# États des boutons
button_states = {pin: GPIO.input(pin) for pin in pins.keys()}

# Compteurs
stats = {
    'volume_up': 0,
    'volume_down': 0,
    'next': 0,
    'prev': 0,
    'switch': 0
}

try:
    last_encoder_time = 0

    while True:
        current_time = time.time()

        # Lire l'état actuel
        current_clk = GPIO.input(ENCODER_CLK)
        current_dt = GPIO.input(ENCODER_DT)

        # Détecter les changements d'encodeur
        if current_clk != encoder_state['last_clk'] or current_dt != encoder_state['last_dt']:
            # Enregistrer l'événement
            if current_clk == 0 and encoder_state['last_clk'] == 1:
                event_history.append((ENCODER_CLK, 'down'))
            elif current_clk == 1 and encoder_state['last_clk'] == 0:
                event_history.append((ENCODER_CLK, 'up'))

            if current_dt == 0 and encoder_state['last_dt'] == 1:
                event_history.append((ENCODER_DT, 'down'))
            elif current_dt == 1 and encoder_state['last_dt'] == 0:
                event_history.append((ENCODER_DT, 'up'))

            # Détection de rotation avec debounce
            if current_time - last_encoder_time > 0.01:  # 10ms debounce
                direction = detect_rotation_pattern()

                if direction and current_clk == 0:  # Sur front descendant de CLK
                    timestamp = time.strftime("%H:%M:%S")

                    if "DROITE" in direction:
                        encoder_state['position'] += 1
                        stats['volume_up'] += 1
                        print(f"[{timestamp}] 🔊 Volume UP   (position: {encoder_state['position']:+3d}) [{stats['volume_up']} fois]")
                    elif "GAUCHE" in direction:
                        encoder_state['position'] -= 1
                        stats['volume_down'] += 1
                        print(f"[{timestamp}] 🔉 Volume DOWN (position: {encoder_state['position']:+3d}) [{stats['volume_down']} fois]")

                    last_encoder_time = current_time

            encoder_state['last_clk'] = current_clk
            encoder_state['last_dt'] = current_dt

        # Vérifier les boutons
        for pin in [BTN_NEXT, BTN_PREV, BTN_SWITCH]:
            current = GPIO.input(pin)
            if current == 0 and button_states[pin] == 1:  # Front descendant
                timestamp = time.strftime("%H:%M:%S")

                if pin == BTN_NEXT:
                    stats['next'] += 1
                    print(f"[{timestamp}] ⏭️  NEXT pressé [{stats['next']} fois]")
                elif pin == BTN_PREV:
                    stats['prev'] += 1
                    print(f"[{timestamp}] ⏮️  PREVIOUS pressé [{stats['prev']} fois]")
                elif pin == BTN_SWITCH:
                    stats['switch'] += 1
                    print(f"[{timestamp}] ⏯️  PLAY/PAUSE pressé [{stats['switch']} fois]")

            button_states[pin] = current

        time.sleep(0.001)  # 1ms pour réactivité maximale

except KeyboardInterrupt:
    print("\n\n" + "=" * 60)
    print("📊 STATISTIQUES DE SESSION")
    print("-" * 40)
    print(f"🔊 Volume UP:    {stats['volume_up']} rotations")
    print(f"🔉 Volume DOWN:  {stats['volume_down']} rotations")
    print(f"⏭️  Next:         {stats['next']} pressions")
    print(f"⏮️  Previous:     {stats['prev']} pressions")
    print(f"⏯️  Play/Pause:   {stats['switch']} pressions")
    print(f"\n📍 Position finale encodeur: {encoder_state['position']:+d}")

    GPIO.cleanup()
    print("\n✅ GPIO nettoyé")