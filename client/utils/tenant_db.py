"""
Tenant-aware database utilities

This module provides helper functions for database operations
that automatically use tenant-prefixed table names.
"""

from client.utils.supabase_client import get_supabase
from client.tenant_loader import get_tenant_context


def get_tenant_table(table_name: str):
    """
    Get Supabase query builder for a tenant-specific table
    
    Args:
        table_name: Base table name (without prefix)
        
    Returns:
        Supabase table query builder
    """
    supabase = get_supabase()
    tenant_context = get_tenant_context()
    full_table_name = tenant_context.get_table_name(table_name)
    return supabase.table(full_table_name)


def get_table_name(table_name: str) -> str:
    """
    Get full table name with tenant prefix
    
    Args:
        table_name: Base table name (without prefix)
        
    Returns:
        Full table name with tenant prefix
    """
    tenant_context = get_tenant_context()
    return tenant_context.get_table_name(table_name)
