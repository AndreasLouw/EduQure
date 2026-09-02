import streamlit as st
from client.utils.auth import init_auth_state, login, render_sidebar
from client.tabs import choir_attendance, live_monitor, access_logs, choir_management


def main():
    # Page configuration - MUST be the first Streamlit command
    st.set_page_config(
        page_title="School Attendance Live Feed",
        page_icon="🏫",
        layout="wide",  # This enables full-width layout
        initial_sidebar_state="expanded"
    )

    # Initialize authentication
    init_auth_state()

    # --- Main App Logic ---
    if not st.session_state.authenticated:
        st.header("🏫 School Attendance Live Feed")
        login()
        return

    # Multipage app: only the active page's code (and its queries) executes
    # on each rerun. With st.tabs, all four sections ran on every rerun.
    page = st.navigation([
        st.Page(choir_attendance.render, title="Choir Attendance", icon="🎵", default=True),
        st.Page(live_monitor.render, title="Live Monitor", icon="⚠️"),
        st.Page(access_logs.render, title="Access Logs", icon="🔒"),
        st.Page(choir_management.render, title="Management", icon="⚙️"),
    ])

    # Sidebar (user info, refresh, logout) renders on every page
    render_sidebar()

    page.run()


if __name__ == "__main__":
    main()

