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
def render_todays_attendance(choir_df):
    """Render today's attendance subtab with local caching and batched updates"""
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
    if st.button('Refresh Today Data'):
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
                attended=changes.get('attended'), 
                excuse=changes.get('excuse')
            )
            count += 1
        
        st.session_state.pending_attendance_changes = {}
        st.session_state.last_sync_time = time.time()
        # st.toast(f"Synced {count} changes.") # Optional noise

    # Load data if not in session state (Cached DB Logic)
    if st.session_state.attendance_df is None:
        # Check for session
        supabase = get_supabase()
        check_date_str = today.strftime("%Y-%m-%d")
        session_check = supabase.table("choir_practice_dates").select("*").eq("date", check_date_str).execute()
        
        if session_check.data:
            st.session_state.choir_session_exists = True
            
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
        st.caption("Batch select attendees below. Click 'Update Attendance' to save changes and calculate totals.")
        
        with st.form("attendance_form"):
            edited_df = st.data_editor(
                st.session_state.attendance_df,
                column_config={
                    "Name and Surname": st.column_config.TextColumn("Name and Surname", disabled=True),
                    "Grade": st.column_config.NumberColumn("Grade", disabled=True, format="%d"),
                    "Present": st.column_config.TextColumn("Present", disabled=True),
                    "Time In": st.column_config.TextColumn("Time In", disabled=True),
                    "Manual Attendance": st.column_config.CheckboxColumn("Manual Attendance"),
                    "Excuse": st.column_config.CheckboxColumn("Excuse"),
                    "is_present_via_card": None, # Hide this column
                },
                use_container_width=True,
                key="attendance_editor",
                num_rows="fixed",
                hide_index=True
            )
            
            if st.form_submit_button("Update Attendance", type="primary"):
                # Process changes from the editor state
                # Note: st.data_editor inside form returns the *modified* dataframe (edited_df) upon submit
                # BUT edited_df doesn't apply our mutual exclusivity logic automatically during the edit,
                # so we might see both checked. We must resolve logic here.

                # We can iterate the session state "edited_rows" which persists?
                # Actually, capturing the diff is easier via session state "attendance_editor"
                
                state = st.session_state.get("attendance_editor")
                changes = state.get("edited_rows", {}) if state else {}
                
                # Check if we have changes
                if changes:
                    df = st.session_state.attendance_df
                    current_time_str = datetime.now().strftime("%H:%M")
                    updates_made = 0
                    
                    for idx, diff in changes.items():
                        try:
                            # Use internal index if sorted/filtered? 
                            # Usually direct index access is safest if index is person_id
                            person_id = df.index[int(idx)]
                        except (ValueError, IndexError):
                            continue
                            
                        attended = diff.get("Manual Attendance")
                        excuse = diff.get("Excuse")
                        
                        # Logic: Update Local DF & DB
                        is_card_present = df.at[person_id, "is_present_via_card"]
                        
                        db_attended = None
                        db_excuse = None

                        if attended is not None:
                            if attended:
                                df.at[person_id, "Manual Attendance"] = True
                                df.at[person_id, "Excuse"] = False # Mutual Exclusivity
                                df.at[person_id, "Present"] = "✅"
                                if not is_card_present:
                                    df.at[person_id, "Time In"] = current_time_str
                                db_attended = True
                                db_excuse = False
                            else:
                                df.at[person_id, "Manual Attendance"] = False
                                # Recalculate State
                                if is_card_present:
                                    df.at[person_id, "Present"] = "✅"
                                elif df.at[person_id, "Excuse"]: 
                                    df.at[person_id, "Present"] = "📝"
                                    df.at[person_id, "Time In"] = "-"
                                else:
                                    df.at[person_id, "Present"] = ""
                                    df.at[person_id, "Time In"] = "-"
                                db_attended = False
                                # We need to check if excuse should be preserved in DB call
                                # If excuse wasn't touched in this edit, it retains its value.
                                # But update_manual_attendance updates *args*.
                                # If we pass None, the function ignores it?
                                # Let's check update_manual_attendance.
                                # Yes, it has defaults=None.

                        if excuse is not None:
                            if excuse:
                                df.at[person_id, "Excuse"] = True
                                df.at[person_id, "Manual Attendance"] = False # Mutual Exclusivity
                                if is_card_present:
                                    df.at[person_id, "Present"] = "✅"
                                else:
                                    df.at[person_id, "Present"] = "📝"
                                    df.at[person_id, "Time In"] = "-"
                                db_excuse = True
                                db_attended = False
                            else:
                                df.at[person_id, "Excuse"] = False
                                if is_card_present:
                                     df.at[person_id, "Present"] = "✅"
                                elif df.at[person_id, "Manual Attendance"]:
                                     df.at[person_id, "Present"] = "✅"
                                else:
                                     df.at[person_id, "Present"] = ""
                                db_excuse = False

                        # Perform DB Update
                        if db_attended is not None or db_excuse is not None:
                            update_manual_attendance(person_id, attended=db_attended, excuse=db_excuse)
                            updates_made += 1

                    if updates_made > 0:
                        st.success(f"Updated {updates_made} records.")
                        # Clear edits ?
                        st.session_state["attendance_editor"]["edited_rows"] = {}
                        st.rerun() 
                else:
                    st.info("No changes to save.")
        
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
