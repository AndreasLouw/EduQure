-- Migration script for tenant: EduQure - School Attendance
-- Tenant ID: eduqure
-- Generated: database_manager.py

-- Create Tables

-- Table: persons
CREATE TABLE eduqure_persons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  surname TEXT NOT NULL,
  card_uid TEXT UNIQUE,
  grade INTEGER,
  is_choir BOOLEAN DEFAULT false,
  choir_year INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: access_logs
CREATE TABLE eduqure_access_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_uid TEXT NOT NULL,
  lock TEXT,
  status BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  person_id UUID,
  FOREIGN KEY (person_id) REFERENCES eduqure_persons(id)
);

-- Table: unidentified_cards
CREATE TABLE eduqure_unidentified_cards (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_uid TEXT NOT NULL,
  lock TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: choir_practice_dates
CREATE TABLE eduqure_choir_practice_dates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL UNIQUE,
  year INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: choir_register
CREATE TABLE eduqure_choir_register (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  personId UUID NOT NULL,
  year INTEGER NOT NULL,
  removed BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  FOREIGN KEY (personId) REFERENCES eduqure_persons(id)
);

-- Table: manual_choir_attendance
CREATE TABLE eduqure_manual_choir_attendance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  person_id UUID,
  practice_date_id UUID,
  attended BOOLEAN DEFAULT false,
  excuse BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  FOREIGN KEY (person_id) REFERENCES eduqure_persons(id),
  FOREIGN KEY (practice_date_id) REFERENCES eduqure_choir_practice_dates(id),
  UNIQUE(person_id, practice_date_id)
);

-- Enable Row Level Security

ALTER TABLE eduqure_persons ENABLE ROW LEVEL SECURITY;
ALTER TABLE eduqure_access_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE eduqure_unidentified_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE eduqure_choir_practice_dates ENABLE ROW LEVEL SECURITY;
ALTER TABLE eduqure_choir_register ENABLE ROW LEVEL SECURITY;
ALTER TABLE eduqure_manual_choir_attendance ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies


CREATE POLICY "allow_all_authenticated" ON eduqure_persons
  FOR ALL
  USING (auth.role() = 'authenticated');


CREATE POLICY "allow_all_authenticated" ON eduqure_access_logs
  FOR ALL
  USING (auth.role() = 'authenticated');


CREATE POLICY "allow_all_authenticated" ON eduqure_unidentified_cards
  FOR ALL
  USING (auth.role() = 'authenticated');


CREATE POLICY "allow_all_authenticated" ON eduqure_choir_practice_dates
  FOR ALL
  USING (auth.role() = 'authenticated');


CREATE POLICY "allow_all_authenticated" ON eduqure_choir_register
  FOR ALL
  USING (auth.role() = 'authenticated');


CREATE POLICY "allow_all_authenticated" ON eduqure_manual_choir_attendance
  FOR ALL
  USING (auth.role() = 'authenticated');
