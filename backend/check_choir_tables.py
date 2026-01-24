
import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def get_table_info(table_name):
    print(f"Checking {table_name}...")
    try:
        response = supabase.table(table_name).select("*").limit(1).execute()
        print(f"Table '{table_name}' exists. Sample data: {response.data}")
    except Exception as e:
        print(f"Table '{table_name}' check failed: {e}")

get_table_info("choir_register")
get_table_info("choir_practice_dates")
