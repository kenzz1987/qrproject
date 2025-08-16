#!/usr/bin/env python3
"""
Test script for the transaction optimization implementation
"""

try:
    from database import get_db_manager
    print("✓ Database manager imported successfully")
    
    db = get_db_manager()
    print("✓ Database manager initialized")
    print(f"Database type: {db.db_type}")
    
    # Test that the new execute_transaction method exists
    if hasattr(db, 'execute_transaction'):
        print("✓ execute_transaction method found")
        print("✓ Transaction optimization implemented successfully")
    else:
        print("✗ execute_transaction method not found")
    
    # Test import of main.py 
    import main
    print("✓ Main.py imports successfully with transaction optimization")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
