#!/usr/bin/env python3
"""
Database migration test script
Tests the database migration functionality
"""

import sqlite3
import os

def test_migration():
    """Test database migration"""
    print("🔧 Testing database migration...")
    
    # Remove existing database for clean test
    if os.path.exists('qr_codes.db'):
        print("   Removing existing database for clean test...")
        os.remove('qr_codes.db')
    
    # Import and run the migration
    from main import init_db
    
    print("   Running database initialization...")
    init_db()
    
    # Check the database structure
    conn = sqlite3.connect('qr_codes.db')
    cursor = conn.cursor()
    
    # Check qr_codes table structure
    cursor.execute("PRAGMA table_info(qr_codes)")
    qr_columns = [column[1] for column in cursor.fetchall()]
    print(f"   QR codes table columns: {qr_columns}")
    
    # Check business_cards table structure
    cursor.execute("PRAGMA table_info(business_cards)")
    bc_columns = [column[1] for column in cursor.fetchall()]
    print(f"   Business cards table columns: {bc_columns}")
    
    # Verify required columns exist
    required_qr_columns = ['id', 'code_data', 'created_at', 'scanned_at', 'is_expired', 'metadata', 'business_card_id']
    required_bc_columns = ['id', 'name', 'company_name', 'phone', 'created_at', 'scan_count']
    
    qr_check = all(col in qr_columns for col in required_qr_columns)
    bc_check = all(col in bc_columns for col in required_bc_columns)
    
    if qr_check and bc_check:
        print("   ✅ Database migration successful!")
        print("   ✅ All required columns are present")
        
        # Test inserting data
        try:
            # Insert a test business card
            cursor.execute(
                'INSERT INTO business_cards (id, name, company_name, phone) VALUES (?, ?, ?, ?)',
                ('test-123', 'John Doe', 'Test Company', '+1234567890')
            )
            
            # Insert a test QR code linked to the business card
            cursor.execute(
                'INSERT INTO qr_codes (id, code_data, business_card_id) VALUES (?, ?, ?)',
                ('qr-123', 'https://example.com/card/test-123', 'test-123')
            )
            
            # Test the JOIN query that was failing
            cursor.execute('''
                SELECT bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count,
                       COUNT(qr.id) as qr_count
                FROM business_cards bc
                LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
                GROUP BY bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count
                ORDER BY bc.created_at DESC
            ''')
            
            result = cursor.fetchone()
            if result:
                print(f"   ✅ JOIN query test successful: {result[1]} has {result[6]} QR codes")
            else:
                print("   ❌ JOIN query returned no results")
                
        except Exception as e:
            print(f"   ❌ Data insertion test failed: {e}")
    else:
        print("   ❌ Database migration failed!")
        print(f"   Missing QR columns: {[col for col in required_qr_columns if col not in qr_columns]}")
        print(f"   Missing BC columns: {[col for col in required_bc_columns if col not in bc_columns]}")
    
    conn.commit()
    conn.close()
    
    print("   Database migration test completed!")

if __name__ == "__main__":
    test_migration()
