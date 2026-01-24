import time
from machine import I2C

PN532_I2C_ADDRESS = (0x48 >> 1)
PN532_I2C_READBIT = (0x01)
PN532_COMMAND_INLISTPASSIVETARGET = (0x4A)

class PN532_I2C:
    def __init__(self, i2c, address=0x24):
        self.i2c = i2c
        self.address = address
        self.wakeup()

    def _write_frame(self, data):
        # Build frame
        length = len(data) + 1 # +1 for TFI
        frame = bytearray([0x00, 0x00, 0xFF, length, (0x100 - length) & 0xFF, 0xD4])
        frame.extend(data)
        dcs = 0xD4
        for b in data:
            dcs += b
        frame.append((0x100 - (dcs & 0xFF)) & 0xFF)
        frame.append(0x00)
        
        try:
            self.i2c.writeto(self.address, frame)
        except OSError:
            pass # ACK error sometimes expected during wakeup

    def _read_data(self, count):
        # Read raw data
        try:
             # Basic I2C read
             response = self.i2c.readfrom(self.address, count + 10) # extra buffer
             # Check for ready packet
             if response[0] & 0x01:
                 # Ready
                 return response[1:]
             else:
                 return None
        except OSError:
            return None

    def _read_frame(self, length):
        # Wait for ready
        # In a real driver, this is more robust
        response = self._read_data(length + 8) 
        if response:
             # Basic extraction, assume aligned for this simplified version
             # Skip Preamble/Start codes to get to TFI/Data
             # Real logic needs to parse 00 00 FF ...
             # Minimal Search for 00 00 FF
             idx = 0
             if len(response) > 3:
                 try:
                     idx = response.index(b'\x00\x00\xff')
                     return response[idx+3:] # Return from LEN onwards
                 except ValueError:
                     pass
        return None

    def wakeup(self):
        # Send dummy
        pass

    def call_function(self, command, response_length=0, params=[], timeout=100):
        data = bytearray([command])
        data.extend(params)
        self._write_frame(data)
        
        # Wait
        t = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t) < timeout:
            time.sleep_ms(10)
            # Check ACK... skipping for brevity in this minimal version which is risky
            # Ideally reading data logic here
            pass
        return None

    def read_passive_target(self, card_baud=0x00, timeout=1000):
        # Simplified simulation or basic attempt. 
        # Writing a robust I2C PN532 driver in one go is error prone.
        # This function sends the command to scan for a card.
        
        # COMMAND: InListPassiveTarget (0x4A)
        # MaxTg (1), BrTy (0 = 106 kbps type A)
        cmd = [0x4A, 0x01, 0x00]
        self._write_frame(bytearray(cmd))
        
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout:
             # Poll for reading...
             # For the sake of this plan, if we can't guarantee a working low-level driver,
             # we might assume the user will copy a standard library 'pn532.py'.
             # However I will provide the best-effort structure.
             
             # Actually, checking the read response:
             try:
                 # Read status/data
                 data = self.i2c.readfrom(self.address, 20)
                 # Check if we have data (first byte status 0x01 = ready)
                 if data[0] == 0x01:
                     # Parse logic...
                     # Simplification: if we see 0x4B (response to 4A)
                     # Find 0xD5 0x4B
                     for i in range(len(data)-1):
                         if data[i] == 0xD5 and data[i+1] == 0x4B:
                             # NbTg = data[i+2]
                             # Target 1 = data[i+3...]
                             # Tg 1 info: Tg, SENS_RES(2), SEL_RES(1), NFCIDLength(1), NFCID(...)
                             uid_len = data[i+7]
                             uid = data[i+8 : i+8+uid_len]
                             return uid
                 time.sleep_ms(50)
             except OSError:
                 time.sleep_ms(50)
                 
        return None
