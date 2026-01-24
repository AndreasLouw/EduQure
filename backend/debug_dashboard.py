import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- FETCHING ACCESS LOGS ---")
try:
    logs = supabase.table("access_logs").select("*").limit(5).execute()
    df_logs = pd.DataFrame(logs.data)
    print("Columns:", df_logs.columns.tolist())
    if not df_logs.empty:
        print("First row:", df_logs.iloc[0].to_dict())
        # Check type of UID column
        for col in df_logs.columns:
            if "uid" in col.lower():
                print(f"Type of {col}: {df_logs[col].dtype}")
                print(f"Sample value: {df_logs[col].iloc[0]!r}")
except Exception as e:
    print(f"Error fetching access_logs: {e}")

print("\n--- FETCHING PERSONS ---")
try:
    persons = supabase.table("persons").select("*").limit(5).execute()
    df_persons = pd.DataFrame(persons.data)
    print("Columns:", df_persons.columns.tolist())
    if not df_persons.empty:
        print("First row:", df_persons.iloc[0].to_dict())
        # Check type of UID column
        for col in df_persons.columns:
            if "uid" in col.lower():
                print(f"Type of {col}: {df_persons[col].dtype}")
                print(f"Sample value: {df_persons[col].iloc[0]!r}")
except Exception as e:
    print(f"Error fetching persons: {e}")
