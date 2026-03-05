"""
Tenant Manager - Multi-Tenant IoT Platform

This module handles tenant configuration loading, validation, and management.
It provides a centralized system for managing multiple IoT client tenants.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TenantConfig:
    """Tenant configuration data class"""
    tenant_id: str
    tenant_name: str
    tenant_type: str
    device_type: str
    database: Dict
    firmware: Dict
    dashboard: Dict
    config_path: Optional[Path] = None
    
    @classmethod
    def from_json(cls, config_path: Path) -> 'TenantConfig':
        """Load tenant configuration from JSON file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(
            tenant_id=data['tenant_id'],
            tenant_name=data['tenant_name'],
            tenant_type=data['tenant_type'],
            device_type=data['device_type'],
            database=data['database'],
            firmware=data['firmware'],
            dashboard=data['dashboard'],
            config_path=config_path
        )


class TenantManager:
    """Manages multi-tenant configurations and operations"""
    
    def __init__(self, tenants_dir: Optional[Path] = None):
        """
        Initialize TenantManager
        
        Args:
            tenants_dir: Path to tenants directory. Defaults to './tenants'
        """
        if tenants_dir is None:
            # Default to tenants directory in project root
            project_root = Path(__file__).parent.parent
            tenants_dir = project_root / 'tenants'
        
        self.tenants_dir = Path(tenants_dir)
        self._tenants: Dict[str, TenantConfig] = {}
        self._load_all_tenants()
    
    def _load_all_tenants(self):
        """Scan tenants directory and load all tenant configurations"""
        if not self.tenants_dir.exists():
            raise FileNotFoundError(f"Tenants directory not found: {self.tenants_dir}")
        
        for tenant_dir in self.tenants_dir.iterdir():
            if tenant_dir.is_dir():
                config_file = tenant_dir / 'tenant.config.json'
                if config_file.exists():
                    try:
                        tenant_config = TenantConfig.from_json(config_file)
                        self._tenants[tenant_config.tenant_id] = tenant_config
                        print(f"✅ Loaded tenant: {tenant_config.tenant_name} ({tenant_config.tenant_id})")
                    except Exception as e:
                        print(f"❌ Failed to load tenant from {config_file}: {e}")
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        Get tenant configuration by ID
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            TenantConfig if found, None otherwise
        """
        return self._tenants.get(tenant_id)
    
    def get_all_tenants(self) -> List[TenantConfig]:
        """Get list of all loaded tenants"""
        return list(self._tenants.values())
    
    def get_tenant_ids(self) -> List[str]:
        """Get list of all tenant IDs"""
        return list(self._tenants.keys())
    
    def validate_tenant_config(self, tenant_id: str) -> tuple[bool, Optional[str]]:
        """
        Validate tenant configuration
        
        Args:
            tenant_id: Tenant ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False, f"Tenant '{tenant_id}' not found"
        
        # Validate required fields
        required_fields = ['tenant_id', 'tenant_name', 'tenant_type', 'device_type']
        for field in required_fields:
            if not getattr(tenant, field, None):
                return False, f"Missing required field: {field}"
        
        # Validate database config
        if not tenant.database:
            return False, "Missing database configuration"
        
        if 'schema_prefix' not in tenant.database:
            return False, "Missing database.schema_prefix"
        
        if 'tables' not in tenant.database or not tenant.database['tables']:
            return False, "Missing or empty database.tables"
        
        # Validate firmware config
        if not tenant.firmware:
            return False, "Missing firmware configuration"
        
        if 'device_type' not in tenant.firmware:
            return False, "Missing firmware.device_type"
        
        # Validate dashboard config
        if not tenant.dashboard:
            return False, "Missing dashboard configuration"
        
        if 'tabs' not in tenant.dashboard or not tenant.dashboard['tabs']:
            return False, "Missing or empty dashboard.tabs"
        
        return True, None
    
    def get_tenant_schema_prefix(self, tenant_id: str) -> Optional[str]:
        """Get database schema prefix for a tenant"""
        tenant = self.get_tenant(tenant_id)
        if tenant:
            return tenant.database.get('schema_prefix')
        return None
    
    def get_tenant_tables(self, tenant_id: str) -> Optional[Dict]:
        """Get database table definitions for a tenant"""
        tenant = self.get_tenant(tenant_id)
        if tenant:
            return tenant.database.get('tables')
        return None
    
    def get_tenant_dashboard_tabs(self, tenant_id: str) -> Optional[List[Dict]]:
        """Get dashboard tab configuration for a tenant"""
        tenant = self.get_tenant(tenant_id)
        if tenant:
            return tenant.dashboard.get('tabs')
        return None
    
    def create_tenant(self, config: Dict, overwrite: bool = False) -> tuple[bool, str]:
        """
        Create a new tenant from configuration dictionary
        
        Args:
            config: Tenant configuration dictionary
            overwrite: Whether to overwrite existing tenant
            
        Returns:
            Tuple of (success, message)
        """
        tenant_id = config.get('tenant_id')
        if not tenant_id:
            return False, "Missing tenant_id in configuration"
        
        # Check if tenant already exists
        if tenant_id in self._tenants and not overwrite:
            return False, f"Tenant '{tenant_id}' already exists"
        
        # Create tenant directory
        tenant_dir = self.tenants_dir / tenant_id
        tenant_dir.mkdir(exist_ok=True)
        
        # Write config file
        config_file = tenant_dir / 'tenant.config.json'
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            # Load the new tenant
            tenant_config = TenantConfig.from_json(config_file)
            self._tenants[tenant_id] = tenant_config
            
            return True, f"Tenant '{tenant_id}' created successfully"
        except Exception as e:
            return False, f"Failed to create tenant: {e}"
    
    def reload_tenant(self, tenant_id: str) -> tuple[bool, str]:
        """
        Reload tenant configuration from disk
        
        Args:
            tenant_id: Tenant ID to reload
            
        Returns:
            Tuple of (success, message)
        """
        tenant_dir = self.tenants_dir / tenant_id
        config_file = tenant_dir / 'tenant.config.json'
        
        if not config_file.exists():
            return False, f"Config file not found: {config_file}"
        
        try:
            tenant_config = TenantConfig.from_json(config_file)
            self._tenants[tenant_id] = tenant_config
            return True, f"Tenant '{tenant_id}' reloaded successfully"
        except Exception as e:
            return False, f"Failed to reload tenant: {e}"
    
    def __repr__(self):
        return f"TenantManager(tenants={len(self._tenants)})"


# Singleton instance
_tenant_manager: Optional[TenantManager] = None


def get_tenant_manager(tenants_dir: Optional[Path] = None) -> TenantManager:
    """
    Get or create singleton TenantManager instance
    
    Args:
        tenants_dir: Path to tenants directory (only used on first call)
        
    Returns:
        TenantManager instance
    """
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager(tenants_dir)
    return _tenant_manager
