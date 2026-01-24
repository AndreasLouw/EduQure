import streamlit as st
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, date
import time

# Load environment variables
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    st.error("Supabase URL and Key not found. Please check your .env file.")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(url, key)

supabase = init_supabase()

st.title("🏫 School Attendance Live Feed")

# --- Authentication Logic ---

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Log In"):
        try:
            # Supabase Auth
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.success("Logged in successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.authenticated = False
    st.session_state.pop("user", None)
    st.rerun()

# --- Main App Logic (Wrapped) ---

if not st.session_state.authenticated:
    login()
else:
    # Sidebar for logout
    with st.sidebar:
        st.write(f"Logged in as: {st.session_state.user.email}")
        if st.button("Log Out"):
            logout()

    # --- Existing Helper Functions ---
    
    def get_unidentified_logs():
        try:
            response = supabase.table("unidentified_cards").select("*").order("created_at", desc=True).limit(50).execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching unidentified logs: {e}")
            return []

    def get_access_logs():
        try:
            # Increased limit to better capture daily flows for In/Out logic
            response = supabase.table("access_logs").select("*").order("created_at", desc=True).limit(200).execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching access logs: {e}")
            return []

    def get_persons():
        try:
            response = supabase.table("persons").select("card_uid, name, surname").execute()
            return response.data
        except Exception as e:
            return []

    def get_choir_members(year):
        try:
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
        try:
            response = supabase.table("choir_practice_dates").select("*").execute()
            if response.data:
                df = pd.DataFrame(response.data)
                # Ensure date column exists
                date_col = "date" 
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col])
                    return df[df[date_col].dt.year == year].sort_values(date_col)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error fetching practice dates: {e}")
            return pd.DataFrame()

    def create_practice_date(practice_date):
        try:
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
        try:
            # Fetch logs within range
            response = supabase.table("access_logs").select("*") \
                .gte("created_at", start_date.isoformat()) \
                .lte("created_at", end_date.isoformat()) \
                .execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching historical logs: {e}")
            return []

    if st.button('Refresh Data'):
        st.rerun()

    # Layout
    tab1, tab2, tab3 = st.tabs(["🔒 Access Logs", "⚠️ Live Monitor", "🎵 Choir Attendance"])

    with tab3:
        st.header("Choir Attendance Dashboard")
        
        current_year = datetime.now().year
        selected_year = st.number_input("Year", min_value=2020, max_value=2030, value=current_year, step=1)
        
        choir_df = get_choir_members(selected_year)
        
        if choir_df.empty:
            st.warning(f"No choir members found for {selected_year} or table structure mismatch.")
        else:            
            subtab_today, subtab_year = st.tabs(["📅 Today's Session", "📊 Yearly Report"])
            
            with subtab_today:
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
                
                # Fetch specifically for today
                try:
                    start_of_day = datetime(today.year, today.month, today.day)
                    pass
                except:
                    pass
                
                if not choir_df.empty:
                    start_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    end_today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
                    
                    todays_logs = get_logs_for_date_range(start_today, end_today)
                    df_todays_logs = pd.DataFrame(todays_logs)
                    
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
                                    # Convert to loc time (approx +2 for SA)
                                    first_log = first_log.tz_convert("Africa/Johannesburg") if first_log.tzinfo else first_log
                                    time_in = first_log.strftime("%H:%M")

                        attendance_status.append({
                            "Name and Surname": f"{row.get('name', '')} {row.get('surname', '')}",
                            "Present": "✅" if is_present else "", # "❌"
                            "Time In": time_in,
                            "Card UID": uid
                        })
                    
                    st.dataframe(pd.DataFrame(attendance_status), use_container_width=True)

            with subtab_year:
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

    with tab2:
        st.markdown("### Unidentified Card Scans")
        data = get_unidentified_logs()

        if data:
            df = pd.DataFrame(data)
            
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"])
                if df["created_at"].dt.tz is None:
                     df["created_at"] = df["created_at"].dt.tz_localize("UTC")
                df["created_at"] = df["created_at"].dt.tz_convert("Africa/Johannesburg")
            
            display_cols = ["id", "card_uid", "lock", "created_at"]
            display_cols = [c for c in display_cols if c in df.columns]
            
            st.dataframe(df[display_cols], use_container_width=True)
            st.metric("Recent Unidentified Scans", len(df))
        else:
            st.info("No unidentified logs found.")

    with tab1:
        st.markdown("### Access History")
        logs_data = get_access_logs()
        
        if logs_data:
            df_logs = pd.DataFrame(logs_data)
            
            uid_col = "card_uid" if "card_uid" in df_logs.columns else "student_uid"
            
            persons_data = get_persons()
            if persons_data:
                df_persons = pd.DataFrame(persons_data)
                if uid_col in df_logs.columns and "card_uid" in df_persons.columns:
                    df_logs = df_logs.merge(df_persons, left_on=uid_col, right_on="card_uid", how="left")
            
            if "created_at" in df_logs.columns:
                df_logs["created_at"] = pd.to_datetime(df_logs["created_at"])
                if df_logs["created_at"].dt.tz is None:
                     df_logs["created_at"] = df_logs["created_at"].dt.tz_localize("UTC")
                df_logs["created_at"] = df_logs["created_at"].dt.tz_convert("Africa/Johannesburg")

            # --- Logic for In/Out Calculation ---
            df_logs = df_logs.sort_values("created_at")
            
            df_logs['direction'] = "" 
            
            if 'status' in df_logs.columns:
                mask_success = df_logs['status'] == True
                df_logs.loc[mask_success, 'temp_date'] = df_logs.loc[mask_success, 'created_at'].dt.date
                df_logs.loc[mask_success, 'seq'] = df_logs[mask_success].groupby([uid_col, 'temp_date']).cumcount()
                
                def get_direction(seq):
                    if pd.isna(seq): return ""
                    return "IN" if seq % 2 == 0 else "OUT"
                
                df_logs.loc[mask_success, 'direction'] = df_logs.loc[mask_success, 'seq'].apply(get_direction)
                df_logs.drop(columns=['temp_date', 'seq'], errors='ignore', inplace=True)

            df_logs = df_logs.sort_values("created_at", ascending=False)

            def color_status(val):
                color = "#d4edda" if val else "#f8d7da" 
                return f'background-color: {color}; color: black'

            desired_cols = ["created_at", "direction", "name", "surname", uid_col, "status", "lock"]
            final_cols = [c for c in desired_cols if c in df_logs.columns]
            
            column_config = {
                "name": "Name",
                "surname": "Surname",
                "created_at": "Time",
                uid_col: "Card UID",            
                "status": "Success",
                "direction": "In/Out",
                "lock": "Gate"
            }
            
            st.dataframe(
                df_logs[final_cols].style.applymap(color_status, subset=['status'] if 'status' in df_logs.columns else None),
                column_config=column_config,
                use_container_width=True
            )
            
        else:
            st.info("No access logs found.")
