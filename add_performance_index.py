#!/usr/bin/env python3
"""
Database Performance Migration
Adds compound index for QR code scanning optimization
"""

import os
import sys
from database import get_db_manager

def add_performance_index():
    """Add compound index for QR code scanning performance"""
    db_manager = get_db_manager()
    
    # New performance index
    index_query = '''
        CREATE INDEX IF NOT EXISTS idx_qr_codes_scan_lookup 
        ON qr_codes(id, business_card_id, is_expired)
    '''
    
    try:
        print("Adding QR code scanning performance index...")
        db_manager.execute_query(index_query)
        print("✅ Performance index added successfully!")
        
        # Verify index was created
        verify_query = '''
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'qr_codes' 
            AND indexname = 'idx_qr_codes_scan_lookup'
        '''
        
        result = db_manager.execute_query(verify_query, fetch='one')
        if result:
            print(f"✅ Index verified: {result[0]}")
        else:
            print("⚠️ Index creation may have failed")
            
    except Exception as e:
        print(f"❌ Error adding performance index: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("=== QR Code Performance Migration ===")
    print("This will add a compound index to optimize QR code scanning...")
    
    # Check if DATABASE_URL is set
    if not os.environ.get('DATABASE_URL'):
        print("⚠️ DATABASE_URL not set. Please set it before running migration.")
        print("Example: set DATABASE_URL=postgresql://...")
        sys.exit(1)
    
    add_performance_index()
    print("🚀 Migration completed! QR code scanning should now be faster.")
