import streamlit as st
from client.utils.auth import init_auth_state, login, render_sidebar
from client.tenant_loader import init_tenant_session, get_tenant_context, render_tabs


def main():
    # Page configuration - MUST be the first Streamlit command
    st.set_page_config(
        page_title="Multi-Tenant IoT Platform",
        page_icon="🏫",
        initial_sidebar_state="expanded"
    )

    # Initialize authentication
    init_auth_state()

    # --- Main App Logic ---
    if not st.session_state.authenticated:
        login()
    else:
        # Initialize tenant context
        tenant_context = init_tenant_session()
        
        # Update page title based on tenant
        st.title(tenant_context.get_dashboard_title())
        
        # Sidebar for logout
        render_sidebar()
        
        # Refresh button
        if st.button('Refresh Data'):
            st.rerun()

        # Render tenant-specific tabs
        render_tabs(tenant_context)

if __name__ == "__main__":
    main()
