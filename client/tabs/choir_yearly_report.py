import streamlit as st
import pandas as pd
from client.tabs.choir_data import get_practice_dates, get_logs_for_date_range, get_manual_attendance_for_date

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
                
                # 1. Get Log Attendance (Card Scans)
                d_start = p_date.replace(hour=0, minute=0, second=0)
                d_end = p_date.replace(hour=23, minute=59, second=59)
                
                logs = get_logs_for_date_range(d_start, d_end)
                log_uids = set()
                if logs:
                    dfl = pd.DataFrame(logs)
                    c = "card_uid" if "card_uid" in dfl.columns else "student_uid"
                    if c in dfl.columns:
                        log_uids = set(dfl[c].unique())

                # 2. Get Manual Attendance
                manual_recs = get_manual_attendance_for_date(p_date.date())
                manual_person_ids = set()
                excused_person_ids = set()
                
                if manual_recs:
                    for r in manual_recs:
                        pid = r.get('person_id')
                        if pid:
                            if r.get('attended'):
                                manual_person_ids.add(pid)
                            if r.get('excuse'):
                                excused_person_ids.add(pid)
                
                attendance_map[p_date_str] = {
                    "card_uids": log_uids,
                    "manual_ids": manual_person_ids,
                    "excused_ids": excused_person_ids
                }

        matrix = []
        dates_list = sorted(attendance_map.keys())
        
        for _, person in choir_df.iterrows():
            uid = person.get("card_uid")
            # Resolve person_id just like in choir_attendance.py
            person_id = person.get('id_y') or person.get('id') or person.get('person_id')

            row_data = {
                "Name": f"{person.get('name', '')} {person.get('surname', '')}"
            }
            total_attended = 0
            excused_count = 0
            
            for d in dates_list:
                day_data = attendance_map[d]
                
                # Check status
                in_logs = uid in day_data["card_uids"]
                in_manual = person_id in day_data["manual_ids"]
                in_excused = person_id in day_data["excused_ids"]
                
                attended = in_logs or in_manual
                
                if attended:
                    row_data[d] = "✅"
                    total_attended += 1
                elif in_excused:
                    row_data[d] = "📝"
                    excused_count += 1
                else:
                    row_data[d] = "❌"
            
            row_data["Total"] = total_attended
            
            # Percentage ignores excused days
            net_practices = len(dates_list) - excused_count
            if net_practices > 0:
                 row_data["%"] = f"{(total_attended / net_practices * 100):.1f}%"
            else:
                 row_data["%"] = "N/A"
                
            matrix.append(row_data)
            
        st.dataframe(pd.DataFrame(matrix), use_container_width=True)
