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


def process_editor_edits(df, edited_rows, selected_date, current_time_str):
    """Apply st.data_editor cell edits to the attendance df and persist them.

    edited_rows maps positional row indices -> {column: new value}. Rows map
    back to persons via the df's person_id index. Mutual exclusivity is
    enforced here: marking a person attended clears their excuse and
    vice-versa. Returns the number of records saved.
    """
    updates_made = 0
    for row_idx, cell_edits in edited_rows.items():
        try:
            row_idx = int(row_idx)
        except (TypeError, ValueError):
            continue
        if row_idx < 0 or row_idx >= len(df):
            continue

        person_id = df.index[row_idx]
        row = df.iloc[row_idx]
        new_att = cell_edits.get("Manual Attendance", bool(row["Manual Attendance"]))
        new_exc = cell_edits.get("Excuse", bool(row["Excuse"]))
        new_att, new_exc = bool(new_att), bool(new_exc)

        # Mutual exclusivity: the field the user just flipped ON wins, matching
        # the old checkbox flow's "just checked" semantics. Checking which
        # field was edited (not which is True) is what lets excusing an
        # already-attended member clear the attendance.
        att_just_checked = new_att and not bool(row["Manual Attendance"])
        exc_just_checked = new_exc and not bool(row["Excuse"])
        if att_just_checked:
            new_exc = False
        elif exc_just_checked:
            new_att = False

        if new_att == bool(row["Manual Attendance"]) and new_exc == bool(row["Excuse"]):
            continue  # no-op edit

        is_card_present = bool(row.get("is_present_via_card", False))

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

        update_manual_attendance(person_id, target_date=selected_date,
                                 attended=new_att, excuse=new_exc)
        updates_made += 1
    return updates_made


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
        st.session_state.choir_session_exists = False
        st.session_state.show_update_success = None
        for key in list(st.session_state.keys()):
            if key.startswith("attendance_editor"):
                del st.session_state[key]
        # Drop stale checkbox values from the previously viewed date, otherwise
        # they leak across dates and one date's data overwrites another's
        for key in list(st.session_state.keys()):
            if key.startswith("att_") or key.startswith("exc_"):
                del st.session_state[key]
             
    # Initialize session state variables
    if "attendance_df" not in st.session_state:
        st.session_state.attendance_df = None
    if "choir_session_exists" not in st.session_state:
        st.session_state.choir_session_exists = False
    
    # Refresh button
    if st.button('Refresh Session Data'):
        st.session_state.attendance_df = None
        st.session_state.choir_session_exists = False # Force check
        # Drop checkbox and editor state so values re-initialize from the
        # fresh DB data instead of leaking from the previously rendered view
        for key in list(st.session_state.keys()):
            if key.startswith("att_") or key.startswith("exc_") or key.startswith("attendance_editor"):
                del st.session_state[key]
        st.rerun()

    # Widget keys are scoped to the selected date. Date-agnostic keys made any
    # missed state cleanup leak one date's checkbox values into another's UI
    # and DB writes; with a date prefix a stale key from another date is
    # simply never read.
    date_prefix = selected_date.strftime("%Y%m%d")

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
        st.caption("Tick attendees below — changes save automatically.")
        
        df = st.session_state.attendance_df
        
        # Editor state is date-scoped like every other per-date widget key
        editor_key = f"attendance_editor_{date_prefix}"
        
        # Apply and persist any edits made since the last rerun, then drain them
        # so they don't replay on subsequent reruns
        edited_rows = {}
        if editor_key in st.session_state:
            edited_rows = st.session_state[editor_key].get("edited_rows", {}) or {}
        
        current_time_str = datetime.now().strftime("%H:%M")
        if edited_rows:
            updates_made = process_editor_edits(df, edited_rows, selected_date, current_time_str)
            if updates_made > 0:
                st.session_state.show_update_success = f"Updates successfully applied. {updates_made} records updated."
        if editor_key in st.session_state:
            st.session_state[editor_key]["edited_rows"] = {}
        
        # Show the success message once, then clear it
        update_success_msg = st.session_state.get("show_update_success")
        if update_success_msg:
            st.success(update_success_msg)
            st.session_state.show_update_success = None
        
        # One editable table replaces the per-row checkbox grid: fewer widgets,
        # batched rendering, native sort. Identity/scan columns are read-only.
        editor_df = df.reset_index(drop=True)
        st.data_editor(
            editor_df[["Name and Surname", "Grade", "Present", "Time In", "Manual Attendance", "Excuse"]],
            key=editor_key,
            width='stretch',
            hide_index=True,
            column_config={
                "Name and Surname": st.column_config.Column("Name and Surname", disabled=True),
                "Grade": st.column_config.Column("Grade", disabled=True),
                "Present": st.column_config.Column("Present", disabled=True),
                "Time In": st.column_config.Column("Time In", disabled=True),
                "Manual Attendance": st.column_config.CheckboxColumn("Manual Attendance", default=False),
                "Excuse": st.column_config.CheckboxColumn("Excuse", default=False),
            },
        )
        
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
        # Radio instead of st.tabs: tab switching is purely client-side (no
        # rerun), so the yearly report kept showing data from whenever its
        # body last rendered. With a radio, switching reruns the fragment and
        # only the selected view's body executes -- the report always
        # reflects the latest DB state, and the hidden view costs nothing.
        view = st.radio(
            "View",
            ["📅 Session Attendance", "📊 Yearly Report"],
            horizontal=True,
            key="attendance_view_mode",
        )
        
        if view == "📅 Session Attendance":
            render_session_attendance(choir_df, selected_year)
        else:
            render_yearly_report(choir_df, selected_year)
