import streamlit as st
from client.utils.auth import init_auth_state, login, render_sidebar
from client.tabs import choir_attendance, live_monitor, access_logs

# Page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="School Attendance Live Feed",
    page_icon="🏫",
    layout="wide",  # This enables full-width layout
    initial_sidebar_state="expanded"
)

st.title("🏫 School Attendance Live Feed")

# Initialize authentication
init_auth_state()

# --- Main App Logic ---
if not st.session_state.authenticated:
    login()
else:
    # Sidebar for logout
    render_sidebar()
    
    # Refresh button
    if st.button('Refresh Data'):
        st.rerun()

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🎵 Choir Attendance", "⚠️ Live Monitor", "🔒 Access Logs"])

    with tab1:
        choir_attendance.render()

    with tab2:
        live_monitor.render()

    with tab3:
        access_logs.render()

