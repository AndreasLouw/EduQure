import streamlit as st
import pandas as pd
from client.utils.supabase_client import get_supabase
from client.tenant_loader import get_tenant_context

def get_unidentified_logs():
    """Fetch recent unidentified card scans"""
    try:
        supabase = get_supabase()
        tenant_context = get_tenant_context()
        table_name = tenant_context.get_table_name("unidentified_cards")
        
        response = supabase.table(table_name).select("*").order("created_at", desc=True).limit(50).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching unidentified logs: {e}")
        return []

def render():
    """Main render function for Live Monitor tab"""
    st.markdown("### Unidentified Card Scans")
    data = get_unidentified_logs()

    if data:
        df = pd.DataFrame(data)
        
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])
            if df["created_at"].dt.tz is None:
                 df["created_at"] = df["created_at"].dt.tz_localize("UTC")
            df["created_at"] = df["created_at"].dt.tz_convert("Africa/Johannesburg")
        
        display_cols = ["id", "card_uid", "lock", "created_at"]
        display_cols = [c for c in display_cols if c in df.columns]
        
        st.dataframe(df[display_cols], width='stretch')
        st.metric("Recent Unidentified Scans", len(df))
    else:
        st.info("No unidentified logs found.")
