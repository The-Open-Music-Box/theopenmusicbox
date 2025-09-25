#!/bin/bash
# Test rapide WM8960 - à exécuter sur le Raspberry Pi

echo "🧪 TEST RAPIDE WM8960 - DIAGNOSTIC ABSENCE DE SON"
echo "=================================================="

echo ""
echo "1️⃣ Test ALSA devices..."
aplay -l

echo ""
echo "2️⃣ Test device WM8960..."
aplay -D hw:wm8960soundcard --list-pcms

echo ""
echo "3️⃣ Mixer ALSA settings..."
amixer scontents | grep -A5 -B5 -i "master\|speaker\|headphone\|playback"

echo ""
echo "4️⃣ Volume levels..."
amixer get Master 2>/dev/null || echo "Pas de contrôle Master"
amixer get Speaker 2>/dev/null || echo "Pas de contrôle Speaker"
amixer get Headphone 2>/dev/null || echo "Pas de contrôle Headphone"

echo ""
echo "5️⃣ Test direct aplay (ARRÊTEZ L'APPLICATION D'ABORD!)..."
echo "Assurez-vous que l'application est arrêtée, puis:"
echo "aplay -D hw:wm8960soundcard,0 /usr/share/sounds/alsa/Front_Center.wav"

echo ""
echo "6️⃣ Configuration audio système..."
cat /proc/asound/cards

echo ""
echo "7️⃣ Device tree overlays actifs..."
grep -i wm8960 /boot/firmware/config.txt

echo ""
echo "🏁 TEST TERMINÉ. Exécutez les commandes manuellement pour plus de détails."