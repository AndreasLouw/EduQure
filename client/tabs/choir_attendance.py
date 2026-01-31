import streamlit as st
import pandas as pd
from datetime import datetime, date
from client.utils.supabase_client import get_supabase

def get_choir_members(year):
    """Fetch choir members for a specific year"""
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

def get_practice_dates(year):
    """Fetch practice dates for a specific year"""
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

def create_practice_date(practice_date):
    """Create a new practice date"""
    try:
        supabase = get_supabase()
        date_str = practice_date.strftime("%Y-%m-%d")
        # Check if exists
        existing = supabase.table("choir_practice_dates").select("*").eq("date", date_str).execute()
        if not existing.data:
            supabase.table("choir_practice_dates").insert({"date": date_str}).execute()
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

def update_manual_attendance(person_id, attended=None, excuse=None):
    """Update or insert manual attendance record for today"""
    try:
        supabase = get_supabase()
        today = date.today()
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        
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
        
        if existing.data:
            # Update existing record
            record_id = existing.data[0]["id"]
            supabase.table("manual_choir_attendance").update(data).eq("id", record_id).execute()
        else:
            # Insert new record
            data["person_id"] = person_id
            supabase.table("manual_choir_attendance").insert(data).execute()
        
        return True
    except Exception as e:
        st.error(f"Error updating manual attendance: {e}")
        return False

def render_todays_attendance(choir_df):
    """Render today's attendance subtab"""
    st.subheader("Today's Attendance")
    
    today = date.today()
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"Date: **{today.strftime('%A, %d %B %Y')}**")
    with col2:
        if st.button("Create New Attendance Session"):
            success, msg = create_practice_date(today)
            if success:
                st.success(msg)
            else:
                st.info(msg)
    
    if st.button('Refresh Today Data'):
        st.rerun()
    
    # Check for today's session
    supabase = get_supabase()
    check_date_str = today.strftime("%Y-%m-%d")
    session_check = supabase.table("choir_practice_dates").select("*").eq("date", check_date_str).execute()
    
    if session_check.data:
        if not choir_df.empty:
            start_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            end_today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
            
            todays_logs = get_logs_for_date_range(start_today, end_today)
            df_todays_logs = pd.DataFrame(todays_logs)
            
            # Get manual attendance records
            manual_attendance = get_manual_attendance_for_date(today)
            manual_attendance_dict = {}
            if manual_attendance:
                for record in manual_attendance:
                    manual_attendance_dict[record['person_id']] = {
                        'attended': record.get('attended', False),
                        'excuse': record.get('excuse', False)
                    }
            
            attendance_status = []
            
            # Normalize UID columns
            uid_col_persons = "card_uid"
            uid_col_logs = "card_uid" if not df_todays_logs.empty and "card_uid" in df_todays_logs.columns else "student_uid"
            
            present_uids = set()
            if not df_todays_logs.empty and uid_col_logs in df_todays_logs.columns:
                 present_uids = set(df_todays_logs[uid_col_logs].unique())
            
            for index, row in choir_df.iterrows():
                uid = row.get(uid_col_persons)
                is_present = uid in present_uids
                
                # Find time in
                time_in = "-"
                if is_present:
                    # Find first log
                    person_logs = df_todays_logs[df_todays_logs[uid_col_logs] == uid]
                    if not person_logs.empty:
                        if "created_at" in person_logs.columns:
                            first_log = pd.to_datetime(person_logs['created_at']).min()
                            first_log = first_log.tz_convert("Africa/Johannesburg") if first_log.tzinfo else first_log
                            time_in = first_log.strftime("%H:%M")

                attendance_status.append({
                    "Name and Surname": f"{row.get('name', '')} {row.get('surname', '')}",
                    "Grade": row.get('grade', ''),
                    "Present": "✅" if is_present else "",
                    "Time In": time_in,
                    "person_id": row.get('id'),  # Store person_id for checkbox callbacks
                })
            
            df_attendance = pd.DataFrame(attendance_status)
            
            # Display the table with interactive checkboxes
            st.write("**Manual Attendance & Excuses**")
            st.caption("Check 'Manual Attendance' if someone attended but forgot their tag. Check 'Excuse' if they provided an excuse for absence.")
            
            # Create columns for the table
            cols = st.columns([0.5, 3, 1, 1.5, 1.5, 1.5, 1.5])
            
            with cols[0]:
                st.write("**#**")
            with cols[1]:
                st.write("**Name and Surname**")
            with cols[2]:
                st.write("**Grade**")
            with cols[3]:
                st.write("**Present**")
            with cols[4]:
                st.write("**Time In**")
            with cols[5]:
                st.write("**Manual Attendance**")
            with cols[6]:
                st.write("**Excuse**")
            
            # Display each row with checkboxes
            for idx, row in df_attendance.iterrows():
                person_id = row['person_id']
                manual_record = manual_attendance_dict.get(person_id, {'attended': False, 'excuse': False})
                
                cols = st.columns([0.5, 3, 1, 1.5, 1.5, 1.5, 1.5])
                
                with cols[0]:
                    st.write(f"{idx + 1}")
                with cols[1]:
                    st.write(row['Name and Surname'])
                with cols[2]:
                    st.write(row['Grade'])
                with cols[3]:
                    st.write(row['Present'])
                with cols[4]:
                    st.write(row['Time In'])
                with cols[5]:
                    # Manual attendance checkbox
                    checkbox_key = f"manual_attended_{person_id}_{idx}"
                    
                    # Initialize session state if not exists
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = manual_record['attended']
                    
                    manual_attended = st.checkbox(
                        "Attended",
                        value=st.session_state[checkbox_key],
                        key=checkbox_key,
                        label_visibility="collapsed"
                    )
                    
                    # Only update if value actually changed
                    if manual_attended != manual_record['attended']:
                        if update_manual_attendance(person_id, attended=manual_attended):
                            st.session_state[checkbox_key] = manual_attended
                            
                with cols[6]:
                    # Excuse checkbox
                    checkbox_key = f"excuse_{person_id}_{idx}"
                    
                    # Initialize session state if not exists
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = manual_record['excuse']
                    
                    has_excuse = st.checkbox(
                        "Excuse",
                        value=st.session_state[checkbox_key],
                        key=checkbox_key,
                        label_visibility="collapsed"
                    )
                    
                    # Only update if value actually changed
                    if has_excuse != manual_record['excuse']:
                        if update_manual_attendance(person_id, excuse=has_excuse):
                            st.session_state[checkbox_key] = has_excuse
    else:
        st.info("No practice session created for today.")

def render_yearly_report(choir_df, selected_year):
    """Render yearly attendance report subtab"""
    st.subheader(f"Attendance Report {selected_year}")
    
    practice_dates_df = get_practice_dates(selected_year)
    
    if practice_dates_df.empty:
        st.info("No practice dates recorded yet for this year.")
    else:
        attendance_map = {} 
        
        with st.spinner("Compiling yearly report..."):
            for _, date_row in practice_dates_df.iterrows():
                p_date = date_row['date']
                p_date_str = p_date.strftime("%Y-%m-%d")
                
                d_start = p_date.replace(hour=0, minute=0, second=0)
                d_end = p_date.replace(hour=23, minute=59, second=59)
                
                logs = get_logs_for_date_range(d_start, d_end)
                log_uids = set()
                if logs:
                    dfl = pd.DataFrame(logs)
                    c = "card_uid" if "card_uid" in dfl.columns else "student_uid"
                    if c in dfl.columns:
                        log_uids = set(dfl[c].unique())
                
                attendance_map[p_date_str] = log_uids

        matrix = []
        dates_list = sorted(attendance_map.keys())
        
        for _, person in choir_df.iterrows():
            uid = person.get("card_uid")
            row_data = {
                "Name": f"{person.get('name', '')} {person.get('surname', '')}"
            }
            total_attended = 0
            
            for d in dates_list:
                attended = uid in attendance_map[d]
                row_data[d] = "✅" if attended else "❌"
                if attended: total_attended += 1
            
            row_data["Total"] = total_attended
            try:
                row_data["%"] = f"{(total_attended / len(dates_list) * 100):.1f}%"
            except:
                row_data["%"] = "0%"
                
            matrix.append(row_data)
            
        st.dataframe(pd.DataFrame(matrix), use_container_width=True)

def render():
    """Main render function for Choir Attendance tab"""
    st.header("Choir Attendance Dashboard")
    
    current_year = datetime.now().year
    selected_year = st.number_input("Year", min_value=2020, max_value=2030, value=current_year, step=1)
    
    choir_df = get_choir_members(selected_year)
    
    if choir_df.empty:
        st.warning(f"No choir members found for {selected_year} or table structure mismatch.")
    else:            
        subtab_today, subtab_year = st.tabs(["📅 Today's Session", "📊 Yearly Report"])
        
        with subtab_today:
            render_todays_attendance(choir_df)
        
        with subtab_year:
            render_yearly_report(choir_df, selected_year)
