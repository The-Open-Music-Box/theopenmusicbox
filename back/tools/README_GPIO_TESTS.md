# Outils de Test GPIO Simples

## Scripts de Test Direct

### 1. `gpio_simple_test.py` - Test des 5 GPIO configurés
```bash
sudo python3 tools/gpio_simple_test.py
```
- Teste les 5 pins configurés (26, 19, 13, 20, 21)
- Affiche quand un bouton est pressé
- Utilise RPi.GPIO directement

### 2. `gpio_single_pin_test.py` - Test d'un seul pin
```bash
sudo python3 tools/gpio_single_pin_test.py
```
- Test ultra-simple d'un seul GPIO (pin 26 par défaut)
- Modifiez la variable `PIN` pour tester un autre pin
- Le plus minimaliste possible

### 3. `gpio_gpiozero_test.py` - Test avec gpiozero
```bash
python3 tools/gpio_gpiozero_test.py
```
- Utilise la librairie gpiozero (plus moderne)
- Gestion événementielle des boutons
- Ne nécessite pas toujours sudo

### 4. `gpio_scan_all.py` - Scanner tous les GPIO
```bash
sudo python3 tools/gpio_scan_all.py
```
- Scanne TOUS les GPIO safe (17 pins)
- Utile pour identifier quel pin est connecté à quel bouton
- Affiche tout changement d'état

## Utilisation Rapide

### Test le plus simple (1 pin):
```bash
# Éditer le fichier pour changer le PIN si besoin
nano tools/gpio_single_pin_test.py
# Puis exécuter
sudo python3 tools/gpio_single_pin_test.py
```

### Test complet des boutons configurés:
```bash
sudo python3 tools/gpio_simple_test.py
```

### Identifier les connexions:
```bash
# Scanner tous les pins pour voir lesquels réagissent
sudo python3 tools/gpio_scan_all.py
```

## Résultats Attendus

Quand vous appuyez sur un bouton, vous devriez voir:
```
[14:23:45] 🔘 Next         PRESSÉ! (GPIO 26)
[14:23:47] 🔘 Previous      PRESSÉ! (GPIO 19)
[14:23:49] 🔘 Play/Pause    PRESSÉ! (GPIO 13)
```

## Dépannage

### Aucune détection?
1. Vérifiez les connexions physiques
2. Essayez avec `sudo`
3. Testez `gpio_scan_all.py` pour identifier les bons pins
4. Vérifiez que les boutons sont "normally open" (NO)

### "Permission denied"?
```bash
sudo usermod -a -G gpio $USER
# Puis déconnectez/reconnectez
```

### "No module named RPi"?
```bash
sudo apt-get update
sudo apt-get install python3-rpi.gpio
pip3 install gpiozero
```