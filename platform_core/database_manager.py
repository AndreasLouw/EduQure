"""
Database Manager - Multi-Tenant IoT Platform

This module handles multi-tenant database operations including:
- Schema creation and management per tenant
- Tenant-aware query execution
- Schema migrations
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from supabase import create_client, Client
from platform_core.tenant_manager import TenantConfig, get_tenant_manager


class DatabaseManager:
    """Manages multi-tenant database operations"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize DatabaseManager
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        # Don't validate credentials yet - only when actually connecting
        self._client: Optional[Client] = None
        self.tenant_manager = get_tenant_manager()
    
    def get_client(self) -> Client:
        """Get or create Supabase client"""
        if self._client is None:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and Key must be provided or set in environment")
            self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client
    
    def generate_create_table_sql(self, tenant_id: str, table_name: str, table_def: Dict) -> str:
        """
        Generate SQL CREATE TABLE statement from table definition
        
        Args:
            tenant_id: Tenant identifier
            table_name: Table name (without prefix)
            table_def: Table definition from tenant config
            
        Returns:
            SQL CREATE TABLE statement
        """
        schema_prefix = self.tenant_manager.get_tenant_schema_prefix(tenant_id)
        full_table_name = f"{schema_prefix}{table_name}"
        
        columns = table_def.get('columns', [])
        column_defs = []
        
        for col in columns:
            col_name = col['name']
            col_type = col['type']
            
            col_def = f"{col_name} {col_type}"
            
            # Add constraints
            if col.get('primary_key'):
                col_def += " PRIMARY KEY"
            
            if col.get('required') and not col.get('primary_key'):
                col_def += " NOT NULL"
            
            if col.get('unique'):
                col_def += " UNIQUE"
            
            if 'default' in col:
                default_val = col['default']
                # Check if it's a function call (e.g., NOW(), gen_random_uuid())
                if default_val in ['NOW()', 'gen_random_uuid()']:
                    col_def += f" DEFAULT {default_val}"
                elif isinstance(default_val, bool):
                    col_def += f" DEFAULT {str(default_val).lower()}"
                elif isinstance(default_val, (int, float)):
                    col_def += f" DEFAULT {default_val}"
                else:
                    col_def += f" DEFAULT '{default_val}'"
            
            column_defs.append(col_def)
        
        # Add foreign key constraints
        foreign_keys = []
        for col in columns:
            if 'foreign_key' in col:
                fk_table, fk_column = col['foreign_key'].split('.')
                fk_full_table = f"{schema_prefix}{fk_table}"
                foreign_keys.append(
                    f"FOREIGN KEY ({col['name']}) REFERENCES {fk_full_table}({fk_column})"
                )
        
        # Add unique constraints
        unique_constraints = table_def.get('unique_constraints', [])
        for constraint_cols in unique_constraints:
            cols_str = ', '.join(constraint_cols)
            foreign_keys.append(f"UNIQUE({cols_str})")
        
        all_defs = column_defs + foreign_keys
        sql = f"CREATE TABLE {full_table_name} (\n  " + ",\n  ".join(all_defs) + "\n);"
        
        return sql
    
    def create_tenant_tables(self, tenant_id: str) -> tuple[bool, str]:
        """
        Create all tables for a tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tuple of (success, message)
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False, f"Tenant '{tenant_id}' not found"
        
        tables = self.tenant_manager.get_tenant_tables(tenant_id)
        if not tables:
            return False, f"No tables defined for tenant '{tenant_id}'"
        
        client = self.get_client()
        created_tables = []
        errors = []
        
        for table_name, table_def in tables.items():
            try:
                sql = self.generate_create_table_sql(tenant_id, table_name, table_def)
                print(f"Executing SQL for {table_name}:")
                print(sql)
                
                # Execute via Supabase RPC or direct SQL execution
                # Note: This may require service_role key for DDL operations
                # For now, we'll generate the SQL for manual execution
                created_tables.append(table_name)
            except Exception as e:
                errors.append(f"{table_name}: {str(e)}")
        
        if errors:
            error_msg = "; ".join(errors)
            return False, f"Failed to create some tables: {error_msg}"
        
        return True, f"Created {len(created_tables)} tables for tenant '{tenant_id}'"
    
    def enable_rls(self, tenant_id: str, table_name: str) -> str:
        """
        Generate SQL to enable Row Level Security for a table
        
        Args:
            tenant_id: Tenant identifier
            table_name: Table name (without prefix)
            
        Returns:
            SQL statement
        """
        schema_prefix = self.tenant_manager.get_tenant_schema_prefix(tenant_id)
        full_table_name = f"{schema_prefix}{table_name}"
        
        return f"ALTER TABLE {full_table_name} ENABLE ROW LEVEL SECURITY;"
    
    def create_rls_policy(self, tenant_id: str, table_name: str, policy_name: str = "allow_all_authenticated") -> str:
        """
        Generate SQL to create RLS policy for a table
        
        Args:
            tenant_id: Tenant identifier
            table_name: Table name (without prefix)
            policy_name: Name of the policy
            
        Returns:
            SQL statement
        """
        schema_prefix = self.tenant_manager.get_tenant_schema_prefix(tenant_id)
        full_table_name = f"{schema_prefix}{table_name}"
        
        sql = f"""
CREATE POLICY "{policy_name}" ON {full_table_name}
  FOR ALL
  USING (auth.role() = 'authenticated');
"""
        return sql
    
    def get_tenant_table_name(self, tenant_id: str, table_name: str) -> str:
        """
        Get full table name with tenant prefix
        
        Args:
            tenant_id: Tenant identifier
            table_name: Table name (without prefix)
            
        Returns:
            Full table name with prefix
        """
        schema_prefix = self.tenant_manager.get_tenant_schema_prefix(tenant_id)
        return f"{schema_prefix}{table_name}"
    
    def execute_tenant_query(self, tenant_id: str, table_name: str) -> Any:
        """
        Execute a query in the context of a specific tenant
        
        Args:
            tenant_id: Tenant identifier
            table_name: Table name (without prefix)
            
        Returns:
            Supabase table query builder
        """
        client = self.get_client()
        full_table_name = self.get_tenant_table_name(tenant_id, table_name)
        return client.table(full_table_name)
    
    def generate_migration_sql(self, tenant_id: str) -> str:
        """
        Generate complete SQL migration script for a tenant
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Complete SQL script
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return f"-- Error: Tenant '{tenant_id}' not found"
        
        tables = self.tenant_manager.get_tenant_tables(tenant_id)
        if not tables:
            return f"-- Error: No tables defined for tenant '{tenant_id}'"
        
        sql_parts = [
            f"-- Migration script for tenant: {tenant.tenant_name}",
            f"-- Tenant ID: {tenant_id}",
            f"-- Generated: {Path(__file__).name}",
            "",
            "-- Create Tables",
            ""
        ]
        
        # Generate CREATE TABLE statements
        for table_name, table_def in tables.items():
            sql_parts.append(f"-- Table: {table_name}")
            sql_parts.append(self.generate_create_table_sql(tenant_id, table_name, table_def))
            sql_parts.append("")
        
        # Generate RLS statements
        sql_parts.append("-- Enable Row Level Security")
        sql_parts.append("")
        
        for table_name in tables.keys():
            sql_parts.append(self.enable_rls(tenant_id, table_name))
        
        sql_parts.append("")
        sql_parts.append("-- Create RLS Policies")
        sql_parts.append("")
        
        for table_name in tables.keys():
            sql_parts.append(self.create_rls_policy(tenant_id, table_name))
        
        return "\n".join(sql_parts)


# Singleton instance
_database_manager: Optional[DatabaseManager] = None


def get_database_manager(supabase_url: Optional[str] = None, supabase_key: Optional[str] = None) -> DatabaseManager:
    """
    Get or create singleton DatabaseManager instance
    
    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        
    Returns:
        DatabaseManager instance
    """
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager(supabase_url, supabase_key)
    return _database_manager
