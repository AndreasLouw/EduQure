"""
List All Tenants

This script lists all configured tenants with their details.

Usage:
    python scripts/list_tenants.py
    python scripts/list_tenants.py --verbose
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from platform_core import get_tenant_manager


def main():
    parser = argparse.ArgumentParser(description='List all configured tenants')
    parser.add_argument('--verbose', action='store_true', help='Show detailed information')
    
    args = parser.parse_args()
    
    try:
        tenant_manager = get_tenant_manager()
        tenants = tenant_manager.get_all_tenants()
        
        if not tenants:
            print("No tenants configured")
            return
        
        print(f"\n{'='*60}")
        print(f"Multi-Tenant IoT Platform - Configured Tenants")
        print(f"{'='*60}\n")
        
        for tenant in tenants:
            print(f"📦 {tenant.tenant_name}")
            print(f"   ID: {tenant.tenant_id}")
            print(f"   Type: {tenant.tenant_type}")
            print(f"   Device: {tenant.device_type}")
            
            if args.verbose:
                # Show database info
                tables = tenant.database.get('tables', {})
                print(f"   Tables: {len(tables)} ({', '.join(tables.keys())})")
                
                # Show dashboard tabs
                tabs = tenant.dashboard.get('tabs', [])
                enabled_tabs = [t['name'] for t in tabs if t.get('enabled', True)]
                print(f"   Dashboard Tabs: {len(enabled_tabs)}")
                for tab in enabled_tabs:
                    print(f"      - {tab}")
                
                # Validation
                is_valid, error_msg = tenant_manager.validate_tenant_config(tenant.tenant_id)
                status = "✅ Valid" if is_valid else f"❌ Invalid: {error_msg}"
                print(f"   Status: {status}")
            
            print()
        
        print(f"Total: {len(tenants)} tenant(s)\n")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
