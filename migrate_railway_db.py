#!/usr/bin/env python3
"""
Database Migration Script for Railway Deployment
This script helps migrate existing database to persistent volume
"""

import os
import shutil
import sqlite3
from datetime import datetime

def migrate_database():
    """Migrate database to persistent volume if needed"""
    old_db_path = 'qr_codes.db'
    new_db_path = os.environ.get('DATABASE_PATH', '/app/data/qr_codes.db')
    data_dir = os.path.dirname(new_db_path)
    
    print(f"Starting database migration at {datetime.now()}")
    print(f"Target database path: {new_db_path}")
    print(f"Data directory: {data_dir}")
    
    # Ensure data directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"Created data directory: {data_dir}")
    else:
        print(f"Data directory already exists: {data_dir}")
    
    # Check if database already exists at target location
    if os.path.exists(new_db_path):
        print(f"Database already exists at {new_db_path}")
        # Test the existing database
        try:
            conn = sqlite3.connect(new_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM business_cards")
            card_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM qr_codes")
            qr_count = cursor.fetchone()[0]
            conn.close()
            print(f"Existing database has {card_count} business cards and {qr_count} QR codes")
        except Exception as e:
            print(f"Error checking existing database: {e}")
        return
    
    # Check if old database exists and migrate it
    if os.path.exists(old_db_path):
        print(f"Migrating database from {old_db_path} to {new_db_path}")
        
        # Test connection to old database
        try:
            conn = sqlite3.connect(old_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM business_cards")
            card_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM qr_codes")
            qr_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"Found {card_count} business cards and {qr_count} QR codes")
            
            # Copy database file
            shutil.copy2(old_db_path, new_db_path)
            print(f"Database successfully migrated to {new_db_path}")
            
            # Verify migration
            conn = sqlite3.connect(new_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM business_cards")
            new_card_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM qr_codes")
            new_qr_count = cursor.fetchone()[0]
            conn.close()
            
            if card_count == new_card_count and qr_count == new_qr_count:
                print("Migration verification successful!")
                # Optionally remove old database
                # os.remove(old_db_path)
            else:
                print("Migration verification failed!")
                return False
                
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            return False
            
    elif os.path.exists(new_db_path):
        print(f"Database already exists at {new_db_path}")
        
        # Verify database integrity
        try:
            conn = sqlite3.connect(new_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM business_cards")
            card_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM qr_codes")
            qr_count = cursor.fetchone()[0]
            conn.close()
            print(f"Database contains {card_count} business cards and {qr_count} QR codes")
        except Exception as e:
            print(f"Database verification failed: {str(e)}")
            return False
    else:
        print("No existing database found, will create new one")
    
    return True

if __name__ == "__main__":
    migrate_database()
