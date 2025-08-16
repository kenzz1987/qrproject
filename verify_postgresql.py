#!/usr/bin/env python3
"""
PostgreSQL Setup Verification Script
Verifies that the application can connect to PostgreSQL and create tables
"""

import os
import sys

def verify_postgresql():
    """Verify PostgreSQL setup"""
    print("🔍 Verifying PostgreSQL Setup")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("💡 Set it with: set DATABASE_URL=postgresql://user:pass@host:port/db")
        return False
    
    print(f"✅ DATABASE_URL found: {database_url[:30]}...")
    
    # Try to import the database manager
    try:
        from database import get_db_manager
        print("✅ Database module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import database module: {e}")
        print("💡 Install psycopg2-binary: pip install psycopg2-binary")
        return False
    
    # Test database connection
    try:
        db_manager = get_db_manager()
        print(f"✅ Database manager created (type: {db_manager.db_type})")
        
        # Test simple query
        result = db_manager.execute_query('SELECT 1 as test', fetch='one')
        if result:
            print("✅ Database connection successful")
            
            # Test table initialization
            db_manager.init_tables()
            print("✅ Database tables initialized")
            
            # Test business cards table
            result = db_manager.execute_query('SELECT COUNT(*) FROM business_cards', fetch='one')
            count = result[0] if isinstance(result, (list, tuple)) else result['count']
            print(f"✅ Business cards table working (count: {count})")
            
            # Test QR codes table
            result = db_manager.execute_query('SELECT COUNT(*) FROM qr_codes', fetch='one')
            count = result[0] if isinstance(result, (list, tuple)) else result['count']
            print(f"✅ QR codes table working (count: {count})")
            
            print("\n🎉 PostgreSQL setup verification successful!")
            print("✅ The application is ready to run with PostgreSQL")
            return True
            
        else:
            print("❌ Database query failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Check your PostgreSQL server and DATABASE_URL")
        return False

if __name__ == "__main__":
    success = verify_postgresql()
    sys.exit(0 if success else 1)
