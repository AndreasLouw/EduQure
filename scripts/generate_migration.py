"""
Generate SQL Migration for Tenant

This script generates a complete SQL migration file for a tenant
based on their configuration.

Usage:
    python scripts/generate_migration.py --tenant eduqure
    python scripts/generate_migration.py --tenant eduqure --output migrations/eduqure_initial.sql
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from platform_core import get_tenant_manager, get_database_manager


def main():
    parser = argparse.ArgumentParser(description='Generate SQL migration for tenant')
    parser.add_argument('--tenant', required=True, help='Tenant ID')
    parser.add_argument('--output', help='Output SQL file path (optional)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Initialize managers
        tenant_manager = get_tenant_manager()
        db_manager = get_database_manager()
        
        # Validate tenant exists
        tenant = tenant_manager.get_tenant(args.tenant)
        if not tenant:
            print(f"❌ Error: Tenant '{args.tenant}' not found")
            print(f"Available tenants: {', '.join(tenant_manager.get_tenant_ids())}")
            sys.exit(1)
        
        # Validate tenant configuration
        is_valid, error_msg = tenant_manager.validate_tenant_config(args.tenant)
        if not is_valid:
            print(f"❌ Error: Invalid tenant configuration: {error_msg}")
            sys.exit(1)
        
        if args.verbose:
            print(f"✅ Generating migration for: {tenant.tenant_name}")
        
        # Generate SQL
        sql = db_manager.generate_migration_sql(args.tenant)
        
        # Output
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(sql, encoding='utf-8')
            print(f"✅ Migration saved to: {output_path}")
        else:
            print(sql)
        
        if args.verbose:
            tables = tenant_manager.get_tenant_tables(args.tenant)
            print(f"\n📊 Generated {len(tables)} tables")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
