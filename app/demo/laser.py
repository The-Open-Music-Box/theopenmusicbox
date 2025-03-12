# app/demo/laser.py

import time
import smbus2

# Adresse I2C du VL53L0X
VL53L0X_ADDRESS = 0x29

class VL53L0X:
    def __init__(self, bus_num=1, address=VL53L0X_ADDRESS):
        self.bus = smbus2.SMBus(bus_num)
        self.address = address
        self.init_sensor()

    def init_sensor(self):
        try:
            # Vérifier l'ID du capteur
            device_id = self.read_byte(0xC0)
            print(f"Device ID: 0x{device_id:02X}")

            if device_id != 0xEE:
                print("Erreur: ID du capteur invalide")
                return False

            # Configuration simple du capteur
            self.write_byte(0x80, 0x01)
            self.write_byte(0xFF, 0x01)
            self.write_byte(0x00, 0x00)
            self.write_byte(0x91, 0x3C)
            self.write_byte(0x00, 0x01)
            self.write_byte(0xFF, 0x00)
            self.write_byte(0x80, 0x00)

            return True
        except Exception as e:
            print(f"Erreur: {e}")
            return False

    def read_byte(self, register):
        return self.bus.read_byte_data(self.address, register)

    def write_byte(self, register, value):
        self.bus.write_byte_data(self.address, register, value)

    def read_distance(self):
        try:
            # Démarrer la mesure
            self.write_byte(0x00, 0x01)

            # Attendre la fin de la mesure
            time.sleep(0.1)  # Attente fixe de 100ms

            # Lire la distance
            high = self.read_byte(0x1E)
            low = self.read_byte(0x1F)

            # Combiner les octets
            distance = (high << 8) | low

            return distance

        except Exception as e:
            print(f"Erreur: {e}")
            return -1

def main():
    try:
        sensor = VL53L0X()

        print("Capteur VL53L0X - Ctrl+C pour quitter")
        print("------------------------------------")

        while True:
            distance = sensor.read_distance()

            if distance > 0:
                print(f"\rDistance: {distance:4d} mm", end="")
            else:
                print("\rErreur de mesure      ", end="")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nProgramme arrêté")
    except Exception as e:
        print(f"\nErreur: {e}")

if __name__ == "__main__":
    main()