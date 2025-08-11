#!/usr/bin/env python3
"""
Database Backup Script for Railway Deployment
This script creates backups of the database
"""

import os
import shutil
import sqlite3
from datetime import datetime
import gzip

def create_backup():
    """Create a backup of the current database"""
    db_path = os.environ.get('DATABASE_PATH', '/app/data/qr_codes.db')
    
    if not os.path.exists(db_path):
        print("No database found to backup")
        return False
    
    # Create backup directory
    backup_dir = '/app/data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'qr_codes_backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Compress backup
        compressed_path = backup_path + '.gz'
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed backup
        os.remove(backup_path)
        
        print(f"Database backup created: {compressed_path}")
        
        # Verify backup integrity
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM business_cards")
        card_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM qr_codes")
        qr_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"Backup contains {card_count} business cards and {qr_count} QR codes")
        
        # Clean up old backups (keep last 5)
        cleanup_old_backups(backup_dir)
        
        return True
        
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        return False

def cleanup_old_backups(backup_dir, keep_count=5):
    """Clean up old backup files, keeping only the most recent ones"""
    try:
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db.gz')]
        backup_files.sort(reverse=True)
        
        if len(backup_files) > keep_count:
            for old_backup in backup_files[keep_count:]:
                old_path = os.path.join(backup_dir, old_backup)
                os.remove(old_path)
                print(f"Removed old backup: {old_backup}")
                
    except Exception as e:
        print(f"Cleanup failed: {str(e)}")

if __name__ == "__main__":
    create_backup()
