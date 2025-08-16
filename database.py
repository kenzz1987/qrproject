#!/usr/bin/env python3
"""
Database configuration and connection management
PostgreSQL only - optimized for production deployment
"""

import os
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import psycopg2 - required for operation
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    raise ImportError("psycopg2 is required for database operations. Install with: pip install psycopg2-binary")

class DatabaseManager:
    def __init__(self):
        self.db_type = 'postgresql'
        self.connection_params = self._get_connection_params()
        logger.info(f"Database type: {self.db_type}")
        
    def _get_connection_params(self):
        """Get PostgreSQL connection parameters"""
        # Railway PostgreSQL connection
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            return {'database_url': database_url}
        else:
            # Manual connection parameters
            return {
                'host': os.environ.get('PGHOST', 'localhost'),
                'port': int(os.environ.get('PGPORT', 5432)),
                'database': os.environ.get('PGDATABASE', 'railway'),
                'user': os.environ.get('PGUSER', 'postgres'),
                'password': os.environ.get('PGPASSWORD', ''),
            }
    
    @contextmanager
    def get_connection(self):
        """Get PostgreSQL database connection with automatic cleanup"""
        conn = None
        try:
            if 'database_url' in self.connection_params:
                conn = psycopg2.connect(
                    self.connection_params['database_url'],
                    cursor_factory=RealDictCursor
                )
            else:
                conn = psycopg2.connect(
                    **self.connection_params,
                    cursor_factory=RealDictCursor
                )
            conn.autocommit = False
                
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a single query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if fetch:
                if fetch == 'one':
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
                return result
            else:
                conn.commit()
                return cursor.rowcount
    
    def execute_many(self, query, params_list):
        """Execute query with multiple parameter sets"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
    
    def execute_transaction(self, queries_with_params):
        """Execute multiple queries in a single transaction
        
        Args:
            queries_with_params: List of tuples (query, params) to execute atomically
            
        Returns:
            List of results for queries that fetch data, None for others
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            results = []
            
            for query, params in queries_with_params:
                cursor.execute(query, params or ())
                # Check if this is a SELECT query by looking for RETURNING or fetch expectations
                if query.strip().upper().startswith('SELECT') or 'RETURNING' in query.upper():
                    results.append(cursor.fetchall())
                else:
                    results.append(cursor.rowcount)
            
            conn.commit()
            return results
    
    def init_tables(self):
        """Initialize PostgreSQL database tables"""
        logger.info(f"Initializing {self.db_type} database tables...")
        self._init_postgresql_tables()
    
    def _init_postgresql_tables(self):
        """Initialize PostgreSQL tables"""
        queries = [
            # Enable UUID extension
            'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',
            
            # Business cards table
            '''
            CREATE TABLE IF NOT EXISTS business_cards (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name TEXT,
                company_name TEXT NOT NULL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_count INTEGER DEFAULT 0
            )
            ''',
            
            # QR codes table
            '''
            CREATE TABLE IF NOT EXISTS qr_codes (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                code_data TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scanned_at TIMESTAMP NULL,
                is_expired BOOLEAN DEFAULT FALSE,
                metadata JSONB,
                business_card_id UUID REFERENCES business_cards(id) ON DELETE CASCADE
            )
            ''',
            
            # Indexes for performance
            'CREATE INDEX IF NOT EXISTS idx_qr_codes_business_card_id ON qr_codes(business_card_id)',
            'CREATE INDEX IF NOT EXISTS idx_qr_codes_expired ON qr_codes(is_expired)',
            'CREATE INDEX IF NOT EXISTS idx_qr_codes_created_at ON qr_codes(created_at)',
            'CREATE INDEX IF NOT EXISTS idx_business_cards_company ON business_cards USING gin(to_tsvector(\'english\', company_name))',
            
            # Compound index for QR code scanning optimization
            'CREATE INDEX IF NOT EXISTS idx_qr_codes_scan_lookup ON qr_codes(id, business_card_id, is_expired)',
        ]
        
        for query in queries:
            try:
                self.execute_query(query)
                logger.info(f"Executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Query failed (might be expected): {e}")

# Global database manager instance
db_manager = None

def get_db_manager():
    """Get or create the global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
