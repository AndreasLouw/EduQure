import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def try_table(name):
    print(f"\nTesting table: '{name}'")
    try:
        res = supabase.table(name).select("*").limit(3).execute()
        print(f"SUCCESS. Rows: {len(res.data)}")
        if res.data:
            print("Sample:", res.data[0])
    except Exception as e:
        print(f"FAILED: {e}")

try_table("person")
try_table("persons")
try_table("student")
try_table("students")
