# 🏫 EduQure - School Access & Attendance Management System

**A comprehensive IoT-based access control and attendance tracking system designed for South African schools**

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Platform](https://img.shields.io/badge/platform-ESP32-blue.svg)]()
[![Framework](https://img.shields.io/badge/framework-Streamlit-red.svg)]()
[![Database](https://img.shields.io/badge/database-Supabase-green.svg)]()

---

## 📋 Table of Contents

- [High-Level Overview](#-high-level-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Documentation](#-documentation)
- [Use Cases](#-use-cases)
- [Technology Stack](#-technology-stack)
- [Database Schema](#-database-schema)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 High-Level Overview

**EduQure** is a hybrid hardware-software solution that automates student access control and attendance tracking for schools. The system consists of three main components:

### 1. **Hardware Layer** (Firmware)
- **ESP32** microcontroller with **MFRC522 RFID reader**
- NFC card-based access validation (13.56MHz)
- Physical control of solenoid locks via relay
- Visual (LED) and audio (buzzer) feedback
- **Offline resilience** with local queue storage

### 2. **Cloud Backend** (Supabase/PostgreSQL)
- Stores attendance logs and access events
- Manages authorized card database
- Row-Level Security (RLS) for multi-tenant architecture
- Real-time data synchronization

### 3. **Web Dashboard** (Streamlit)
- **Live Monitoring**: Real-time access events
- **Choir Attendance**: Specialized tracking for choir practices with manual overrides
- **Access Logs**: Historical data with in/out direction tracking
- **Admin Interface**: User authentication and data management

---

## ✨ Key Features

### 🔐 **Automated Access Control**
- NFC card-based entry validation
- Grant/deny access with relay-controlled locks
- Visual and audio feedback (LEDs, buzzer)
- Unidentified card logging for security

### 📊 **Intelligent Attendance Tracking**
- Automatic logging on card scan
- Manual attendance override (for forgotten cards)
- Excuse tracking system
- Yearly attendance reports and statistics

### ⚡ **Load-Shedding Resilient**
- Offline queue system stores logs locally
- Auto-sync when connectivity restored
- Designed for South African infrastructure
- UPS backup support

### 🎵 **Specialized Choir Module**
- Practice date scheduling
- Attendance vs. excuse tracking (mutually exclusive)
- Automatic presence detection via NFC
- Yearly reports with attendance percentages

### 🔄 **Dynamic Card Management**
- Card whitelist synced from database hourly
- No firmware updates needed to add/remove cards
- Cached locally for offline operation
- SPIFFS-based persistent storage

### 🌐 **Multi-Tenant Architecture**
- Row Level Security (RLS) in PostgreSQL
- Isolated data per school
- Scalable cloud or on-premise deployment

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   ESP32 RFID    │────────▶│   Supabase       │◀────────│   Streamlit     │
│   Scanner       │  HTTPS  │   (PostgreSQL)   │  HTTPS  │   Dashboard     │
│                 │         │                  │         │                 │
│ - MFRC522 NFC   │         │ - access_logs    │         │ Tabs:           │
│ - Solenoid Lock │         │ - persons        │         │ - Choir Attend. │
│ - LED/Buzzer    │         │ - choir_practice │         │ - Live Monitor  │
│ - Offline Queue │         │ - unidentified   │         │ - Access Logs   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
      ▲                              ▲                          ▲
      │                              │                          │
   Card Scan ──▶ Validate ──▶ Log Event         Admin View/Edit Data
```

### Data Flow

1. **Card Scan** → ESP32 reads NFC card UID
2. **Validation** → Check against cached whitelist
3. **Physical Action** → Grant (unlock) or Deny (beep)
4. **Cloud Logging** → Send event to Supabase (or queue if offline)
5. **Dashboard View** → Real-time display in Streamlit

---

## 📂 Project Structure

```
EduQure/
├── firmware/                       # ESP32 embedded code
│   ├── boot.py                     # Legacy: MicroPython WiFi init
│   ├── main.py                     # Legacy: MicroPython main logic
│   ├── pn532.py                    # Legacy: PN532 NFC driver
│   ├── config.py                   # Legacy: MicroPython config
│   ├── rfidCard_scanner/           # ✅ ACTIVE Arduino firmware
│   │   ├── rfidCard_scanner.ino    # Main sketch
│   │   ├── access_control.h        # Physical control (relay, LEDs, buzzer)
│   │   ├── network_manager.h       # WiFi & Supabase HTTP sync
│   │   ├── offline_queue.h         # Offline log queue (SPIFFS)
│   │   ├── card_manager.h          # Dynamic card whitelist
│   │   ├── secrets.h               # WiFi/API credentials (DO NOT COMMIT)
│   │   └── secrets.example.h       # Template for secrets
│   └── README.md                   # Firmware documentation
│
├── client/                         # Streamlit web dashboard
│   ├── secured_dashboard.py        # Main app entry point
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment variables (DO NOT COMMIT)
│   ├── .env.example                # Template for .env
│   ├── .streamlit/                 # Streamlit configuration
│   │   └── config.toml             # UI theme settings
│   ├── tabs/                        # Dashboard tab modules
│   │   ├── choir_attendance.py     # Choir practice attendance
│   │   ├── live_monitor.py         # Real-time monitoring
│   │   └── access_logs.py          # Historical logs
│   ├── utils/                      # Utility modules
│   │   ├── supabase_client.py      # Database client
│   │   └── auth.py                 # Authentication
│   └── README.md                   # Client documentation
│
├── README.md                       # This file (project overview)
├── DOCUMENTATION_INDEX.md          # Index of all documentation
└── This proposal and project plan are.txt  # Original project proposal
```

---

## 🚀 Quick Start

### Prerequisites

- **Hardware**: ESP32, MFRC522 RFID reader, relay module, LEDs, buzzer
- **Software**: Arduino IDE, Python 3.8+
- **Cloud**: Supabase account (free tier works)

### 1. Setup Firmware (ESP32)

```bash
# 1. Install Arduino IDE and ESP32 board support
# 2. Install libraries: MFRC522, ArduinoJson
# 3. Navigate to firmware/rfidCard_scanner/
cd firmware/rfidCard_scanner/

# 4. Copy secrets template
cp secrets.example.h secrets.h

# 5. Edit secrets.h with your credentials
# 6. Open rfidCard_scanner.ino in Arduino IDE
# 7. Upload to ESP32
```

**Detailed instructions:** [firmware/README.md](firmware/README.md)

### 2. Setup Dashboard (Client)

```bash
# 1. Navigate to client directory
cd client/

# 2. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your Supabase credentials

# 6. Run dashboard
streamlit run secured_dashboard.py
```

**Detailed instructions:** [client/README.md](client/README.md)

### 3. Setup Supabase Database

```sql
-- Run these SQL commands in Supabase SQL Editor

-- 1. Persons table
CREATE TABLE persons (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  surname TEXT NOT NULL,
  card_uid TEXT UNIQUE,
  grade TEXT,
  is_choir BOOLEAN DEFAULT FALSE,
  choir_year INTEGER
);

-- 2. Access logs table
CREATE TABLE access_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  card_uid TEXT NOT NULL,
  lock TEXT,
  status BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  person_id UUID REFERENCES persons(id)
);

-- 3. Unidentified cards table
CREATE TABLE unidentified_cards (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  card_uid TEXT NOT NULL,
  lock TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Choir practice dates table
CREATE TABLE choir_practice_dates (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  practice_date DATE UNIQUE NOT NULL,
  year INTEGER
);

-- 5. Manual choir attendance table
CREATE TABLE manual_choir_attendance (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  person_id UUID REFERENCES persons(id),
  practice_date_id UUID REFERENCES choir_practice_dates(id),
  present BOOLEAN DEFAULT FALSE,
  excuse BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(person_id, practice_date_id)
);

-- Enable Row Level Security (RLS)
ALTER TABLE persons ENABLE ROW LEVEL SECURITY;
ALTER TABLE access_logs ENABLE ROW LEVEL SECURITY;
-- ... (repeat for other tables)

-- Create policies (allow authenticated users to read/write)
CREATE POLICY "Allow all for authenticated" ON persons
  FOR ALL USING (auth.role() = 'authenticated');
-- ... (repeat for other tables)
```

---

## 📖 Documentation

### Main Documentation
- **[Project Overview](README.md)** - This file
- **[Firmware Guide](firmware/README.md)** - Hardware setup and Arduino code
- **[Client Guide](client/README.md)** - Dashboard setup and usage
- **[Documentation Index](DOCUMENTATION_INDEX.md)** - Complete file listing

### File-Specific Documentation
- [firmware/boot.md](firmware/boot.md) - Legacy WiFi initialization
- [firmware/main.md](firmware/main.md) - Legacy main logic
- [firmware/pn532.md](firmware/pn532.md) - Legacy NFC driver
- [firmware/config.md](firmware/config.md) - Legacy configuration
- [client/utils/supabase_client.md](client/utils/supabase_client.md) - Database client

### Code Examples
See individual .md files for detailed usage examples and API documentation.

---

## 🎭 Use Cases

### 1. School Gate Access Control
- Students scan NFC cards at entrance
- Automatic unlock for authorized cards
- Log all entry/exit events with timestamps
- Track who's currently on school premises (IN/OUT tracking)

### 2. Choir Practice Attendance
- Automatic attendance via card scan
- Manual override for forgotten cards
- Excuse submission tracking
- Yearly attendance reports for choir director

### 3. Security Monitoring
- Real-time alerts for unidentified cards
- Historical access logs for investigations
- Multi-gate deployment with lock identification

### 4. Offline Operation (Load-Shedding)
- Queue logs locally when internet down
- Auto-sync when connectivity restored
- Continue operation with UPS battery backup

---

## 🛠️ Technology Stack

### Hardware
- **ESP32** - WiFi-enabled microcontroller
- **MFRC522** - 13.56MHz RFID reader
- **12V Solenoid Lock** - Electromagnetic door lock
- **5V Relay Module** - Lock control interface
- **LEDs** - Visual feedback (green/red)
- **Buzzer** - Audio feedback

### Firmware
- **Arduino C++** - Embedded code
- **MFRC522 Library** - NFC communication
- **ArduinoJson** - JSON parsing
- **HTTPClient** - REST API communication
- **SPIFFS** - File system for offline queue

### Backend
- **Supabase** - Backend-as-a-Service
- **PostgreSQL** - Relational database
- **PostgREST** - Auto-generated REST API
- **Row Level Security (RLS)** - Multi-tenant isolation

### Frontend (Dashboard)
- **Streamlit** - Python web framework
- **Pandas** - Data manipulation
- **Python Supabase Client** - Database SDK
- **Python DotEnv** - Environment management

---

## 🗄️ Database Schema

### Key Tables

| Table | Description | Key Columns |
|-------|-------------|-------------|
| **persons** | Student/staff records | id, name, surname, card_uid, grade, is_choir |
| **access_logs** | Successful access events | id, card_uid, status, created_at, person_id |
| **unidentified_cards** | Unknown card scans | id, card_uid, created_at, lock |
| **choir_practice_dates** | Scheduled practice dates | id, practice_date, year |
| **manual_choir_attendance** | Attendance overrides | id, person_id, practice_date_id, present, excuse |

### Relationships

```
persons (1) ──< (M) access_logs
persons (1) ──< (M) manual_choir_attendance
choir_practice_dates (1) ──< (M) manual_choir_attendance
```

---

## 🐛 Troubleshooting

### ESP32 Not Connecting to WiFi
- Verify SSID/password in `secrets.h`
- Ensure 2.4GHz network (ESP32 doesn't support 5GHz)
- Check Serial Monitor output at 115200 baud

### Cards Not Reading
- Verify MFRC522 wiring (SDA=GPIO5, RST=GPIO22)
- Check card is 13.56MHz compatible (Mifare, NTAG, etc.)
- Ensure proper power supply (stable 3.3V to reader)

### Dashboard Won't Load Data
- Check `.env` has correct Supabase URL and key
- Verify RLS policies allow access for anon key
- Test Supabase connection in browser

### Logs Not Uploading
- Check ESP32 WiFi connection
- Verify Supabase URL and API key in `secrets.h`
- Review Serial Monitor for HTTP error codes

**See detailed troubleshooting in:**
- [firmware/README.md](firmware/README.md#troubleshooting)
- [client/README.md](client/README.md#troubleshooting)

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add documentation
5. Submit a pull request

---

## 📄 License

This project is for educational purposes. Modify as needed for your use case.

---

## 🙏 Acknowledgments

- Designed for **South African school environments**
- Optimized for **load-shedding resilience**
- Built with **open-source technologies**

---

## 📞 Support

For issues or questions:
1. Check the documentation in each directory
2. Review the [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
3. Open an issue on the repository

---

**Status:** ✅ Active Development | **Version:** 2.1 | **Last Updated:** January 2026
