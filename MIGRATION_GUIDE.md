# Database Migration Guide

## Current Status

The multi-tenant platform has been successfully refactored and all tests pass. The dashboard is running at `http://localhost:8501`, but it needs the new database tables to function properly.

---

## Step-by-Step Migration

### Option 1: Fresh Start (Recommended for Testing)

If you want to start fresh with the new multi-tenant structure:

#### 1. Open Supabase SQL Editor
- Go to your Supabase project dashboard
- Navigate to **SQL Editor**

#### 2. Execute Migration
- Copy the contents of `tenants/eduqure/migration_initial.sql`
- Paste into SQL Editor
- Click **Run**

#### 3. Verify Tables Created
Run this query to verify:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'eduqure_%'
ORDER BY table_name;
```

You should see:
- `eduqure_access_logs`
- `eduqure_choir_practice_dates`
- `eduqure_choir_register`
- `eduqure_manual_choir_attendance`
- `eduqure_persons`
- `eduqure_unidentified_cards`

#### 4. Test Dashboard
- Refresh `http://localhost:8501`
- Login with your credentials
- All tabs should now work with the new tables

---

### Option 2: Migrate Existing Data

If you have existing data you want to keep:

#### 1. Backup Existing Data
```sql
-- Backup persons
CREATE TABLE persons_backup AS SELECT * FROM persons;

-- Backup access_logs  
CREATE TABLE access_logs_backup AS SELECT * FROM access_logs;

-- Continue for all tables...
```

#### 2. Create New Tables
- Execute `tenants/eduqure/migration_initial.sql` as in Option 1

#### 3. Migrate Data
```sql
-- Migrate persons
INSERT INTO eduqure_persons (id, name, surname, card_uid, grade, is_choir, choir_year, created_at)
SELECT id, name, surname, card_uid, grade, is_choir, choir_year, created_at 
FROM persons;

-- Migrate access_logs
INSERT INTO eduqure_access_logs (id, card_uid, lock, status, created_at, person_id)
SELECT id, card_uid, lock, status, created_at, person_id
FROM access_logs;

-- Migrate unidentified_cards
INSERT INTO eduqure_unidentified_cards (id, card_uid, lock, created_at)
SELECT id, card_uid, lock, created_at
FROM unidentified_cards;

-- Migrate choir_practice_dates
INSERT INTO eduqure_choir_practice_dates (id, date, year, created_at)
SELECT id, date, year, created_at
FROM choir_practice_dates;

-- Migrate choir_register  
INSERT INTO eduqure_choir_register (id, personId, year, removed, created_at)
SELECT id, personId, year, removed, created_at
FROM choir_register;

-- Migrate manual_choir_attendance
INSERT INTO eduqure_manual_choir_attendance (id, person_id, practice_date_id, attended, excuse, created_at, updated_at)
SELECT id, person_id, practice_date_id, attended, excuse, created_at, updated_at
FROM manual_choir_attendance;
```

#### 4. Verify Migration
```sql
-- Check row counts match
SELECT 
    'persons' as table_name,
    (SELECT COUNT(*) FROM persons) as old_count,
    (SELECT COUNT(*) FROM eduqure_persons) as new_count
UNION ALL
SELECT 
    'access_logs',
    (SELECT COUNT(*) FROM access_logs),
    (SELECT COUNT(*) FROM eduqure_access_logs)
-- Continue for all tables...
;
```

#### 5. (Optional) Drop Old Tables
⚠️ **Only after verifying everything works!**
```sql
DROP TABLE persons;
DROP TABLE access_logs;
DROP TABLE unidentified_cards;
DROP TABLE choir_practice_dates;
DROP TABLE choir_register;
DROP TABLE manual_choir_attendance;
```

---

## Update ESP32 Firmware

After database migration, update the firmware to use new table names:

### File: `firmware/rfidCard_scanner/rfidCard_scanner.ino`

Find these lines and update table names:

```cpp
// OLD:
String endpoint = "/rest/v1/access_logs";

// NEW:
String endpoint = "/rest/v1/eduqure_access_logs";
```

```cpp
// OLD:
response = supabase.table("persons").select("card_uid").execute();

// NEW:
response = supabase.table("eduqure_persons").select("card_uid").execute();
```

Update all instances of:
- `access_logs` → `eduqure_access_logs`
- `persons` → `eduqure_persons`
- `unidentified_cards` → `eduqure_unidentified_cards`

---

## Verification Checklist

After migration, verify these features:

### Dashboard Tests
- [ ] Login works
- [ ] **Choir Attendance Tab**:
  - [ ] Today's attendance loads
  - [ ] Manual attendance checkboxes work
  - [ ] Excuse checkboxes work
  - [ ] Statistics display correctly
  - [ ] Yearly report generates
- [ ] **Live Monitor Tab**:
  - [ ] Unidentified cards display
  - [ ] Recent scans show
- [ ] **Access Logs Tab**:
  - [ ] Logs display with names
  - [ ] IN/OUT status calculates
  - [ ] Filtering works
- [ ] **Management Tab**:
  - [ ] Choir register management works
  - [ ] Practice dates CRUD works
  - [ ] Persons CRUD works

### Firmware Tests (after firmware update)
- [ ] RFID scan logs to `eduqure_access_logs`
- [ ] Card sync uses `eduqure_persons`
- [ ] Unknown cards log to `eduqure_unidentified_cards`
- [ ] Offline queue processes correctly

---

## Rollback Plan

If something goes wrong:

### Quick Rollback
```sql
-- Drop new tables
DROP TABLE IF EXISTS eduqure_persons CASCADE;
DROP TABLE IF EXISTS eduqure_access_logs CASCADE;
DROP TABLE IF EXISTS eduqure_unidentified_cards CASCADE;
DROP TABLE IF EXISTS eduqure_choir_practice_dates CASCADE;
DROP TABLE IF EXISTS eduqure_choir_register CASCADE;
DROP TABLE IF EXISTS eduqure_manual_choir_attendance CASCADE;

-- Restore from backup
CREATE TABLE persons AS SELECT * FROM persons_backup;
CREATE TABLE access_logs AS SELECT * FROM access_logs_backup;
-- etc.
```

### Code Rollback
```bash
# Revert to old dashboard (if needed)
git checkout HEAD~1 client/secured_dashboard.py
```

---

## Support

If you encounter issues:

1. **Check Supabase logs** for SQL errors
2. **Check Streamlit terminal** for Python errors
3. **Run tests**: `python test_platform.py`
4. **Verify table names**: 
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' AND table_name LIKE 'eduqure_%';
   ```

---

## Next Steps After Migration

1. ✅ Apply database migration
2. ✅ Test all dashboard features
3. ✅ Update firmware
4. ✅ Test RFID scanning
5. 🚀 Deploy to production
6. 🎯 Add GymTrack tenant
7. 🎯 Add FarmSense tenant

**Good luck with the migration!** 🚀
