#!/usr/bin/env python3
"""
Test script for bulk QR generator
"""

print("Testing bulk QR generator setup...")

try:
    from database import get_db_manager
    print("✅ Database import successful")
    
    db = get_db_manager()
    print(f"✅ Database type: {db.db_type}")
    
    # Test business cards query
    query = '''
        SELECT bc.id, bc.company_name, bc.name, 
               COUNT(qr.id) as existing_qr_count
        FROM business_cards bc
        LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
        GROUP BY bc.id, bc.company_name, bc.name
        ORDER BY bc.created_at DESC
    '''
    
    results = db.execute_query(query, fetch='all')
    print(f"✅ Found {len(results)} business cards")
    
    for i, row in enumerate(results[:3], 1):  # Show first 3
        if isinstance(row, (list, tuple)):
            card_id, company_name, name, qr_count = row
        else:
            card_id = row['id']
            company_name = row['company_name']
            name = row['name']
            qr_count = row['existing_qr_count']
        
        name_display = f" ({name})" if name else ""
        print(f"  {i}. {company_name}{name_display} - {qr_count:,} QR codes")
    
    print("✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
