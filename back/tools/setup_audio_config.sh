#!/bin/bash

# Script de configuration automatique audio pour The Open Music Box
# Configure ALSA pour utiliser le WM8960 par nom (stable entre redémarrages)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "🎵 Configuration Audio WM8960 🎵"
echo "========================================="
echo ""

# Fonction pour afficher les messages colorés
print_status() {
    if [ "$1" = "OK" ]; then
        echo -e "${GREEN}[✓]${NC} $2"
    elif [ "$1" = "ERROR" ]; then
        echo -e "${RED}[✗]${NC} $2"
    elif [ "$1" = "WARNING" ]; then
        echo -e "${YELLOW}[!]${NC} $2"
    elif [ "$1" = "INFO" ]; then
        echo -e "${BLUE}[i]${NC} $2"
    fi
}

# 1. Détection du WM8960
print_status "INFO" "Détection de la carte audio WM8960..."

# Vérifier si aplay est disponible
if ! command -v aplay &> /dev/null; then
    print_status "ERROR" "aplay n'est pas installé. Installation requise: sudo apt-get install alsa-utils"
    exit 1
fi

# Détecter la carte WM8960
WM8960_FOUND=false
WM8960_CARD_NUM=""

# Obtenir la liste des cartes audio
APLAY_OUTPUT=$(aplay -l 2>/dev/null || true)

if [ -z "$APLAY_OUTPUT" ]; then
    print_status "ERROR" "Aucune carte audio détectée"
    exit 1
fi

# Chercher le WM8960
while IFS= read -r line; do
    if echo "$line" | grep -qi "wm8960\|wm8960soundcard"; then
        WM8960_FOUND=true
        # Extraire le numéro de carte
        if [[ "$line" =~ card[[:space:]]([0-9]+): ]]; then
            WM8960_CARD_NUM="${BASH_REMATCH[1]}"
            print_status "OK" "WM8960 détecté sur la carte $WM8960_CARD_NUM"
            break
        fi
    fi
done <<< "$APLAY_OUTPUT"

if [ "$WM8960_FOUND" = false ]; then
    print_status "ERROR" "Carte WM8960 non détectée. Vérifiez les connexions I2C."
    print_status "INFO" "Cartes audio disponibles:"
    echo "$APLAY_OUTPUT" | grep "^card" | sed 's/^/    /'
    exit 1
fi

# 2. Test de la carte WM8960 par nom
print_status "INFO" "Test d'accès à la carte WM8960 par nom..."

if aplay -D hw:wm8960soundcard,0 --list-pcms &>/dev/null; then
    print_status "OK" "Accès par nom 'hw:wm8960soundcard' fonctionnel"
    DEVICE_NAME="hw:wm8960soundcard,0"
else
    print_status "WARNING" "Accès par nom échoué, utilisation du numéro de carte $WM8960_CARD_NUM"
    DEVICE_NAME="hw:$WM8960_CARD_NUM,0"
fi

# 3. Sauvegarde de l'ancienne configuration
if [ -f /etc/asound.conf ]; then
    print_status "INFO" "Sauvegarde de la configuration existante..."
    sudo cp /etc/asound.conf /etc/asound.conf.backup.$(date +%Y%m%d_%H%M%S)
    print_status "OK" "Ancienne configuration sauvegardée"
fi

# 4. Création de la nouvelle configuration ALSA
print_status "INFO" "Création de la configuration ALSA optimisée..."

sudo tee /etc/asound.conf > /dev/null << EOF
# Configuration ALSA pour The Open Music Box avec WM8960
# Généré automatiquement le $(date)
# Utilise le nom de la carte pour éviter les problèmes de numérotation

# Périphérique par défaut avec dmix pour permettre le partage
pcm.!default {
    type plug
    slave.pcm "dmixed"
}

# Configuration dmix pour le partage audio entre applications
pcm.dmixed {
    type dmix
    ipc_key 555555  # Clé IPC unique pour le partage
    ipc_key_add_uid false  # Partage entre différents utilisateurs
    ipc_perm 0666  # Permissions pour tous les utilisateurs

    slave {
        # Utilise le nom de la carte au lieu du numéro
        pcm "hw:wm8960soundcard"

        # Configuration optimisée pour WM8960
        period_time 0
        period_size 1024
        buffer_size 8192
        rate 44100
        format S16_LE
        channels 2
    }

    # Configuration de la latence
    bindings {
        0 0  # Canal gauche
        1 1  # Canal droit
    }
}

# Contrôle du volume par défaut
ctl.!default {
    type hw
    card "wm8960soundcard"
}

# Alias direct pour le WM8960 (utilise dmix)
pcm.wm8960 {
    type plug
    slave.pcm "dmixed"
}

# Contrôle direct du WM8960
ctl.wm8960 {
    type hw
    card "wm8960soundcard"
}

# Configuration pour l'accès direct si nécessaire (sans dmix)
pcm.wm8960_direct {
    type hw
    card "wm8960soundcard"
    device 0
}

# Configuration de sortie avec conversion de format automatique
pcm.output {
    type plug
    slave.pcm "dmixed"
}
EOF

print_status "OK" "Configuration ALSA créée avec succès"

# 5. Test de la configuration
print_status "INFO" "Test de la nouvelle configuration..."

# Test avec le périphérique par défaut
if timeout 2 aplay -D default --list-pcms &>/dev/null; then
    print_status "OK" "Périphérique par défaut accessible"
else
    print_status "WARNING" "Problème d'accès au périphérique par défaut"
fi

# Test avec dmix
if timeout 2 aplay -D dmixed --list-pcms &>/dev/null; then
    print_status "OK" "Configuration dmix fonctionnelle"
else
    print_status "WARNING" "Problème avec la configuration dmix"
fi

# 6. Configuration des volumes initiaux
print_status "INFO" "Configuration des volumes audio..."

# Configurer le volume principal
if amixer -c wm8960soundcard sset 'Headphone' 80% &>/dev/null; then
    print_status "OK" "Volume Headphone configuré à 80%"
fi

if amixer -c wm8960soundcard sset 'Speaker' 80% &>/dev/null; then
    print_status "OK" "Volume Speaker configuré à 80%"
fi

if amixer -c wm8960soundcard sset 'Master' 80% &>/dev/null; then
    print_status "OK" "Volume Master configuré à 80%"
fi

# 7. Test audio final
print_status "INFO" "Test audio final..."

if [ -f /usr/share/sounds/alsa/Front_Center.wav ]; then
    print_status "INFO" "Lecture du son de test (vous devriez entendre 'Front Center')..."
    if timeout 3 aplay /usr/share/sounds/alsa/Front_Center.wav &>/dev/null; then
        print_status "OK" "Test audio réussi!"
    else
        print_status "WARNING" "Test audio échoué (le service tomb utilise peut-être l'audio)"
    fi
else
    print_status "WARNING" "Fichier de test audio non trouvé"
fi

# 8. Redémarrage du service si nécessaire
if systemctl is-active --quiet app.service; then
    print_status "INFO" "Redémarrage du service tomb pour appliquer les changements..."
    sudo systemctl restart app.service
    sleep 3
    if systemctl is-active --quiet app.service; then
        print_status "OK" "Service tomb redémarré avec succès"
    else
        print_status "ERROR" "Le service tomb n'a pas redémarré correctement"
    fi
fi

# 9. Résumé final
echo ""
echo "========================================="
echo "Configuration terminée!"
echo "========================================="
print_status "INFO" "Configuration ALSA: /etc/asound.conf"
print_status "INFO" "Carte WM8960: Card $WM8960_CARD_NUM (hw:wm8960soundcard)"
print_status "INFO" "Périphérique par défaut: dmix avec partage audio"
echo ""
echo "Pour tester manuellement:"
echo "  aplay /usr/share/sounds/alsa/Front_Center.wav"
echo "  speaker-test -c 2 -t wav"
echo ""
echo "Si l'audio ne fonctionne pas:"
echo "  1. Vérifiez les connexions I2C: sudo i2cdetect -y 1"
echo "  2. Vérifiez les logs: journalctl -u app -n 50"
echo "  3. Testez sans le service: sudo systemctl stop app && aplay test.wav"
echo "========================================="