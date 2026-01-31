# Firmware Directory

This directory contains the embedded firmware for the **ESP32-based RFID access control system**. The firmware handles card scanning, access validation, network communication, and offline resilience.

## 📂 Directory Structure

```
firmware/
├── boot.py                 # MicroPython WiFi initialization (legacy)
├── main.py                 # MicroPython main logic (legacy)
├── pn532.py               # PN532 NFC driver for MicroPython (legacy)
├── config.py              # Configuration file (legacy)
└── rfidCard_scanner/      # Arduino/ESP32 C++ implementation (ACTIVE)
    ├── rfidCard_scanner.ino    # Main Arduino sketch
    ├── access_control.h        # Access control logic (relay, buzzer)
    ├── network_manager.h       # WiFi and Supabase HTTP integration
    ├── offline_queue.h         # Offline log queue management
    ├── card_manager.h          # Card whitelist management
    ├── secrets.h               # WiFi and API credentials (DO NOT COMMIT)
    └── secrets.example.h       # Template for secrets file
```

## 🎯 Purpose

The firmware is responsible for:

1. **Card Reading**: Using MFRC522 RFID reader to scan NFC cards
2. **Access Validation**: Checking scanned card UIDs against a cached whitelist
3. **Physical Control**: Activating relay (solenoid lock) and buzzer based on access rights
4. **Cloud Logging**: Sending real-time attendance logs to Supabase
5. **Offline Resilience**: Queuing logs when internet is unavailable and syncing when restored
6. **Dynamic Card Sync**: Hourly updates of authorized card UIDs from the database

## ⚙️ Hardware Requirements

- **ESP32** development board (ESP32-DevKitC or similar)
- **MFRC522 RFID Module** (13.56MHz)
  - VCC → 3.3V
  - GND → GND
  - SDA (SS) → GPIO 5
  - SCK → GPIO 18
  - MOSI → GPIO 23
  - MISO → GPIO 19
  - RST → GPIO 22
- **Relay Module** (5V or 3.3V compatible)
  - Signal → GPIO 4
- **Buzzer** (active or passive)
  - Signal → GPIO 13
- **LED Indicators** (optional)
  - Green LED → GPIO 25
  - Red LED → GPIO 26
- **12V Solenoid Lock** (connected through relay)
- **12V DC Power Supply** with UPS backup (optional but recommended)

## 🚀 Getting Started

### 1. Arduino IDE Setup

1. Install [Arduino IDE](https://www.arduino.cc/en/software)
2. Add ESP32 board support:
   - Go to **File → Preferences**
   - Add to "Additional Board Manager URLs": 
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to **Tools → Board → Boards Manager**
   - Search for "ESP32" and install "esp32 by Espressif Systems"

### 2. Install Required Libraries

Install these libraries via **Sketch → Include Library → Manage Libraries**:

- **MFRC522** by GithubCommunity
- **ArduinoJson** by Benoit Blanchon (version 6.x)

### 3. Configure Secrets

1. Navigate to `rfidCard_scanner/`
2. Copy `secrets.example.h` to `secrets.h`
3. Edit `secrets.h` with your credentials:

```cpp
#define WIFI_SSID "YourNetworkName"
#define WIFI_PASSWORD "YourNetworkPassword"
#define SUPABASE_URL "https://yourproject.supabase.co"
#define SUPABASE_ANON_KEY "your.anon.key.here"
```

### 4. Upload Firmware

1. Connect ESP32 via USB
2. Select **Tools → Board → ESP32 Dev Module**
3. Select the correct **Port** (COM port on Windows, /dev/ttyUSB on Linux)
4. Click **Upload** (→ button)

### 5. Monitor Serial Output

Open **Tools → Serial Monitor** and set baud rate to **115200** to view logs:

```
--- School Access System v2.1 (Dynamic Sync) ---
Connecting to WiFi...
WiFi Connected! IP: 192.168.1.150
Syncing cards from DB...
Loaded 45 authorized cards
System Online
Scan your RFID card...
```

## 📡 How It Works

### Startup Sequence

1. **Initialize Hardware**: SPI, RFID reader, relay, buzzer, LEDs
2. **Load Cached Cards**: Read previously synced card UIDs from SPIFFS storage
3. **Connect to WiFi**: Attempt network connection
4. **Sync Card Database**: If online, fetch latest authorized cards from Supabase
5. **Enter Main Loop**: Begin scanning for RFID cards

### Main Loop

1. **Background Tasks** (every 60s):
   - Process offline queue (retry failed log uploads)
   - Sync card database (every 1 hour)

2. **Card Scan Event**:
   - Read card UID
   - Check against authorized card list
   - Grant or deny access (relay + LED + buzzer)
   - Log event to Supabase (or queue if offline)

### Offline Operation

- If WiFi is unavailable, the system continues to work using cached cards
- Failed log uploads are saved to `/queue.txt` in SPIFFS
- Every 60 seconds, the system retries sending queued logs
- Cards are synced hourly when connectivity is restored

## 🔧 File Descriptions

See individual file READMEs for detailed documentation:

- [boot.py](boot.md) - Legacy MicroPython WiFi setup
- [main.py](main.md) - Legacy MicroPython main logic
- [pn532.py](pn532.md) - Legacy PN532 NFC driver
- [config.py](config.md) - Legacy configuration file
- [rfidCard_scanner.ino](rfidCard_scanner/rfidCard_scanner.md) - Main Arduino sketch
- [access_control.h](rfidCard_scanner/access_control.md) - Access control module
- [network_manager.h](rfidCard_scanner/network_manager.md) - Network and API module
- [offline_queue.h](rfidCard_scanner/offline_queue.md) - Offline queue module
- [card_manager.h](rfidCard_scanner/card_manager.md) - Card management module
- [secrets.h](rfidCard_scanner/secrets.md) - Credentials configuration

## 🐛 Troubleshooting

### Card Not Detected
- Check RFID module wiring (especially SDA/SCL for PN532, or SPI pins for MFRC522)
- Verify card is 13.56MHz compatible (Mifare Classic, Ultralight, NTAG, etc.)
- Check Serial Monitor for initialization messages

### WiFi Not Connecting
- Verify SSID and password in `secrets.h`
- Check if 2.4GHz network (ESP32 doesn't support 5GHz)
- Try reducing WiFi timeout in `network_manager.h`

### Relay Not Activating
- Check relay module power (some need 5V, others work with 3.3V)
- Verify GPIO pin assignment matches your wiring
- Test relay manually with digitalWrite() in setup()

### Logs Not Uploading
- Verify Supabase URL and anon key
- Check Row Level Security (RLS) policies in Supabase
- Review Serial Monitor for HTTP error codes

## 📝 Notes

- **Legacy MicroPython Files**: The `boot.py`, `main.py`, `pn532.py`, and `config.py` files are from an earlier MicroPython implementation. The current active implementation uses Arduino C++ in the `rfidCard_scanner/` directory.
  
- **Security**: Never commit `secrets.h` to version control. Add it to `.gitignore`.

- **Load Shedding**: The system is designed for South African infrastructure. Consider adding a UPS or battery backup to the 12V power supply for uninterrupted operation during power outages.

- **Card Format**: Card UIDs are stored in hex format with `0x` prefix (e.g., `0x1a2b3c4d`).

## 🔐 Security Considerations

- Use environment variables or encrypted storage for production deployments
- Implement HTTPS for all API calls (Supabase uses HTTPS by default)
- Enable Row Level Security (RLS) in Supabase to isolate school data
- Consider using API keys with limited permissions (not service_role key)
- Physically secure the ESP32 device to prevent tampering

## 🛠️ Future Enhancements

- [ ] Implement encrypted card storage
- [ ] Add LCD display for user feedback
- [ ] Support for keypad + PIN backup access
- [ ] Battery voltage monitoring
- [ ] Bi-directional sync (download cards, upload configurations)
- [ ] Over-the-air (OTA) firmware updates
