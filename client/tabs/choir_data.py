import streamlit as st
import pandas as pd
from datetime import datetime, date
from client.utils.supabase_client import get_supabase

@st.cache_data(ttl=60)
def get_choir_members(year):
    """Fetch choir members for a specific year (cached 60s; use clear_choir_data_cache after writes)"""
    try:
        supabase = get_supabase()
        # Get choir register
        register_response = supabase.table("choir_register").select("*").eq("year", year).execute()
        register_data = register_response.data
        
        if not register_data:
            return pd.DataFrame()

        # Get all persons
        persons_response = supabase.table("persons").select("*").execute()
        persons_data = persons_response.data
        
        if not persons_data:
            return pd.DataFrame()

        df_register = pd.DataFrame(register_data)
        
        # Filter out removed members
        if "removed" in df_register.columns:
            df_register = df_register[df_register["removed"] != True]
            
        df_persons = pd.DataFrame(persons_data)
        
        # Merge to get names and card_uids
        pid_col = "person_id" if "person_id" in df_register.columns else "personId"
        
        if pid_col in df_register.columns and "id" in df_persons.columns:
            merged = df_register.merge(df_persons, left_on=pid_col, right_on="id", how="inner")
            return merged
        else:
            st.error(f"Column mismatch: Found {df_register.columns} in register and {df_persons.columns} in persons")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error fetching choir members: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_practice_dates(year):
    """Fetch practice dates for a specific year (cached 60s; use clear_choir_data_cache after writes)"""
    try:
        supabase = get_supabase()
        response = supabase.table("choir_practice_dates").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            date_col = "date" 
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                return df[df[date_col].dt.year == year].sort_values(date_col)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching practice dates: {e}")
        return pd.DataFrame()


def clear_choir_data_cache():
    """Invalidate cached choir fetches after any write"""
    get_choir_members.clear()
    get_practice_dates.clear()


def create_practice_date(practice_date):
    """Create a new practice date"""
    try:
        supabase = get_supabase()
        date_str = practice_date.strftime("%Y-%m-%d")
        # Check if exists
        existing = supabase.table("choir_practice_dates").select("*").eq("date", date_str).execute()
        if not existing.data:
            supabase.table("choir_practice_dates").insert({
                "date": date_str,
                "updated_at": datetime.now().isoformat()
            }).execute()
            clear_choir_data_cache()
            return True, "Practice date created."
        return False, "Date already exists."
    except Exception as e:
        return False, f"Error creating date: {e}"

def get_logs_for_date_range(start_date, end_date):
    """Fetch access logs for a date range"""
    try:
        supabase = get_supabase()
        response = supabase.table("access_logs").select("*") \
            .gte("created_at", start_date.isoformat()) \
            .lte("created_at", end_date.isoformat()) \
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching historical logs: {e}")
        return []

def get_logs_for_year(year):
    """Fetch all access logs in one query for a whole year (replaces per-date N+1).

    Selects "*" rather than a guessed column list: the uid column name has
    differed across schema versions (card_uid vs student_uid), and selecting a
    nonexistent column makes PostgREST fail the whole query (42703). The
    report only uses the uid column that is actually present.
    """
    try:
        supabase = get_supabase()
        start = datetime(year, 1, 1, 0, 0, 0)
        end = datetime(year, 12, 31, 23, 59, 59)
        response = supabase.table("access_logs").select("*") \
            .gte("created_at", start.isoformat()) \
            .lte("created_at", end.isoformat()) \
            .execute()
        return response.data or []
    except Exception as e:
        st.error(f"Error fetching yearly logs: {e}")
        return []

def get_manual_attendance_for_date(target_date):
    """Fetch manual attendance records for a specific date"""
    try:
        supabase = get_supabase()
        start_date = datetime.combine(target_date, datetime.min.time())
        end_date = datetime.combine(target_date, datetime.max.time())
        
        response = supabase.table("manual_choir_attendance").select("*") \
            .gte("created_at", start_date.isoformat()) \
            .lte("created_at", end_date.isoformat()) \
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching manual attendance: {e}")
        return []

@st.cache_data(ttl=60)
def get_manual_attendance_for_year(year):
    """Fetch all manual attendance records in one query for a whole year (replaces per-date N+1).

    Records are located by their created_at day (the app stamps created_at with
    the target practice date on insert), mirroring get_manual_attendance_for_date.
    """
    try:
        supabase = get_supabase()
        start = datetime(year, 1, 1, 0, 0, 0)
        end = datetime(year, 12, 31, 23, 59, 59)
        response = supabase.table("manual_choir_attendance").select("*") \
            .gte("created_at", start.isoformat()) \
            .lte("created_at", end.isoformat()) \
            .execute()
        records = response.data or []
        by_date = {}
        for r in records:
            created = r.get("created_at")
            if not created:
                continue
            # ISO8601 + utc: inserted rows carry an offset-less timestamp while
            # DB-default rows carry "+00:00" and fractional seconds
            day = pd.to_datetime(created, format="ISO8601", utc=True).date()
            by_date.setdefault(day, []).append(r)
        return by_date
    except Exception as e:
        st.error(f"Error fetching yearly manual attendance: {e}")
        return {}

def update_manual_attendance(person_id, target_date=None, attended=None, excuse=None):
    """Update or insert manual attendance record for a specific date (defaults to today)"""
    try:
        supabase = get_supabase()
        if target_date is None:
            target_date = date.today()
            
        start_date = datetime.combine(target_date, datetime.min.time())
        end_date = datetime.combine(target_date, datetime.max.time())
        
        # Check if record exists for today
        existing = supabase.table("manual_choir_attendance").select("*") \
            .eq("person_id", person_id) \
            .gte("created_at", start_date.isoformat()) \
            .lte("created_at", end_date.isoformat()) \
            .execute()
        
        data = {}
        if attended is not None:
            data["attended"] = attended
        if excuse is not None:
            data["excuse"] = excuse
        
        # Always set updated_at to current time
        data["updated_at"] = datetime.now().isoformat()
        
        if existing.data:
            # Update existing record
            record_id = existing.data[0]["id"]
            supabase.table("manual_choir_attendance").update(data).eq("id", record_id).execute()
        else:
            # Insert new record
            data["person_id"] = person_id
            # Set created_at to the target date so it shows up correctly in historical queries
            data["created_at"] = datetime.combine(target_date, datetime.now().time()).isoformat()
            supabase.table("manual_choir_attendance").insert(data).execute()
        
        get_manual_attendance_for_year.clear()
        return True
    except Exception as e:
        st.error(f"Error updating manual attendance: {e}")
        return False
