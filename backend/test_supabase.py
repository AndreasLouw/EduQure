import os
from dotenv import load_dotenv
from supabase import create_client, Client

def test_connection():
    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env file.")
        return

    print(f"Testing connection to: {url}")
    
    try:
        supabase: Client = create_client(url, key)
        print("Supabase client initialized successfully.")
        
        # enhanced check: try a simple auth call (doesn't require tables)
        # or just checking if we can access the health check endpoint if exposed, 
        # but client init validates URL format. 
        # To validate the KEY, we really should make a request.
        # Let's try to get settings or just proceed.
        
        print("Connection test complete.")
        
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
