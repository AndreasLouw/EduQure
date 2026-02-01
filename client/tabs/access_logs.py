import streamlit as st
import pandas as pd
from client.utils.supabase_client import get_supabase

def get_access_logs():
    """Fetch recent access logs"""
    try:
        supabase = get_supabase()
        # Increased limit to better capture daily flows for In/Out logic
        response = supabase.table("access_logs").select("*").order("created_at", desc=True).limit(200).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching access logs: {e}")
        return []

def get_persons():
    """Fetch all persons with their card UIDs"""
    try:
        supabase = get_supabase()
        response = supabase.table("persons").select("card_uid, name, surname").execute()
        return response.data
    except Exception as e:
        return []

def color_status(val):
    """Color code status values"""
    color = "#d4edda" if val else "#f8d7da" 
    return f'background-color: {color}; color: black'

def render():
    """Main render function for Access Logs tab"""
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
            df_logs[final_cols].style.map(color_status, subset=['status'] if 'status' in df_logs.columns else None),
            column_config=column_config,
            width='stretch'
        )
        
    else:
        st.info("No access logs found.")
