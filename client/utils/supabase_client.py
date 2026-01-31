import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def get_secret(key_name):
    """Get secret from Streamlit secrets or environment variables"""
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.environ.get(key_name)

@st.cache_resource
def init_supabase():
    """Initialize and cache Supabase client"""
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    
    if not url or not key:
        st.error("Supabase URL and Key not found. Please check your .env file.")
        st.stop()
    
    return create_client(url, key)

def get_supabase():
    """Get the Supabase client instance"""
    return init_supabase()
