"""
Test script for Multi-Tenant Platform

This script tests the core platform functionality without needing
the Streamlit UI or database connection.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_tenant_manager():
    """Test TenantManager functionality"""
    print("\n" + "="*60)
    print("TEST 1: Tenant Manager")
    print("="*60)
    
    try:
        from platform_core import get_tenant_manager
        
        manager = get_tenant_manager()
        print("✅ TenantManager initialized")
        
        # Test get all tenants
        tenants = manager.get_all_tenants()
        print(f"✅ Found {len(tenants)} tenants:")
        for tenant in tenants:
            print(f"   - {tenant.tenant_name} ({tenant.tenant_id})")
        
        # Test get specific tenant
        eduqure = manager.get_tenant('eduqure')
        if eduqure:
            print(f"✅ Retrieved EduQure tenant: {eduqure.tenant_name}")
            print(f"   Schema prefix: {eduqure.database.get('schema_prefix')}")
            print(f"   Tables: {len(eduqure.database.get('tables', {}))}")
            print(f"   Dashboard tabs: {len(eduqure.dashboard.get('tabs', []))}")
        else:
            print("❌ Failed to retrieve EduQure tenant")
            return False
        
        # Test validation
        is_valid, error = manager.validate_tenant_config('eduqure')
        if is_valid:
            print("✅ EduQure configuration is valid")
        else:
            print(f"❌ EduQure configuration invalid: {error}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ TenantManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_manager():
    """Test DatabaseManager functionality"""
    print("\n" + "="*60)
    print("TEST 2: Database Manager")
    print("="*60)
    
    try:
        from platform_core import get_database_manager
        
        # Note: This will work without Supabase credentials for SQL generation
        db_manager = get_database_manager()
        print("✅ DatabaseManager initialized")
        
        # Test SQL generation
        sql = db_manager.generate_migration_sql('eduqure')
        
        if sql and len(sql) > 0:
            lines = sql.split('\n')
            print(f"✅ Generated SQL migration: {len(lines)} lines")
            
            # Count CREATE TABLE statements
            create_table_count = sql.count('CREATE TABLE')
            print(f"   CREATE TABLE statements: {create_table_count}")
            
            # Count RLS policies
            rls_count = sql.count('CREATE POLICY')
            print(f"   RLS policies: {rls_count}")
            
            # Check for tenant prefix
            if 'eduqure_' in sql:
                print("✅ SQL contains tenant prefix 'eduqure_'")
            else:
                print("❌ SQL missing tenant prefix")
                return False
        else:
            print("❌ Failed to generate SQL")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ DatabaseManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tenant_loader():
    """Test TenantLoader functionality"""
    print("\n" + "="*60)
    print("TEST 3: Tenant Loader")
    print("="*60)
    
    try:
        from client.tenant_loader import TenantContext
        
        # Create tenant context
        context = TenantContext('eduqure')
        print("✅ TenantContext created for 'eduqure'")
        
        # Test schema prefix
        prefix = context.get_schema_prefix()
        if prefix == 'eduqure_':
            print(f"✅ Schema prefix: '{prefix}'")
        else:
            print(f"❌ Expected 'eduqure_' but got '{prefix}'")
            return False
        
        # Test table name generation
        table_name = context.get_table_name('persons')
        if table_name == 'eduqure_persons':
            print(f"✅ Table name for 'persons': '{table_name}'")
        else:
            print(f"❌ Expected 'eduqure_persons' but got '{table_name}'")
            return False
        
        # Test dashboard config
        title = context.get_dashboard_title()
        print(f"✅ Dashboard title: '{title}'")
        
        tabs = context.get_enabled_tabs()
        print(f"✅ Enabled tabs: {len(tabs)}")
        for tab in tabs:
            print(f"   - {tab['name']} ({tab['module']})")
        
        return True
        
    except Exception as e:
        print(f"❌ TenantLoader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tenant_db_helper():
    """Test tenant database helper"""
    print("\n" + "="*60)
    print("TEST 4: Tenant DB Helper")
    print("="*60)
    
    try:
        from client.utils.tenant_db import get_table_name
        from client.tenant_loader import TenantContext
        
        # We need to simulate a session state for this
        # For now, just test the import works
        print("✅ tenant_db module imported successfully")
        print("   Note: Full testing requires Streamlit session state")
        
        return True
        
    except Exception as e:
        print(f"❌ tenant_db test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MULTI-TENANT PLATFORM - FUNCTIONALITY TESTS")
    print("="*60)
    
    results = {}
    
    results['tenant_manager'] = test_tenant_manager()
    results['database_manager'] = test_database_manager()
    results['tenant_loader'] = test_tenant_loader()
    results['tenant_db_helper'] = test_tenant_db_helper()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\nThe multi-tenant platform core is working correctly.")
        print("\nNext steps:")
        print("1. Apply database migration: tenants/eduqure/migration_initial.sql")
        print("2. Test Streamlit dashboard at http://localhost:8501")
        print("3. Update firmware to use new table names")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("="*60)
        print("\nPlease review the errors above and fix the issues.")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
