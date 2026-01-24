import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials")
    exit()

supabase: Client = create_client(url, key)

print("--- Access Logs UIDs ---")
try:
    logs = supabase.table("access_logs").select("card_uid").limit(5).execute()
    for row in logs.data:
        print(f"Log UID: '{row.get('card_uid')}'")
except Exception as e:
    print(e)

print("\n--- Person UIDs ---")
try:
    persons = supabase.table("person").select("card_uid, name").limit(5).execute()
    for row in persons.data:
        print(f"Person: {row.get('name')} | UID: '{row.get('card_uid')}'")
except Exception as e:
    print(e)
