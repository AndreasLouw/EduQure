import streamlit as st
import pandas as pd
from datetime import datetime, date
from client.utils.supabase_client import get_supabase

from client.tabs.choir_data import (
    get_choir_members,
    get_practice_dates,
    create_practice_date,
    get_logs_for_date_range,
    get_manual_attendance_for_date,
    update_manual_attendance
)
from client.tabs.choir_yearly_report import render_yearly_report

@st.fragment
def render_attendance_row(idx, row, person_id, manual_attendance_dict, is_present_via_card):
    """Render a single attendance row with checkboxes (fragment to prevent full reload)"""
    manual_record = manual_attendance_dict.get(person_id, {'attended': False, 'excuse': False})
    
    cols = st.columns([0.5, 3, 1, 1.5, 1.5, 1.5, 1.5])
    
    # Define keys first so we can use them for dynamic display
    attended_key = f"manual_attended_{person_id}_{idx}"
    excuse_key = f"excuse_{person_id}_{idx}"
    
    # Keys to track last saved state (to detect actual changes)
    attended_last_saved_key = f"_last_saved_{attended_key}"
    excuse_last_saved_key = f"_last_saved_{excuse_key}"
    
    # Initialize session state from database if not already set
    if attended_key not in st.session_state:
        st.session_state[attended_key] = manual_record['attended']
        st.session_state[attended_last_saved_key] = manual_record['attended']
    if excuse_key not in st.session_state:
        st.session_state[excuse_key] = manual_record['excuse']
        st.session_state[excuse_last_saved_key] = manual_record['excuse']
    
    # Check current manual attendance state from session
    is_manually_attended = st.session_state.get(attended_key, False)
    
    # Person is present if they scanned their card OR are manually marked as attended
    is_present = is_present_via_card or is_manually_attended
    
    # Determine time in based on current state
    time_in = row['Time In']  # Default from database (card scan time)
    if not is_present_via_card and is_manually_attended:
        # First check if we have a timestamp in session state (most recent)
        timestamp_key = f"_timestamp_{attended_key}"
        session_timestamp = st.session_state.get(timestamp_key)
        
        if session_timestamp:
            # Use timestamp from session state (just set by checkbox)
            try:
                updated_time = pd.to_datetime(session_timestamp)
                if updated_time.tzinfo:
                    updated_time = updated_time.tz_convert("Africa/Johannesburg")
                time_in = updated_time.strftime("%H:%M")
            except:
                time_in = "Manual"
        else:
            # Fall back to updated_at from manual attendance record
            manual_updated_at = manual_record.get('updated_at')
            if manual_updated_at:
                try:
                    # Parse and format the timestamp
                    updated_time = pd.to_datetime(manual_updated_at)
                    if updated_time.tzinfo:
                        updated_time = updated_time.tz_convert("Africa/Johannesburg")
                    time_in = updated_time.strftime("%H:%M")
                except:
                    time_in = "Manual"
            else:
                time_in = "Manual"
    elif not is_present:
        time_in = "-"
    
    with cols[0]:
        st.write(f"{idx + 1}")
    with cols[1]:
        st.write(row['Name and Surname'])
    with cols[2]:
        st.write(row['Grade'])
    with cols[3]:
        # Dynamic present display based on current state
        st.write("✅" if is_present else "")
    with cols[4]:
        # Dynamic time in display based on current state
        st.write(time_in)
    with cols[5]:
        # Manual attendance checkbox
        attended_key = f"manual_attended_{person_id}_{idx}"
        excuse_key = f"excuse_{person_id}_{idx}"
        
        # Keys to track last saved state (to detect actual changes)
        attended_last_saved_key = f"_last_saved_{attended_key}"
        excuse_last_saved_key = f"_last_saved_{excuse_key}"
        
        # Initialize session state from database if not already set
        if attended_key not in st.session_state:
            st.session_state[attended_key] = manual_record['attended']
            st.session_state[attended_last_saved_key] = manual_record['attended']
        if excuse_key not in st.session_state:
            st.session_state[excuse_key] = manual_record['excuse']
            st.session_state[excuse_last_saved_key] = manual_record['excuse']
        
        # Use factory function to properly capture variables
        def make_attendance_callback(pid, key, excuse_key, attended_last_saved_key, excuse_last_saved_key):
            def callback():
                new_value = st.session_state[key]
                last_saved = st.session_state.get(attended_last_saved_key, not new_value)  # Default to opposite to ensure update
                
                # Only update if value actually changed from last saved state
                if new_value != last_saved:
                    # Store current timestamp in session state
                    timestamp_key = f"_timestamp_{key}"
                    current_time = datetime.now()
                    st.session_state[timestamp_key] = current_time.isoformat()
                    
                    # If attended is checked, uncheck excuse (mutually exclusive)
                    if new_value:
                        st.session_state[excuse_key] = False  # Update UI immediately
                        update_manual_attendance(pid, attended=new_value, excuse=False)
                        st.session_state[excuse_last_saved_key] = False  # Track saved state
                    else:
                        update_manual_attendance(pid, attended=new_value)
                    
                    # Track the new saved state
                    st.session_state[attended_last_saved_key] = new_value
                    
                    # Increment totals version to trigger refresh
                    st.session_state['_totals_version'] = st.session_state.get('_totals_version', 0) + 1
            return callback
        
        st.checkbox(
            "Attended",
            key=attended_key,
            label_visibility="collapsed",
            on_change=make_attendance_callback(person_id, attended_key, excuse_key, attended_last_saved_key, excuse_last_saved_key)
        )
                
    with cols[6]:
        # Excuse checkbox (keys already defined above)
        
        # Use factory function to properly capture variables
        def make_excuse_callback(pid, key, attended_key, excuse_last_saved_key, attended_last_saved_key):
            def callback():
                new_value = st.session_state[key]
                last_saved = st.session_state.get(excuse_last_saved_key, not new_value)  # Default to opposite to ensure update
                
                # Only update if value actually changed from last saved state
                if new_value != last_saved:
                    # If excuse is checked, uncheck attended (mutually exclusive)
                    if new_value:
                        st.session_state[attended_key] = False  # Update UI immediately
                        update_manual_attendance(pid, excuse=new_value, attended=False)
                        st.session_state[attended_last_saved_key] = False  # Track saved state
                    else:
                        update_manual_attendance(pid, excuse=new_value)
                    
                    # Track the new saved state
                    st.session_state[excuse_last_saved_key] = new_value
                    
                    # Increment totals version to trigger refresh
                    st.session_state['_totals_version'] = st.session_state.get('_totals_version', 0) + 1
            return callback
        
        st.checkbox(
            "Excuse",
            key=excuse_key,
            label_visibility="collapsed",
            on_change=make_excuse_callback(person_id, excuse_key, attended_key, excuse_last_saved_key, attended_last_saved_key)
        )

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
                        'excuse': record.get('excuse', False),
                        'updated_at': record.get('updated_at')  # Store timestamp
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
                
                # Get person_id - after merge, id_y is from persons table which is what we need
                # id_x would be from choir_register if it has an id column
                person_id = row.get('id_y') or row.get('id') or row.get('person_id')
                
                # Check if present via card scan
                is_present_via_card = uid in present_uids
                
                # Check if manually marked as attended
                is_manually_attended = False
                if person_id and person_id in manual_attendance_dict:
                    is_manually_attended = manual_attendance_dict[person_id].get('attended', False)
                
                # Person is present if they scanned their card OR were manually marked as attended
                is_present = is_present_via_card or is_manually_attended
                
                # Find time in
                time_in = "-"
                if is_present_via_card:
                    # Find first log
                    person_logs = df_todays_logs[df_todays_logs[uid_col_logs] == uid]
                    if not person_logs.empty:
                        if "created_at" in person_logs.columns:
                            first_log = pd.to_datetime(person_logs['created_at']).min()
                            first_log = first_log.tz_convert("Africa/Johannesburg") if first_log.tzinfo else first_log
                            time_in = first_log.strftime("%H:%M")
                elif is_manually_attended:
                    # If manually attended but no card scan, show "Manual"
                    time_in = "Manual"
                
                attendance_status.append({
                    "Name and Surname": f"{row.get('name', '')} {row.get('surname', '')}",
                    "Grade": int(float(row.get('grade'))) if row.get('grade') and str(row.get('grade')).replace('.','',1).isdigit() else row.get('grade', ''),
                    "Present": "✅" if is_present else "",
                    "Time In": time_in,
                    "person_id": person_id,  # Store person_id for checkbox callbacks
                    "is_present_via_card": is_present_via_card,  # Store for dynamic rendering
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
                
                # Skip if person_id is None or invalid
                if person_id is None:
                    st.warning(f"⚠️ Missing person ID for {row['Name and Surname']} - cannot track manual attendance")
                    continue
                
                render_attendance_row(idx, row, person_id, manual_attendance_dict, row['is_present_via_card'])
            
            # Calculate and display totals dynamically using a fragment
            # The fragment runs every 0.5s to pick up session state changes from checkbox interactions
            @st.fragment(run_every=0.5)
            def render_attendance_totals(attendance_df):
                """Render attendance totals that update dynamically based on session state"""
                st.divider()
                
                total_members = len(attendance_df)
                present_count = 0
                excuse_count = 0
                
                for idx, row in attendance_df.iterrows():
                    person_id = row['person_id']
                    if person_id is None:
                        continue
                    
                    # Check if present via card scan
                    is_present_via_card = row['is_present_via_card']
                    
                    # Check session state for current checkbox values (dynamic)
                    attended_key = f"manual_attended_{person_id}_{idx}"
                    excuse_key = f"excuse_{person_id}_{idx}"
                    
                    is_manually_attended = st.session_state.get(attended_key, False)
                    has_excuse = st.session_state.get(excuse_key, False)
                    
                    if is_present_via_card or is_manually_attended:
                        present_count += 1
                    elif has_excuse:
                        excuse_count += 1
                
                absent_count = total_members - present_count - excuse_count
                
                # Display totals in a nice format
                total_cols = st.columns(4)
                with total_cols[0]:
                    st.metric("👥 Total Members", total_members)
                with total_cols[1]:
                    st.metric("✅ Present", present_count)
                with total_cols[2]:
                    st.metric("📝 Excused", excuse_count)
                with total_cols[3]:
                    st.metric("❌ Absent", absent_count)
            
            render_attendance_totals(df_attendance)
    else:
        st.info("No practice session created for today.")



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
