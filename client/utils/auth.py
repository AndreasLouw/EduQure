import streamlit as st
from .supabase_client import get_supabase

def init_auth_state():
    """Initialize authentication state in session"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

def login():
    """Display login form and handle authentication"""
    st.header("Login")
    email = st.text_input("Email").strip()
    password = st.text_input("Password", type="password").strip()
    
    if st.button("Log In"):
        try:
            supabase = get_supabase()
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.success("Logged in successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def logout():
    """Handle user logout"""
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.authenticated = False
    st.session_state.pop("user", None)
    st.rerun()

def render_sidebar():
    """Render sidebar with user info and logout button"""
    with st.sidebar:
        st.write(f"Logged in as: {st.session_state.user.email}")
        if st.button("Log Out"):
            logout()
