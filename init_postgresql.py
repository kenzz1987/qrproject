#!/usr/bin/env python3
"""
PostgreSQL migration and initialization script for Railway
"""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize PostgreSQL database"""
    try:
        logger.info("Starting PostgreSQL database initialization...")
        
        # Get database manager
        db_manager = get_db_manager()
        logger.info(f"Database type: {db_manager.db_type}")
        
        logger.info("Creating PostgreSQL tables and indexes...")
        
        # Initialize tables
        db_manager.init_tables()
        
        # Test connection
        result = db_manager.execute_query('SELECT 1', fetch='one')
        logger.info(f"Database test successful: {result}")
        
        logger.info("PostgreSQL database initialization completed successfully!")
        
        # Print environment info for debugging
        logger.info("Environment variables:")
        for key in ['DATABASE_URL', 'PGHOST', 'PGDATABASE', 'PGUSER', 'RAILWAY_ENVIRONMENT']:
            value = os.environ.get(key, 'NOT_SET')
            if key in ['PGPASSWORD', 'DATABASE_URL'] and value != 'NOT_SET':
                value = f"{value[:10]}***HIDDEN***"
            logger.info(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
