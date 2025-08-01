#!/usr/bin/env python3
"""
Test script to verify QR code generation functionality
"""

import qrcode
from PIL import Image
import io

def test_qr_generation():
    """Test basic QR code generation"""
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data("https://example.com/test")
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        
        print("✅ QR code generation test passed!")
        print(f"   Image size: {img.size}")
        print(f"   Image mode: {img.mode}")
        
        return True
    except Exception as e:
        print(f"❌ QR code generation test failed: {e}")
        return False

def test_database():
    """Test SQLite database setup"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(':memory:')  # Use in-memory database for test
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qr_codes (
                id TEXT PRIMARY KEY,
                code_data TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scanned_at TIMESTAMP NULL,
                is_expired BOOLEAN DEFAULT FALSE,
                metadata TEXT
            )
        ''')
        
        # Test insert
        cursor.execute(
            'INSERT INTO qr_codes (id, code_data) VALUES (?, ?)',
            ('test-123', 'https://example.com/scan/test-123')
        )
        
        # Test select
        cursor.execute('SELECT * FROM qr_codes WHERE id = ?', ('test-123',))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            print("✅ Database test passed!")
            print(f"   Record found: {result[0]}")
            return True
        else:
            print("❌ Database test failed: No record found")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running QR Project Tests...")
    print("=" * 40)
    
    qr_test = test_qr_generation()
    db_test = test_database()
    
    print("=" * 40)
    if qr_test and db_test:
        print("🎉 All tests passed! The application should work correctly.")
    else:
        print("⚠️  Some tests failed. Please check the dependencies.")
