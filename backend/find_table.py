import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

print("List of tables:")
try:
    # Query Postgres information_schema (if exposed)
    # Often Supabase exposes this via a view or RPC, but raw SQL via client might not work directly without RPC.
    # But we can try to guess common names.
    pass
except:
    pass

candidates = ["person", "Person", "persons", "Persons", "student", "Student", "students", "Students", "users", "User", "people"]

for c in candidates:
    try:
        res = supabase.table(c).select("count", count="exact").limit(0).execute()
        print(f"FOUND: '{c}' - Count: {res.count}")
    except Exception as e:
        # Just print the error code/msg briefly
        msg = str(e)
        if "Could not find the table" in msg:
            print(f"MISSING: '{c}'")
        else:
            print(f"ERROR '{c}': {msg}")
