"""
Tenant Loader - Multi-Tenant Dashboard Support

This module handles loading tenant-specific configurations and dynamically
importing dashboard tabs based on tenant settings.
"""

import streamlit as st
import importlib
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from platform_core import get_tenant_manager, TenantConfig


class TenantContext:
    """Manages tenant context for the current session"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.tenant_manager = get_tenant_manager()
        self.config = self.tenant_manager.get_tenant(tenant_id)
        
        if not self.config:
            raise ValueError(f"Tenant '{tenant_id}' not found")
    
    def get_schema_prefix(self) -> str:
        """Get the database schema prefix for this tenant"""
        return self.config.database.get('schema_prefix', '')
    
    def get_table_name(self, base_table_name: str) -> str:
        """Get the full table name with tenant prefix"""
        prefix = self.get_schema_prefix()
        return f"{prefix}{base_table_name}"
    
    def get_dashboard_title(self) -> str:
        """Get the dashboard title"""
        return self.config.dashboard.get('title', self.config.tenant_name)
    
    def get_tabs(self) -> List[Dict[str, Any]]:
        """Get configured dashboard tabs"""
        return self.config.dashboard.get('tabs', [])
    
    def get_enabled_tabs(self) -> List[Dict[str, Any]]:
        """Get only enabled dashboard tabs"""
        return [tab for tab in self.get_tabs() if tab.get('enabled', True)]


def init_tenant_session(tenant_id: Optional[str] = None) -> TenantContext:
    """
    Initialize tenant context in session state
    
    Args:
        tenant_id: Tenant ID to load. If None, uses session state or default.
        
    Returns:
        TenantContext instance
    """
    # Check if tenant is already in session
    if 'tenant_id' not in st.session_state:
        if tenant_id is None:
            # Default to first available tenant (for now)
            manager = get_tenant_manager()
            tenant_ids = manager.get_tenant_ids()
            if not tenant_ids:
                st.error("No tenants configured")
                st.stop()
            tenant_id = tenant_ids[0]  # Default to first tenant
        
        st.session_state.tenant_id = tenant_id
    
    # Create or retrieve tenant context
    if 'tenant_context' not in st.session_state:
        st.session_state.tenant_context = TenantContext(st.session_state.tenant_id)
    
    return st.session_state.tenant_context


def get_tenant_context() -> TenantContext:
    """Get the current tenant context from session state"""
    if 'tenant_context' not in st.session_state:
        return init_tenant_session()
    return st.session_state.tenant_context


def load_tab_module(module_path: str):
    """
    Dynamically import a tab module
    
    Args:
        module_path: Python module path (e.g., 'client.tabs.eduqure.choir_attendance')
        
    Returns:
        Imported module
    """
    try:
        module = importlib.import_module(module_path)
        return module
    except ImportError as e:
        st.error(f"Failed to load tab module '{module_path}': {e}")
        return None


def render_tenant_selector():
    """
    Render tenant selection dropdown in sidebar
    
    Returns:
        Selected tenant ID
    """
    manager = get_tenant_manager()
    tenants = manager.get_all_tenants()
    
    if not tenants:
        st.sidebar.error("No tenants configured")
        return None
    
    # Create tenant options
    tenant_options = {t.tenant_name: t.tenant_id for t in tenants}
    
    # Get current tenant
    current_tenant_id = st.session_state.get('tenant_id')
    current_tenant_name = None
    for t in tenants:
        if t.tenant_id == current_tenant_id:
            current_tenant_name = t.tenant_name
            break
    
    # Render selector
    selected_name = st.sidebar.selectbox(
        "Select Tenant",
        list(tenant_options.keys()),
        index=list(tenant_options.values()).index(current_tenant_id) if current_tenant_id else 0
    )
    
    selected_id = tenant_options[selected_name]
    
    # Check if tenant changed
    if selected_id != current_tenant_id:
        st.session_state.tenant_id = selected_id
        st.session_state.tenant_context = TenantContext(selected_id)
        st.rerun()
    
    return selected_id


def render_tabs(tenant_context: TenantContext):
    """
    Render dashboard tabs based on tenant configuration
    
    Args:
        tenant_context: Current tenant context
    """
    enabled_tabs = tenant_context.get_enabled_tabs()
    
    if not enabled_tabs:
        st.warning("No tabs configured for this tenant")
        return
    
    # Create tab objects
    tab_names = [tab['name'] for tab in enabled_tabs]
    tab_objects = st.tabs(tab_names)
    
    # Render each tab
    for tab_obj, tab_config in zip(tab_objects, enabled_tabs):
        with tab_obj:
            module_path = tab_config.get('module')
            if not module_path:
                st.error(f"No module specified for tab: {tab_config.get('id')}")
                continue
            
            # Load and render tab module
            tab_module = load_tab_module(module_path)
            if tab_module and hasattr(tab_module, 'render'):
                try:
                    tab_module.render()
                except Exception as e:
                    st.error(f"Error rendering tab '{tab_config['name']}': {e}")
                    import traceback
                    st.code(traceback.format_exc())
            else:
                st.error(f"Tab module '{module_path}' does not have a 'render()' function")


def get_supabase_for_tenant():
    """
    Get Supabase client configured for current tenant
    
    This is a wrapper around the standard get_supabase() that provides
    tenant context awareness.
    
    Returns:
        Supabase client
    """
    from client.utils.supabase_client import get_supabase
    return get_supabase()
