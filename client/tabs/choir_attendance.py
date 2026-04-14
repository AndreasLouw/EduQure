import streamlit as st
import pandas as pd
import time
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


@st.fragment
def render_session_attendance(choir_df, selected_year):
    """Render session attendance subtab with local caching and batched updates"""
    st.subheader("Session Attendance")
    
    today = date.today()
    
    # Fetch all practice dates for the selected year
    practice_dates_df = get_practice_dates(selected_year)
    available_dates = [today] if today.year == selected_year else []
    
    if not practice_dates_df.empty:
        # Extract dates and add them to the list, ensuring no duplicates
        db_dates = [pd.to_datetime(d).date() for d in practice_dates_df['date'].tolist()]
        for d in db_dates:
            if d not in available_dates:
                available_dates.append(d)
                
    # Sort dates descending (newest first)
    available_dates.sort(reverse=True)
    
    # If viewing a past year and no dates exist, show a message
    if not available_dates:
        st.info(f"No practice dates recorded for {selected_year}.")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        # Let user select a date
        selected_date = st.selectbox(
            "Select Practice Session Date",
            options=available_dates,
            format_func=lambda d: d.strftime('%A, %d %B %Y') + (" (Today)" if d == today else "")
        )
    with col2:
        # Create session button only makes sense for the specifically selected date
        # Check if the selected date already exists in DB
        date_exists_in_db = False
        if not practice_dates_df.empty:
            date_exists_in_db = selected_date in [pd.to_datetime(d).date() for d in practice_dates_df['date'].tolist()]
            
        if not date_exists_in_db:
            if st.button("Create Session for Selected Date"):
                success, msg = create_practice_date(selected_date)
                if success:
                    st.success(msg)
                    time.sleep(1) # Give it a second before rerun
                    st.rerun()
                else:
                    st.info(msg)
        else:
            st.write("") # placeholder
            st.success("Session exists")
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
    # Clear session state if the date changed
    if "current_view_date" not in st.session_state or st.session_state.current_view_date != selected_date:
        st.session_state.current_view_date = selected_date
        st.session_state.attendance_df = None
        st.session_state.pending_attendance_changes = {}
        st.session_state.choir_session_exists = False
        if "attendance_editor" in st.session_state:
             del st.session_state.attendance_editor
             
    # Initialize session state variables
    if "attendance_df" not in st.session_state:
        st.session_state.attendance_df = None
    if "pending_attendance_changes" not in st.session_state:
        st.session_state.pending_attendance_changes = {}
    if "last_sync_time" not in st.session_state:
        st.session_state.last_sync_time = time.time()
    if "choir_session_exists" not in st.session_state:
        st.session_state.choir_session_exists = False
    
    # Refresh button
    if st.button('Refresh Session Data'):
        st.session_state.attendance_df = None
        st.session_state.pending_attendance_changes = {}
        st.session_state.choir_session_exists = False # Force check
        if "attendance_editor" in st.session_state:
             del st.session_state.attendance_editor
        st.rerun()

    # Function to sync pending changes to DB
    def sync_changes():
        pending = st.session_state.pending_attendance_changes
        if not pending:
            return
        
        count = 0
        for person_id, changes in pending.items():
            update_manual_attendance(
                person_id,
                target_date=selected_date,
                attended=changes.get('attended'), 
                excuse=changes.get('excuse')
            )
            count += 1
        
        st.session_state.pending_attendance_changes = {}
        st.session_state.last_sync_time = time.time()
        # st.toast(f"Synced {count} changes.") # Optional noise

    if st.session_state.attendance_df is None:
        # Check for session
        supabase = get_supabase()
        check_date_str = selected_date.strftime("%Y-%m-%d")
        session_check = supabase.table("choir_practice_dates").select("*").eq("date", check_date_str).execute()
        
        if session_check.data:
            st.session_state.choir_session_exists = True
            
            if not choir_df.empty:
                start_today = datetime.combine(selected_date, datetime.min.time())
                end_today = datetime.combine(selected_date, datetime.max.time())
                
                todays_logs = get_logs_for_date_range(start_today, end_today)
                df_todays_logs = pd.DataFrame(todays_logs)
                
                # Get manual attendance records
                manual_attendance = get_manual_attendance_for_date(selected_date)
                manual_attendance_dict = {}
                if manual_attendance:
                    for record in manual_attendance:
                        manual_attendance_dict[record['person_id']] = {
                            'attended': record.get('attended', False),
                            'excuse': record.get('excuse', False),
                            'updated_at': record.get('updated_at')
                        }

                # Normalize UID columns
                uid_col_persons = "card_uid"
                uid_col_logs = "card_uid" if not df_todays_logs.empty and "card_uid" in df_todays_logs.columns else "student_uid"
                
                present_uids = set()
                if not df_todays_logs.empty and uid_col_logs in df_todays_logs.columns:
                        present_uids = set(df_todays_logs[uid_col_logs].unique())
                
                table_data = []
                
                for index, row in choir_df.iterrows():
                    uid = row.get(uid_col_persons)
                    person_id = row.get('id_y') or row.get('id') or row.get('person_id')
                    
                    is_present_via_card = uid in present_uids
                    
                    manual_record = manual_attendance_dict.get(person_id, {})
                    is_manually_attended = manual_record.get('attended', False)
                    has_excuse = manual_record.get('excuse', False)
                    
                    is_present = is_present_via_card or is_manually_attended
                    
                    time_in = "-"
                    if is_present_via_card:
                        person_logs = df_todays_logs[df_todays_logs[uid_col_logs] == uid]
                        if not person_logs.empty:
                            if "created_at" in person_logs.columns:
                                first_log = pd.to_datetime(person_logs['created_at']).min()
                                first_log = first_log.tz_convert("Africa/Johannesburg") if first_log.tzinfo else first_log
                                time_in = first_log.strftime("%H:%M")
                    elif is_manually_attended:
                        manual_updated_at = manual_record.get('updated_at')
                        if manual_updated_at:
                            try:
                                updated_time = pd.to_datetime(manual_updated_at)
                                if updated_time.tzinfo:
                                    updated_time = updated_time.tz_convert("Africa/Johannesburg")
                                time_in = updated_time.strftime("%H:%M")
                            except:
                                time_in = "Manual"
                        else:
                            time_in = "Manual"
                    
                    grade_val = row.get('grade', '')
                    if grade_val and str(grade_val).replace('.','',1).isdigit():
                        grade_val = int(float(grade_val))

                    table_data.append({
                        "person_id": person_id,
                        "Name and Surname": f"{row.get('name', '')} {row.get('surname', '')}",
                        "Grade": grade_val,
                        "Present": "✅" if is_present else ("📝" if has_excuse else ""),
                        "Time In": time_in,
                        "Manual Attendance": bool(is_manually_attended),
                        "Excuse": bool(has_excuse),
                        "is_present_via_card": is_present_via_card # Hidden column for logic
                    })
                
                df_display = pd.DataFrame(table_data)
                if not df_display.empty:
                    df_display.set_index("person_id", inplace=True)
                
                st.session_state.attendance_df = df_display
        else:
             st.session_state.choir_session_exists = False
             st.session_state.attendance_df = pd.DataFrame() # Empty placeholder

    # Using Cached Session Existence State
    if st.session_state.choir_session_exists and st.session_state.attendance_df is not None and not st.session_state.attendance_df.empty:
        
        st.write("**Manual Attendance & Excuses**")
        st.caption("Select attendees below. Checking a box will automatically save and update.")
        
        # Ensure success message survives the Streamlit rerun
        update_success_msg = st.session_state.get("show_update_success")
        if update_success_msg:
            st.success(update_success_msg)
            
        df = st.session_state.attendance_df
        
        # Header
        col_widths = [3, 1, 1.5, 1.5, 1.5, 1.5]
        header_cols = st.columns(col_widths)
        header_cols[0].write("**Name and Surname**")
        header_cols[1].write("**Grade**")
        header_cols[2].write("**Present**")
        header_cols[3].write("**Time In**")
        header_cols[4].write("**Manual**")
        header_cols[5].write("**Excuse**")
        
        st.divider()
        
        # Pre-process state changes to enforce immediate mutual exclusivity
        updates_made = 0
        current_time_str = datetime.now().strftime("%H:%M")
        
        for person_id, row in df.iterrows():
            att_key = f"att_{person_id}"
            exc_key = f"exc_{person_id}"
            
            # Since checkboxes render with keys, Streamlit automatically updates session_state on click
            new_att = st.session_state.get(att_key, row["Manual Attendance"])
            new_exc = st.session_state.get(exc_key, row["Excuse"])
            
            if new_att != row["Manual Attendance"] or new_exc != row["Excuse"]:
                is_card_present = row.get("is_present_via_card", False)
                
                att_just_checked = new_att and not row["Manual Attendance"]
                exc_just_checked = new_exc and not row["Excuse"]
                
                if att_just_checked:
                    new_exc = False
                    st.session_state[exc_key] = False # Force Uncheck
                elif exc_just_checked:
                    new_att = False
                    st.session_state[att_key] = False # Force Uncheck
                    
                # Update DF
                df.at[person_id, "Manual Attendance"] = new_att
                df.at[person_id, "Excuse"] = new_exc
                
                if new_att:
                    df.at[person_id, "Present"] = "✅"
                    if not is_card_present:
                        df.at[person_id, "Time In"] = current_time_str
                elif new_exc:
                    if is_card_present:
                        df.at[person_id, "Present"] = "✅"
                    else:
                        df.at[person_id, "Present"] = "📝"
                        df.at[person_id, "Time In"] = "-"
                else:
                    if is_card_present:
                        df.at[person_id, "Present"] = "✅"
                    else:
                        df.at[person_id, "Present"] = ""
                        df.at[person_id, "Time In"] = "-"
                        
                # Update Database
                update_manual_attendance(person_id, target_date=selected_date, attended=new_att, excuse=new_exc)
                updates_made += 1
                
        if updates_made > 0:
            st.session_state.show_update_success = f"Updates successfully applied. {updates_made} records updated."
            st.rerun()
            
        # Render current state
        for person_id, row in df.iterrows():
            cols = st.columns(col_widths)
            cols[0].write(row["Name and Surname"])
            cols[1].write(str(row["Grade"]))
            cols[2].write(row["Present"])
            cols[3].write(row["Time In"])
            
            cols[4].checkbox("Attend", value=bool(row["Manual Attendance"]), key=f"att_{person_id}")
            cols[5].checkbox("Excuse", value=bool(row["Excuse"]), key=f"exc_{person_id}")
            
        st.divider()
        
        st.caption("Note: Toggling a checkbox saves automatically. You don't strictly need to click update.")
        if st.button("Update Attendance", type="primary"):
            if updates_made == 0:
                st.success("Updates successfully applied.")
                
        if update_success_msg:
            st.success(update_success_msg)
            # Clear it so it doesn't persist beyond this viewing
            st.session_state.show_update_success = None
        
        # Calculate and display totals from SESSION DF
        st.divider()
        
        df_calc = st.session_state.attendance_df
        total_members = len(df_calc)
        present_count = 0
        excuse_count = 0
        
        # Efficient calculation without iteration
        # Note: df_calc['Present'] contains strings, we can count
        present_count = len(df_calc[df_calc['Present'] == "✅"])
        excuse_count = len(df_calc[df_calc['Present'] == "📝"])  
        
        # Double check overlap? Logic ensures Present takes precedence over Excuse in display "Present" column,
        # but for stats, we might want to separate.
        # Logic in loop:
        # if is_present (card or manual): present
        # elif excuse: excuse
        # So "Present" column == "✅" covers all present. "Present" column == "📝" covers pure excuses.
        
        absent_count = total_members - present_count - excuse_count
        
        total_cols = st.columns(4)
        with total_cols[0]:
            st.metric("👥 Total Members", total_members)
        with total_cols[1]:
            st.metric("✅ Present", present_count)
        with total_cols[2]:
            st.metric("📝 Excused", excuse_count)
        with total_cols[3]:
            st.metric("❌ Absent", absent_count)

    else:
        st.info("No practice session created for this date.")



def render():
    """Main render function for Choir Attendance tab"""
    st.header("Choir Attendance Dashboard")
    
    current_year = datetime.now().year
    selected_year = st.number_input("Year", min_value=2020, max_value=2030, value=current_year, step=1)
    
    choir_df = get_choir_members(selected_year)
    
    if choir_df.empty:
        st.warning(f"No choir members found for {selected_year} or table structure mismatch.")
    else:            
        subtab_today, subtab_year = st.tabs(["📅 Session Attendance", "📊 Yearly Report"])
        
        with subtab_today:
            render_session_attendance(choir_df, selected_year)
        
        with subtab_year:
            render_yearly_report(choir_df, selected_year)
