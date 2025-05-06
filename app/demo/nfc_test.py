# app/demo/nfc.py

"""
Demonstration script for the PN532 NFC reader with improved debugging
"""
import time
import sys
from smbus2 import SMBus
import binascii

# PN532 I2C address
PN532_I2C_ADDRESS = 0x24  # Can be 0x24 or 0x48, to be verified

# PN532 Commands
CMD_GET_FIRMWARE_VERSION = 0x02
CMD_SAM_CONFIGURATION = 0x14
CMD_LIST_PASSIVE_TARGET = 0x4A
CMD_INDATA_EXCHANGE = 0x40

# Delays
DELAY_BETWEEN_COMMANDS = 0.05
DELAY_RESPONSE_READ = 0.1

# Debug activation
DEBUG = True

def debug_print(message):
    if DEBUG:
        print(f"DEBUG: {message}")

def write_frame(bus, data):
    """Sends a complete frame to the PN532"""
    try:
        # Preamble
        preamble = [0x00, 0x00, 0xFF]

        # Data length + 1 (for TFI)
        length = len(data) + 1

        # LCS (Length Checksum)
        lcs = (~length + 1) & 0xFF

        # TFI (Frame Identifier - Direction)
        tfi = 0xD4

        # Calculate DCS (Data Checksum)
        dcs = tfi
        for d in data:
            dcs += d
        dcs = (~dcs + 1) & 0xFF

        # Postamble
        postamble = 0x00

        # Assemble the complete frame
        frame = preamble + [length, lcs, tfi] + data + [dcs, postamble]

        debug_print(f"Sending frame: {' '.join([f'{b:02X}' for b in frame])}")

        # Write to I2C bus
        for i in range(0, len(frame), 16):  # Write in blocks of max 16 bytes
            chunk = frame[i:i+16]
            debug_print(f"  Sending chunk: {' '.join([f'{b:02X}' for b in chunk])}")
            try:
                bus.write_i2c_block_data(PN532_I2C_ADDRESS, chunk[0], chunk[1:])
                time.sleep(0.002)  # Small delay between blocks
            except IOError as e:
                debug_print(f"I2C error during write: {e}")
                # Let's try to write byte by byte
                for byte in chunk:
                    try:
                        bus.write_byte(PN532_I2C_ADDRESS, byte)
                        time.sleep(0.001)
                    except IOError:
                        debug_print(f"Byte by byte write also failed")

        time.sleep(DELAY_BETWEEN_COMMANDS)
        return True
    except Exception as e:
        print(f"Write error: {e}")
        return False

def read_frame(bus, timeout=1.0):
    """Reads a complete frame from the PN532 with timeout"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Read ready status
            ready = bus.read_byte(PN532_I2C_ADDRESS)
            debug_print(f"Ready status: 0x{ready:02X}")

            if ready == 0x01:  # PN532 is ready
                try:
                    # Read response - first a data block
                    data = bus.read_i2c_block_data(PN532_I2C_ADDRESS, 0, 16)
                    debug_print(f"Data read: {' '.join([f'{b:02X}' for b in data])}")

                    # Check preamble
                    if data[0:3] != [0x00, 0x00, 0xFF]:
                        debug_print("Invalid preamble")
                        time.sleep(0.1)
                        continue

                    # Get length
                    length = data[3]

                    # Calculate total frame length
                    frame_len = length + 7  # preamble(3) + len(1) + lcs(1) + tfi(1) + data(length) + dcs(1) + postamble(1)

                    # If we need more data
                    if len(data) < frame_len:
                        more_data = bus.read_i2c_block_data(PN532_I2C_ADDRESS, 0, frame_len - len(data))
                        data.extend(more_data)

                    debug_print(f"Complete frame: {' '.join([f'{b:02X}' for b in data])}")
                    return data
                except Exception as e:
                    debug_print(f"Error reading data: {e}")

            time.sleep(0.01)  # Small delay before retrying
        except Exception as e:
            debug_print(f"Read error: {e}")
            time.sleep(0.1)

    print("Timeout waiting for response")
    return None

def send_command(bus, command, params=None):
    """Sends a command and reads the response"""
    if params is None:
        params = []

    debug_print(f"Sending command 0x{command:02X} with parameters: {params}")

    # Assemble the command
    cmd_data = [command] + params

    # Send the command
    if not write_frame(bus, cmd_data):
        print("Failed to send command")
        return None

    # Wait a moment for the PN532 to process the command
    time.sleep(DELAY_RESPONSE_READ)

    # Read the response
    response = read_frame(bus)
    if not response:
        return None

    # Check the response
    if len(response) > 6 and response[5] == 0xD5 and response[6] == command + 1:
        # Return data without headers and terminators
        return response[7:response[3]+6]

    debug_print("Invalid response")
    return None

def get_firmware_version(bus):
    """Gets the PN532 firmware version"""
    response = send_command(bus, CMD_GET_FIRMWARE_VERSION)
    if response and len(response) >= 4:
        return f"{response[1]}.{response[2]}"
    return None

def configure_sam(bus):
    """Configures the Secure Access Module"""
    # Normal mode, timeout = 0 (no timeout)
    params = [0x01, 0x00, 0x00]
    response = send_command(bus, CMD_SAM_CONFIGURATION, params)
    return response is not None

def read_passive_target(bus, max_tries=20):
    """Attempts to read an NFC tag"""
    # InListPassiveTarget: max 1 card, 106 kbps type A
    params = [0x01, 0x00]

    for _ in range(max_tries):
        response = send_command(bus, CMD_LIST_PASSIVE_TARGET, params)
        if response:
            debug_print(f"Passive target response: {' '.join([f'{b:02X}' for b in response])}")

            # Check if a card was found
            if response[0] == 0x01:  # Number of targets found
                # Analyze the response to extract the UID
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
    print("Initializing NFC PN532 reader...")

    try:
        # Open I2C bus (bus 1 on modern Raspberry Pi)
        bus = SMBus(1)

        # Read firmware version
        print("Reading firmware version...")
        firmware = get_firmware_version(bus)
        if not firmware:
            print("Unable to read firmware version. Check connections and I2C address.")
            return

        print(f"PN532 firmware version: {firmware}")

        # Configure PN532
        print("Configuring PN532...")
        if not configure_sam(bus):
            print("Failed to configure PN532")
            return

        print("NFC reader ready. Place an NFC card or tag near the reader...")
        print("Press Ctrl+C to quit")

        # Main loop
        last_uid = None
        while True:
            tag = read_passive_target(bus)
            if tag:
                uid = tag['uid']
                uid_hex = ':'.join([f'{b:02X}' for b in uid])

                if uid != last_uid:
                    print(f"Tag detected! UID: {uid_hex}")
                    last_uid = uid
            else:
                last_uid = None

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            bus.close()
        except:
            pass

if __name__ == "__main__":
    main()
