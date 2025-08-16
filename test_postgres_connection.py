#!/usr/bin/env python3
"""
Test PostgreSQL connection and setup local database
Run this after installing PostgreSQL to verify everything works
"""

import os
import sys

def check_postgresql_installation():
    """Check if PostgreSQL is installed and provide installation guidance"""
    
    print("PostgreSQL Installation Check")
    print("=" * 50)
    
    # Check for PostgreSQL executables
    postgres_paths = [
        r"E:\PostgreSQL\16\bin\psql.exe"
    ]
    
    psql_found = None
    for path in postgres_paths:
        if os.path.exists(path):
            psql_found = path
            break
    
    if psql_found:
        print(f"✅ PostgreSQL found at: {psql_found}")
        return True
    else:
        print("❌ PostgreSQL not found")
        print("\n📥 POSTGRESQL INSTALLATION REQUIRED")
        print("=" * 50)
        print("Please install PostgreSQL for Windows:")
        print("1. Go to: https://www.postgresql.org/download/windows/")
        print("2. Download the PostgreSQL 16.x installer")
        print("3. Run as Administrator")
        print("4. During installation:")
        print("   - Set a password for 'postgres' user (REMEMBER THIS!)")
        print("   - Keep default port 5432")
        print("   - Install all components (Server, pgAdmin, Command Line Tools)")
        print("5. After installation, restart this script")
        print("\nOr use the quick installer links:")
        print("- Windows x64: https://get.enterprisedb.com/postgresql/postgresql-16.1-1-windows-x64.exe")
        print("- Windows x32: https://get.enterprisedb.com/postgresql/postgresql-16.1-1-windows.exe")
        
        return False

try:
    import psycopg2
    from psycopg2 import sql
    from database import get_db_manager
    PSYCOPG2_AVAILABLE = True
except ImportError as e:
    print(f"❌ psycopg2 not available: {e}")
    PSYCOPG2_AVAILABLE = False

def test_postgres_connection():
    """Test PostgreSQL connection with common configurations"""
    
    print("Testing PostgreSQL Connection...")
    print("=" * 50)
    
    # Common PostgreSQL configurations for local development
    test_configs = [
        {
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'dbname': 'postgres'  # Default database
        },
        {
            'host': '127.0.0.1',
            'port': 5432,
            'user': 'postgres',
            'dbname': 'postgres'
        }
    ]
    
    # Get password from user
    password = input("Enter PostgreSQL password for 'postgres' user: ")
    
    successful_config = None
    
    for i, config in enumerate(test_configs, 1):
        print(f"\nTest {i}: Trying {config['host']}:{config['port']}")
        
        try:
            # Test connection
            conn = psycopg2.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=password,
                dbname=config['dbname']
            )
            
            # Test query
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            
            print(f"✅ SUCCESS! Connected to PostgreSQL")
            print(f"   Version: {version}")
            
            cursor.close()
            conn.close()
            
            successful_config = {**config, 'password': password}
            break
            
        except psycopg2.OperationalError as e:
            print(f"❌ Connection failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    if successful_config:
        print(f"\n🎉 PostgreSQL is working!")
        return successful_config
    else:
        print(f"\n❌ Could not connect to PostgreSQL")
        print("Make sure:")
        print("1. PostgreSQL is installed and running")
        print("2. Password is correct")
        print("3. PostgreSQL service is started")
        return None

def create_local_database(config):
    """Create a local database for QR project"""
    
    print(f"\nCreating local database...")
    print("=" * 50)
    
    db_name = 'qrproject_local'
    
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            dbname='postgres'
        )
        
        # Enable autocommit for database creation
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        
        if cursor.fetchone():
            print(f"✅ Database '{db_name}' already exists")
        else:
            # Create database
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(db_name)
                )
            )
            print(f"✅ Created database '{db_name}'")
        
        cursor.close()
        conn.close()
        
        # Test connection to new database
        test_conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            dbname=db_name
        )
        test_conn.close()
        
        print(f"✅ Successfully connected to '{db_name}'")
        
        # Import URL encoding for environment file
        from urllib.parse import quote_plus
        encoded_password = quote_plus(config['password'])
        
        # Create environment file for local development
        env_content = f"""# Local PostgreSQL Configuration
# Add these to your environment or .env file
DATABASE_URL=postgresql://{config['user']}:{encoded_password}@{config['host']}:{config['port']}/{db_name}
PGHOST={config['host']}
PGPORT={config['port']}
PGUSER={config['user']}
PGPASSWORD={config['password']}
PGDATABASE={db_name}

# Windows Command Prompt usage:
# set DATABASE_URL=postgresql://{config['user']}:{encoded_password}@{config['host']}:{config['port']}/{db_name}

# Windows PowerShell usage:
# $env:DATABASE_URL="postgresql://{config['user']}:{encoded_password}@{config['host']}:{config['port']}/{db_name}"
"""
        
        with open('local_postgres.env', 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created 'local_postgres.env' with connection details")
        
        return {**config, 'dbname': db_name}
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return None

def test_database_manager(config):
    """Test our database manager with PostgreSQL"""
    
    print(f"\nTesting Database Manager...")
    print("=" * 50)
    
    try:
        # Import URL encoding to handle special characters in password
        from urllib.parse import quote_plus
        
        # URL-encode the password to handle special characters
        encoded_password = quote_plus(config['password'])
        
        # Set environment variables for PostgreSQL with properly encoded URL
        database_url = f"postgresql://{config['user']}:{encoded_password}@{config['host']}:{config['port']}/{config['dbname']}"
        os.environ['DATABASE_URL'] = database_url
        
        print(f"✅ Using DATABASE_URL: postgresql://{config['user']}:***@{config['host']}:{config['port']}/{config['dbname']}")
        
        # Test database manager
        db_manager = get_db_manager()
        
        print(f"✅ Database Manager Type: {db_manager.db_type}")
        
        # Test connection
        result = db_manager.execute_query('SELECT version()', fetch='one')
        
        # Handle different result formats (PostgreSQL returns dict-like, SQLite returns tuple-like)
        if hasattr(result, 'keys'):  # Dict-like (PostgreSQL)
            version = result['version']
        elif isinstance(result, (list, tuple)):  # Tuple-like (SQLite)
            version = result[0]
        else:
            version = str(result)
            
        print(f"✅ Database Version: {version[:50]}...")
        
        # Initialize tables
        db_manager.init_tables()
        print(f"✅ Tables initialized successfully")
        
        # Test insert - use proper UUID for PostgreSQL compatibility
        import uuid
        test_card_id = str(uuid.uuid4())  # Generate a proper UUID
        
        db_manager.execute_query(
            'INSERT INTO business_cards (id, name, company_name, phone) VALUES (%s, %s, %s, %s)',
            (test_card_id, 'Test User', 'Test Company', '123-456-7890')
        )
        print(f"✅ Test insert successful (ID: {test_card_id[:8]}...)")
        
        # Test select
        result = db_manager.execute_query(
            'SELECT name, company_name FROM business_cards WHERE id = %s',
            (test_card_id,),
            fetch='one'
        )
        
        # Handle different result formats
        if hasattr(result, 'keys'):  # Dict-like (PostgreSQL)
            test_result = f"{result['name']} - {result['company_name']}"
        elif isinstance(result, (list, tuple)):  # Tuple-like (SQLite)
            test_result = f"{result[0]} - {result[1]}"
        else:
            test_result = str(result)
            
        print(f"✅ Test select successful: {test_result}")
        
        # Clean up test data
        db_manager.execute_query(
            'DELETE FROM business_cards WHERE id = %s',
            (test_card_id,)
        )
        print(f"✅ Test cleanup successful")
        
        print(f"\n🎉 Database Manager is working with PostgreSQL!")
        return True
        
    except Exception as e:
        print(f"❌ Database Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    print("QR Project - PostgreSQL Setup Test")
    print("=" * 60)
    
    # Step 0: Check if PostgreSQL is installed
    if not check_postgresql_installation():
        print("\n❌ Please install PostgreSQL first and try again")
        input("Press Enter to exit...")
        return
    
    # Step 1: Check if psycopg2 is available
    if not PSYCOPG2_AVAILABLE:
        print("\n❌ psycopg2 not available. Installing...")
        try:
            import subprocess
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ psycopg2-binary installed successfully")
                print("Please restart this script to continue")
            else:
                print(f"❌ Failed to install psycopg2-binary: {result.stderr}")
        except Exception as e:
            print(f"❌ Installation failed: {e}")
        input("Press Enter to exit...")
        return
    
    # Test 2: Basic PostgreSQL connection
    config = test_postgres_connection()
    if not config:
        print("\n❌ Please check PostgreSQL installation and try again")
        input("Press Enter to exit...")
        return
    
    # Test 3: Create local database
    config = create_local_database(config)
    if not config:
        print("\n❌ Database creation failed")
        input("Press Enter to exit...")
        return
    
    # Test 4: Test database manager
    success = test_database_manager(config)
    if not success:
        print("\n❌ Database manager test failed")
        input("Press Enter to exit...")
        return
    
    print(f"\n🎉 PostgreSQL Setup Complete!")
    print(f"Next steps:")
    print(f"1. Source the environment: set DATABASE_URL=postgresql://...")
    print(f"2. Run: python main.py")
    print(f"3. Access: http://localhost:5000")
    input("Press Enter to exit...")

if __name__ == '__main__':
    main()
