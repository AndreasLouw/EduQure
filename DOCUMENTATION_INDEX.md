# 📚 File Documentation Index

This document provides a complete index of all documentation files in the EduQure project.

---

## 📂 Main Documentation

| File | Description | Location |
|------|-------------|----------|
| **[README.md](README.md)** | Complete project overview and getting started guide | Root |
| **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** | This file - index of all documentation | Root |
| **[firmware/README.md](firmware/README.md)** | Firmware overview and hardware setup guide | `/firmware` |
| **[client/README.md](client/README.md)** | Dashboard setup and usage guide | `/client` |

---

## 🔧 Firmware Documentation

### Main Directory (firmware/)

| File | Description | Status |
|------|-------------|--------|
| **[firmware/README.md](firmware/README.md)** | Complete firmware setup guide with hardware wiring | ✅ Active |
| Legacy files (boot.py, main.py, pn532.py, config.py) | Old MicroPython implementation | 🗑️ **Removed** |

### Active Arduino Firmware (firmware/rfidCard_scanner/)

| File | Description | Status |
|------|-------------|--------|
| **[rfidCard_scanner/README.md](firmware/rfidCard_scanner/README.md)** | Complete Arduino firmware documentation | ✅ Active |
| `rfidCard_scanner.ino` | Main Arduino sketch | ✅ Active |
| `access_control.h` | Physical access control (relay, LEDs, buzzer) | ✅ Active |
| `network_manager.h` | WiFi and Supabase HTTP communication | ✅ Active |
| `offline_queue.h` | SPIFFS-based offline log queue | ✅ Active |
| `card_manager.h` | Dynamic card whitelist management | ✅ Active |
| `secrets.h` | WiFi and API credentials | ⚠️ **DO NOT COMMIT** |
| `secrets.example.h` | Template for secrets file | ✅ Active |

---

## 💻 Client Documentation

### Main Directory (client/)

| File | Description | Status |
|------|-------------|--------|
| **[client/README.md](client/README.md)** | Complete dashboard setup and usage guide | ✅ Active |
| `secured_dashboard.py` | Main Streamlit application entry point | ✅ Active |
| `requirements.txt` | Python package dependencies | ✅ Active |
| `.env` | Environment variables | ⚠️ **DO NOT COMMIT** |
| `.env.example` | Template for environment variables | ✅ Active |

### Utility Modules (client/utils/)

| File | Description | Documentation | Status |
|------|-------------|---------------|--------|
| `supabase_client.py` | Supabase database client initialization | **[supabase_client.md](client/utils/supabase_client.md)** | ✅ Active |
| `auth.py` | Authentication and session management | *(See client README)* | ✅ Active |
| `__init__.py` | Utils package initialization | - | ✅ Active |

### Dashboard Tabs (client/tabs/)

| File | Description | Status |
|------|-------------|--------|
| `choir_attendance.py` | Choir practice attendance tracking with manual overrides | ✅ Active |
| `live_monitor.py` | Real-time monitoring of unidentified card scans | ✅ Active |
| `access_logs.py` | Historical access logs with IN/OUT tracking | ✅ Active |
| `__init__.py` | Tabs package initialization | ✅ Active |

### Configuration (client/.streamlit/)

| File | Description | Status |
|------|-------------|--------|
| `config.toml` | Streamlit UI theme and server settings | ✅ Active |

---

## 🚀 Quick Navigation

### 🆕 **New to the Project?**
1. Start with **[README.md](README.md)** - Project overview
2. Read **[firmware/README.md](firmware/README.md)** - Hardware setup
3. Read **[client/README.md](client/README.md)** - Dashboard setup

### 🔨 **Setting Up Hardware?**
1. **[firmware/README.md](firmware/README.md)** - Complete hardware guide
2. **[firmware/rfidCard_scanner/README.md](firmware/rfidCard_scanner/README.md)** - Arduino firmware details
3. Configure `secrets.h` with WiFi and Supabase credentials

### 💻 **Setting Up Dashboard?**
1. **[client/README.md](client/README.md)** - Installation and setup
2. **[client/utils/supabase_client.md](client/utils/supabase_client.md)** - Database connection
3. Configure `.env` with Supabase credentials

### 🐛 **Troubleshooting Issues?**
- **Hardware issues:** See [firmware/rfidCard_scanner/README.md](firmware/rfidCard_scanner/README.md) - Extensive troubleshooting section
- **Dashboard issues:** See [client/README.md](client/README.md) - Common problems and solutions
- **Database issues:** Check Supabase RLS policies and connection settings

### 🎯 **Understanding Specific Features?**
- **Choir Attendance System:** See [client/README.md](client/README.md) - Choir Attendance section
- **Offline Queue:** See [firmware/rfidCard_scanner/README.md](firmware/rfidCard_scanner/README.md) - Offline resilience
- **Card Management:** See [firmware/rfidCard_scanner/README.md](firmware/rfidCard_scanner/README.md) - Dynamic card sync
- **Authentication:** See [client/utils/supabase_client.md](client/utils/supabase_client.md)

---

## 📖 Documentation Standards

All README files in this project follow this structure:

### Standard Sections
1. **📋 Overview/Purpose** - What the component does
2. **🎯 Key Features/Components** - Main functionality
3. **⚙️ Configuration** - Required settings and credentials
4. **🚀 Installation/Setup** - Step-by-step guide
5. **📊 Usage/Operation** - How to use it
6. **🐛 Troubleshooting** - Common issues and solutions
7. **🔐 Security** - Best practices and warnings
8. **📚 Related Documentation** - Cross-references

### Format Guidelines
- Use emojis for visual navigation
- Include code examples where relevant
- Add diagrams for complex flows
- Provide troubleshooting for common errors
- Cross-reference related documentation

---

## 🔄 Project Structure Overview

```
EduQure/
│
├── 📄 README.md                           ← Start here!
├── 📄 DOCUMENTATION_INDEX.md              ← This file
│
├── 📁 firmware/
│   ├── 📄 README.md                       ← Hardware setup guide
│   ├── 📁 rfidCard_scanner/              ← Active firmware
│   │   ├── 📄 README.md                   ← Complete firmware docs
│   │   ├── 📄 rfidCard_scanner.ino        ← Main sketch
│   │   ├── 📄 access_control.h
│   │   ├── 📄 network_manager.h
│   │   ├── 📄 offline_queue.h
│   │   ├── 📄 card_manager.h
│   │   ├── 📄 secrets.h                   ⚠️ DO NOT COMMIT
│   │   └── 📄 secrets.example.h
│   └── 🗑️ (Legacy MicroPython files removed)
│
└── 📁 client/
    ├── 📄 README.md                       ← Dashboard guide
    ├── 📄 secured_dashboard.py
    ├── 📄 requirements.txt
    ├── 📄 .env                            ⚠️ DO NOT COMMIT
    ├── 📄 .env.example
    ├── 📁 .streamlit/
    │   └── 📄 config.toml
    ├── 📁 tabs/
    │   ├── 📄 choir_attendance.py
    │   ├── 📄 live_monitor.py
    │   ├── 📄 access_logs.py
    │   └── 📄 __init__.py
    └── 📁 utils/
        ├── 📄 supabase_client.py          ← Has dedicated .md
        ├── 📄 supabase_client.md
        ├── 📄 auth.py
        └── 📄 __init__.py
```

---

## ⚠️ Important Files (DO NOT COMMIT)

These files contain sensitive credentials and should **NEVER** be committed to version control:

| File | Purpose | Add to .gitignore |
|------|---------|------------------|
| `firmware/rfidCard_scanner/secrets.h` | WiFi and Supabase credentials for ESP32 | ✅ Required |
| `client/.env` | Supabase credentials for dashboard | ✅ Required |

**Instead, use these templates:**
- `firmware/rfidCard_scanner/secrets.example.h` ✅ Safe to commit
- `client/.env.example` ✅ Safe to commit

---

## 🆘 Getting Help

1. **Check relevant README:**
   - Hardware: [firmware/rfidCard_scanner/README.md](firmware/rfidCard_scanner/README.md)
   - Dashboard: [client/README.md](client/README.md)

2. **Review troubleshooting sections** in each README

3. **Check Serial Monitor** (ESP32) or **Terminal Output** (Dashboard) for error messages

4. **Verify configuration:**
   - `secrets.h` has correct WiFi/Supabase credentials
   - `.env` has correct Supabase credentials
   - Supabase RLS policies are configured

---

## 🤝 Contributing Documentation

When adding new features or files:

1. **Create corresponding documentation**
   - For new `.h` files: Add section to [firmware/rfidCard_scanner/README.md](firmware/rfidCard_scanner/README.md)
   - For new `.py` files: Add section to [client/README.md](client/README.md)
   - For complex modules: Create dedicated `.md` file

2. **Update this index** with the new documentation

3. **Follow documentation standards** (see above)

4. **Add cross-references** to related documentation

---

**Last Updated:** January 31, 2026  
**Project Version:** 2.1  
**Status:** ✅ Documentation Complete
