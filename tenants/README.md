# Multi-Tenant IoT Platform - Tenants

This directory contains tenant-specific configurations for the multi-tenant IoT platform.

## 🏗️ Structure

Each tenant has its own subdirectory containing:

```
tenants/
├── eduqure/
│   ├── tenant.config.json    # Tenant configuration
│   ├── README.md              # Tenant-specific documentation
│   └── migrations/            # Database migrations (optional)
├── gymtrack/
│   └── tenant.config.json
└── farmsense/
    └── tenant.config.json
```

## 📋 Tenant Configuration Format

Each `tenant.config.json` file defines:

### 1. **Tenant Identity**
- `tenant_id`: Unique identifier (lowercase, no spaces)
- `tenant_name`: Display name
- `tenant_type`: Type of application (e.g., "access_control", "environmental_monitoring")
- `device_type`: IoT device type (e.g., "rfid_reader", "sensor_array")

### 2. **Database Schema**
- `schema_prefix`: Prefix for all database tables
- `tables`: Complete table definitions with columns, types, and constraints

### 3. **Firmware Configuration**
- `device_type`: Hardware platform (e.g., "esp32_rfid", "esp32_cellular")
- `template`: Firmware template to use
- `sensors`: List of sensors with pin configurations
- `actuators`: List of actuators (relays, LEDs, etc.)
- `features`: Enabled firmware features
- `endpoints`: API endpoints for data logging

### 4. **Dashboard Configuration**
- `title`: Dashboard title
- `tabs`: List of dashboard tabs to display
  - `id`: Tab identifier
  - `name`: Tab display name
  - `module`: Python module path
  - `enabled`: Whether tab is active

## 🚀 Creating a New Tenant

### Step 1: Create Tenant Directory

```bash
mkdir tenants/mytenant
```

### Step 2: Create Configuration File

Copy an existing `tenant.config.json` and modify:

```bash
cp tenants/eduqure/tenant.config.json tenants/mytenant/tenant.config.json
```

Edit the file to match your requirements.

### Step 3: Generate Database Migration

```bash
python scripts/generate_migration.py --tenant mytenant --output migrations/mytenant_initial.sql
```

### Step 4: Apply Migration

Execute the generated SQL in your Supabase SQL Editor.

### Step 5: Verify Configuration

```bash
python scripts/list_tenants.py --verbose
```

## 📦 Existing Tenants

### EduQure - School Attendance
- **Type**: Access Control
- **Device**: ESP32 + MFRC522 RFID Reader
- **Use Case**: School attendance tracking with choir management
- **Tables**: persons, access_logs, choir_practice_dates, choir_register, manual_choir_attendance

### GymTrack - Fitness Membership
- **Type**: Access Control
- **Device**: ESP32 + MFRC522 RFID Reader
- **Use Case**: Gym member check-ins with points system
- **Tables**: members, check_ins, points_ledger

### FarmSense - Agricultural Monitoring
- **Type**: Environmental Monitoring
- **Device**: ESP32 + DHT22 + Soil Moisture Sensor
- **Use Case**: Field temperature and moisture monitoring with cellular connectivity
- **Tables**: fields, sensor_readings, alerts

## 🔧 Configuration Best Practices

1. **Unique Schema Prefix**: Each tenant must have a unique `schema_prefix` to avoid table conflicts

2. **Consistent Naming**: Use lowercase, underscores for multi-word names

3. **Device Compatibility**: Ensure your firmware template matches the hardware

4. **Dashboard Modules**: Create tenant-specific dashboard tabs in `client/tabs/{tenant_id}/`

5. **API Endpoints**: Ensure firmware endpoints match your database table names

## 🛠️ Validation

Tenant configurations are automatically validated when loaded. Check for:

- ✅ Required fields present
- ✅ Valid JSON format
- ✅ Database schema properly defined
- ✅ Dashboard tabs reference existing modules
- ✅ Firmware configuration matches device type

Run validation:

```bash
python scripts/list_tenants.py --verbose
```

## 📚 Additional Resources

- [Implementation Plan](../implementation_plan.md) - Overall platform architecture
- [Database Manager](../platform_core/database_manager.py) - Schema generation logic
- [Tenant Manager](../platform_core/tenant_manager.py) - Configuration loading

## 🆘 Troubleshooting

**Configuration not loading?**
- Check JSON syntax for errors
- Ensure `tenant_id` matches directory name
- Verify all required fields are present

**Database tables not creating?**
- Generate migration: `python scripts/generate_migration.py --tenant mytenant`
- Review SQL before executing
- Check for foreign key dependencies

**Dashboard not showing tabs?**
- Ensure tab modules exist in `client/tabs/`
- Check module paths in configuration
- Verify imports in dashboard code
