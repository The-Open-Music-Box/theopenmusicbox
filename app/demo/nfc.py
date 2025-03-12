# app/demo/nfc.py

"""
Script de démonstration pour le lecteur NFC PN532 avec debugging amélioré
"""
import time
import sys
from smbus2 import SMBus
import binascii

# Adresse I2C du PN532
PN532_I2C_ADDRESS = 0x24  # Peut être 0x24 ou 0x48, à vérifier

# Commandes PN532
CMD_GET_FIRMWARE_VERSION = 0x02
CMD_SAM_CONFIGURATION = 0x14
CMD_LIST_PASSIVE_TARGET = 0x4A
CMD_INDATA_EXCHANGE = 0x40

# Délais
DELAY_BETWEEN_COMMANDS = 0.05
DELAY_RESPONSE_READ = 0.1

# Activation du debugging
DEBUG = True

def debug_print(message):
    if DEBUG:
        print(f"DEBUG: {message}")

def write_frame(bus, data):
    """Envoie une trame complète au PN532"""
    try:
        # Préambule
        preamble = [0x00, 0x00, 0xFF]

        # Longueur de données + 1 (pour TFI)
        length = len(data) + 1

        # LCS (Length Checksum)
        lcs = (~length + 1) & 0xFF

        # TFI (Frame Identifier - Direction)
        tfi = 0xD4

        # Calcul du DCS (Data Checksum)
        dcs = tfi
        for d in data:
            dcs += d
        dcs = (~dcs + 1) & 0xFF

        # Postambule
        postamble = 0x00

        # Assemblage de la trame complète
        frame = preamble + [length, lcs, tfi] + data + [dcs, postamble]

        debug_print(f"Envoi trame: {' '.join([f'{b:02X}' for b in frame])}")

        # Écriture sur le bus I2C
        for i in range(0, len(frame), 16):  # Écrit par blocs de 16 octets max
            chunk = frame[i:i+16]
            debug_print(f"  Envoi chunk: {' '.join([f'{b:02X}' for b in chunk])}")
            try:
                bus.write_i2c_block_data(PN532_I2C_ADDRESS, chunk[0], chunk[1:])
                time.sleep(0.002)  # Petit délai entre les blocs
            except IOError as e:
                debug_print(f"Erreur I2C lors de l'écriture: {e}")
                # Essayons d'écrire octet par octet
                for byte in chunk:
                    try:
                        bus.write_byte(PN532_I2C_ADDRESS, byte)
                        time.sleep(0.001)
                    except IOError:
                        debug_print(f"Échec également octet par octet")

        time.sleep(DELAY_BETWEEN_COMMANDS)
        return True
    except Exception as e:
        print(f"Erreur d'écriture: {e}")
        return False

def read_frame(bus, timeout=1.0):
    """Lit une trame complète depuis le PN532 avec timeout"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Lire l'état de préparation
            ready = bus.read_byte(PN532_I2C_ADDRESS)
            debug_print(f"État de préparation: 0x{ready:02X}")

            if ready == 0x01:  # PN532 est prêt
                try:
                    # Lire la réponse - d'abord un bloc de données
                    data = bus.read_i2c_block_data(PN532_I2C_ADDRESS, 0, 16)
                    debug_print(f"Données lues: {' '.join([f'{b:02X}' for b in data])}")

                    # Vérifier le préambule
                    if data[0:3] != [0x00, 0x00, 0xFF]:
                        debug_print("Préambule invalide")
                        time.sleep(0.1)
                        continue

                    # Obtenir la longueur
                    length = data[3]

                    # Calculer la longueur totale de la trame
                    frame_len = length + 7  # préambule(3) + len(1) + lcs(1) + tfi(1) + data(length) + dcs(1) + postamble(1)

                    # Si on a besoin de plus de données
                    if len(data) < frame_len:
                        more_data = bus.read_i2c_block_data(PN532_I2C_ADDRESS, 0, frame_len - len(data))
                        data.extend(more_data)

                    debug_print(f"Trame complète: {' '.join([f'{b:02X}' for b in data])}")
                    return data
                except Exception as e:
                    debug_print(f"Erreur lors de la lecture de données: {e}")

            time.sleep(0.01)  # Petit délai avant de réessayer
        except Exception as e:
            debug_print(f"Erreur de lecture: {e}")
            time.sleep(0.1)

    print("Timeout en attendant la réponse")
    return None

def send_command(bus, command, params=None):
    """Envoie une commande et lit la réponse"""
    if params is None:
        params = []

    debug_print(f"Envoi commande 0x{command:02X} avec paramètres: {params}")

    # Assemblage de la commande
    cmd_data = [command] + params

    # Envoi de la commande
    if not write_frame(bus, cmd_data):
        print("Échec de l'envoi de la commande")
        return None

    # Attendre un moment pour que le PN532 traite la commande
    time.sleep(DELAY_RESPONSE_READ)

    # Lire la réponse
    response = read_frame(bus)
    if not response:
        return None

    # Vérifier la réponse
    if len(response) > 6 and response[5] == 0xD5 and response[6] == command + 1:
        # Retourne les données sans les entêtes et terminaisons
        return response[7:response[3]+6]

    debug_print("Réponse invalide")
    return None

def get_firmware_version(bus):
    """Obtient la version du firmware du PN532"""
    response = send_command(bus, CMD_GET_FIRMWARE_VERSION)
    if response and len(response) >= 4:
        return f"{response[1]}.{response[2]}"
    return None

def configure_sam(bus):
    """Configure le Secure Access Module"""
    # Normal mode, timeout = 0 (pas de timeout)
    params = [0x01, 0x00, 0x00]
    response = send_command(bus, CMD_SAM_CONFIGURATION, params)
    return response is not None

def read_passive_target(bus, max_tries=20):
    """Tente de lire un tag NFC"""
    # InListPassiveTarget: max 1 carte, 106 kbps type A
    params = [0x01, 0x00]

    for _ in range(max_tries):
        response = send_command(bus, CMD_LIST_PASSIVE_TARGET, params)
        if response:
            debug_print(f"Réponse cible passive: {' '.join([f'{b:02X}' for b in response])}")

            # Vérifier si une carte a été trouvée
            if response[0] == 0x01:  # Nombre de cibles trouvées
                # Analysons la réponse pour extraire l'UID
                target_data = response[1:]
                sens_res = target_data[1:3]
                sel_res = target_data[3]
                uid_len = target_data[4]
                uid = target_data[5:5+uid_len]

                return {
                    'sens_res': sens_res,
                    'sel_res': sel_res,
                    'uid': uid
                }
        time.sleep(0.1)

    return None

def main():
    print("Initialisation du lecteur NFC PN532...")

    try:
        # Ouvrir le bus I2C (bus 1 sur Raspberry Pi moderne)
        bus = SMBus(1)

        # Lire la version du firmware
        print("Lecture de la version du firmware...")
        firmware = get_firmware_version(bus)
        if not firmware:
            print("Impossible de lire la version du firmware. Vérifiez les connexions et l'adresse I2C.")
            return

        print(f"Version du firmware PN532: {firmware}")

        # Configurer le PN532
        print("Configuration du PN532...")
        if not configure_sam(bus):
            print("Échec de configuration du PN532")
            return

        print("Lecteur NFC prêt. Placez une carte ou un tag NFC près du lecteur...")
        print("Appuyez sur Ctrl+C pour quitter")

        # Boucle principale
        last_uid = None
        while True:
            tag = read_passive_target(bus)
            if tag:
                uid = tag['uid']
                uid_hex = ':'.join([f'{b:02X}' for b in uid])

                if uid != last_uid:
                    print(f"Tag détecté! UID: {uid_hex}")
                    last_uid = uid
            else:
                last_uid = None

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nProgramme arrêté par l'utilisateur")
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        try:
            bus.close()
        except:
            pass

if __name__ == "__main__":
    main()