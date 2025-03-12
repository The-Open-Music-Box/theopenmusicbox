# app/demo/light_sensor.py

import time
import smbus2

# Adresse I2C du BH1750
BH1750_ADDRESS = 0x23
CONTINUOUS_HIGH_RES_MODE = 0x10

class BH1750:
    def __init__(self, bus_num=1, address=BH1750_ADDRESS):
        self.bus = smbus2.SMBus(bus_num)
        self.address = address
        self.power_on()
        self.set_mode(CONTINUOUS_HIGH_RES_MODE)

    def power_on(self):
        self.bus.write_byte(self.address, 0x01)
        time.sleep(0.01)

    def set_mode(self, mode):
        self.bus.write_byte(self.address, mode)
        time.sleep(0.01)

    def read_light(self):
        try:
            data = self.bus.read_i2c_block_data(self.address, CONTINUOUS_HIGH_RES_MODE, 2)
            light = (data[0] << 8 | data[1]) / 1.2  # Convert to lux
            return light
        except Exception as e:
            print(f"Erreur: {e}")
            return -1

def main():
    try:
        sensor = BH1750()

        print("Capteur BH1750 - Ctrl+C pour quitter")
        print("------------------------------------")

        while True:
            lux = sensor.read_light()

            if lux >= 0:
                print(f"\rIntensité lumineuse: {lux:.2f} lux", end="")
            else:
                print("\rErreur de mesure      ", end="")

            time.sleep(0.5)  # 2 mesures par seconde

    except KeyboardInterrupt:
        print("\n\nProgramme arrêté")
    except Exception as e:
        print(f"\nErreur: {e}")

if __name__ == "__main__":
    main()