# School Access & Attendance System

An IoT-based access control system using ESP32, PN532 NFC reader, and Supabase for cloud logging. Contains a Streamlit dashboard for real-time monitoring.

## 📂 Project Structure

- `firmware/`: MicroPython code for the ESP32.
  - `boot.py`: Handles WiFi connection.
  - `main.py`: Core logic for access control and offline logging.
  - `pn532.py`: Minimal driver for PN532 (I2C).
  - `config.py`: Configuration file for credentials.
- `backend/`: Python code for the admin dashboard.
  - `dashboard.py`: Streamlit application.

## ⚙️ Hardware Setup

1. **ESP32** (Any standard dev board like NodeMCU-32S or ESP32-DevKitC)
2. **PN532 NFC Module** (V3 or similar)
   - **VCC** -> 3.3V
   - **GND** -> GND
   - **SDA** -> GPIO 21
   - **SCL** -> GPIO 22
   - **Dip Switches**: Set PN532 to I2C Mode (usually SET0=H, SET1=L).
3. **Relay Module**
   - **IN** -> GPIO 4
4. **Buzzer**
   - **POS** -> GPIO 5

## 🚀 Getting Started

### 1. Firmware (ESP32)

1. **Flash MicroPython** firmware to your ESP32.
2. Edit `firmware/config.py` with your WiFi and Supabase credentials.
3. Upload all files in `firmware/` to the ESP32 using Thonny or `ampy`.
   - `boot.py`
   - `main.py`
   - `pn532.py`
   - `config.py`
4. Reset the board. It should connect to WiFi and start scanning for cards.

### 2. Backend (Dashboard)

1. Navigate to `backend/` directory.
2. Create a `.env` file based on `.env.example` and add your Supabase credentials.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the dashboard:
   ```bash
   streamlit run dashboard.py
   ```

### 3. Supabase Setup

Run this SQL in your Supabase SQL Editor to create the logs table:

```sql
create table public.attendance_logs (
  id uuid default gen_random_uuid() primary key,
  student_uid text not null,
  status boolean not null,
  timestamp timeout with time zone default timezone('utc'::text, now()) not null
);
```

## ⚠️ Notes

- The `pn532.py` included is a minimal implementation. If you have issues reading cards, consider using a full featured library like [micropython-pn532](https://github.com/micropython/micropython-lib).
- The "Store and Forward" feature saves logs to `queue.txt` on the ESP32 if WiFi is down and retries every 60 seconds.
