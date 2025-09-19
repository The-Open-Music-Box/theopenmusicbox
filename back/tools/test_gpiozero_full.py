#!/usr/bin/env python3
"""
Test complet avec gpiozero (boutons + encodeur)
Configuration selon la détection réelle
"""

import time
import sys
from signal import pause

print("=" * 60)
print("🎮 TEST COMPLET GPIOZERO")
print("=" * 60)

try:
    from gpiozero import Button, RotaryEncoder
    print("✅ gpiozero importé")
except ImportError:
    print("❌ gpiozero non disponible")
    print("   Installez avec: pip3 install gpiozero")
    sys.exit(1)

# Configuration selon détection réelle
CONFIG = {
    'next': 16,
    'previous': 26,
    'play_pause': 23,
    'encoder_clk': 8,
    'encoder_dt': 21
}

print("\n📋 Configuration détectée:")
for name, pin in CONFIG.items():
    print(f"   {name:15s}: GPIO {pin}")

# Statistiques
stats = {
    'next': 0,
    'prev': 0,
    'play': 0,
    'vol_up': 0,
    'vol_down': 0,
    'encoder_pos': 0
}

# Créer les boutons
devices = {}

try:
    # Bouton Next
    devices['next'] = Button(CONFIG['next'], pull_up=True, bounce_time=0.3)
    devices['next'].when_pressed = lambda: button_pressed("NEXT", 'next')
    print(f"✅ Bouton NEXT (GPIO {CONFIG['next']}) configuré")
except Exception as e:
    print(f"❌ Bouton NEXT erreur: {e}")

try:
    # Bouton Previous
    devices['prev'] = Button(CONFIG['previous'], pull_up=True, bounce_time=0.3)
    devices['prev'].when_pressed = lambda: button_pressed("PREVIOUS", 'prev')
    print(f"✅ Bouton PREVIOUS (GPIO {CONFIG['previous']}) configuré")
except Exception as e:
    print(f"❌ Bouton PREVIOUS erreur: {e}")

try:
    # Bouton Play/Pause (switch de l'encodeur)
    devices['play'] = Button(CONFIG['play_pause'], pull_up=True, bounce_time=0.3)
    devices['play'].when_pressed = lambda: button_pressed("PLAY/PAUSE", 'play')
    print(f"✅ Bouton PLAY/PAUSE (GPIO {CONFIG['play_pause']}) configuré")
except Exception as e:
    print(f"❌ Bouton PLAY/PAUSE erreur: {e}")

try:
    # Encodeur rotatif
    devices['encoder'] = RotaryEncoder(
        CONFIG['encoder_clk'],
        CONFIG['encoder_dt'],
        bounce_time=0.01
    )

    def on_clockwise():
        stats['vol_up'] += 1
        stats['encoder_pos'] += 1
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔊 Volume UP   (pos: {stats['encoder_pos']:+3d}) [{stats['vol_up']} fois]")

    def on_counter_clockwise():
        stats['vol_down'] += 1
        stats['encoder_pos'] -= 1
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔉 Volume DOWN (pos: {stats['encoder_pos']:+3d}) [{stats['vol_down']} fois]")

    devices['encoder'].when_rotated_clockwise = on_clockwise
    devices['encoder'].when_rotated_counter_clockwise = on_counter_clockwise

    print(f"✅ Encodeur (GPIO {CONFIG['encoder_clk']}/{CONFIG['encoder_dt']}) configuré")
except Exception as e:
    print(f"❌ Encodeur erreur: {e}")

def button_pressed(name, stat_key):
    """Callback pour les boutons"""
    stats[stat_key] += 1
    timestamp = time.strftime("%H:%M:%S")

    if stat_key == 'next':
        icon = "⏭️"
    elif stat_key == 'prev':
        icon = "⏮️"
    else:
        icon = "⏯️"

    print(f"[{timestamp}] {icon} {name:12s} pressé [{stats[stat_key]} fois]")

print("\n" + "=" * 60)
print("🎯 TEST ACTIF")
print("-" * 40)
print("• Appuyez sur les boutons")
print("• Tournez l'encodeur")
print("• Ctrl+C pour arrêter")
print("=" * 60)

try:
    pause()  # Attendre les événements
except KeyboardInterrupt:
    print("\n\n" + "=" * 60)
    print("📊 RÉSUMÉ DE SESSION")
    print("-" * 40)
    print(f"⏭️  Next:       {stats['next']} pressions")
    print(f"⏮️  Previous:   {stats['prev']} pressions")
    print(f"⏯️  Play/Pause: {stats['play']} pressions")
    print(f"🔊 Volume UP:   {stats['vol_up']} rotations")
    print(f"🔉 Volume DOWN: {stats['vol_down']} rotations")
    print(f"\n📍 Position encodeur finale: {stats['encoder_pos']:+d}")

    # Nettoyage
    for device in devices.values():
        try:
            device.close()
        except:
            pass

    print("\n✅ Dispositifs fermés proprement")