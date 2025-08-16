#!/usr/bin/env python3
"""
Demo Bulk QR Code Generator
Small scale test version for demonstration
"""

import os
import uuid
from database import get_db_manager

# Set PostgreSQL environment
os.environ['DATABASE_URL'] = 'postgresql://postgres:%40Carissa92@localhost:5432/qrproject_local'

# Production URL - all QR codes will point here
PRODUCTION_URL = "https://web-production-b1d67.up.railway.app"

def demo_bulk_generation():
    """Demo function to test bulk QR generation"""
    print("🎯 Demo Bulk QR Code Generator")
    print("=" * 50)
    
    try:
        # Initialize database manager
        db_manager = get_db_manager()
        print(f"✅ Database type: {db_manager.db_type}")
        
        # Get business cards
        query = '''
            SELECT bc.id, bc.company_name, bc.name, 
                   COUNT(qr.id) as existing_qr_count
            FROM business_cards bc
            LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
            GROUP BY bc.id, bc.company_name, bc.name
            ORDER BY bc.created_at DESC
        '''
        
        results = db_manager.execute_query(query, fetch='all')
        print(f"✅ Found {len(results)} business cards")
        
        if not results:
            print("❌ No business cards found. Create some first!")
            return
        
        # Show available cards
        print("\n📋 Available Business Cards:")
        for i, row in enumerate(results, 1):
            if isinstance(row, (list, tuple)):
                card_id, company_name, name, qr_count = row
            else:
                card_id = row['id']
                company_name = row['company_name']
                name = row['name']
                qr_count = row['existing_qr_count']
            
            name_display = f" ({name})" if name else ""
            print(f"  {i}. {company_name}{name_display}")
            print(f"     ID: {card_id}")
            print(f"     Existing QR codes: {qr_count:,}")
        
        # Demo: Generate 10 QR codes for the first business card
        if results:
            first_card = results[0]
            if isinstance(first_card, (list, tuple)):
                card_id, company_name = first_card[0], first_card[1]
            else:
                card_id = first_card['id']
                company_name = first_card['company_name']
            
            print(f"\n🚀 Demo: Generating 10 QR codes for '{company_name}'")
            
            # Prepare insert query
            if db_manager.db_type == 'postgresql':
                insert_query = 'INSERT INTO qr_codes (id, code_data, business_card_id) VALUES (%s, %s, %s)'
            else:
                insert_query = 'INSERT INTO qr_codes (id, code_data, business_card_id) VALUES (?, ?, ?)'
            
            # Generate 10 QR codes
            batch_data = []
            for i in range(10):
                code_id = str(uuid.uuid4())
                scan_url = f"{PRODUCTION_URL}/card/{card_id}?qr={code_id}"
                batch_data.append((code_id, scan_url, card_id))
            
            # Insert batch
            if hasattr(db_manager, 'execute_many'):
                db_manager.execute_many(insert_query, batch_data)
            else:
                for data in batch_data:
                    db_manager.execute_query(insert_query, data)
            
            print(f"✅ Generated 10 QR codes successfully!")
            print(f"🔗 All codes point to: {PRODUCTION_URL}")
            
            # Show a sample URL
            sample_code = batch_data[0]
            print(f"📱 Sample QR URL: {sample_code[1]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_bulk_generation()
