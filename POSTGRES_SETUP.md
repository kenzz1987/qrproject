# PostgreSQL Setup Guide for QR Project

## Step 1: Install PostgreSQL for Windows

### Option A: Official Installer (Recommended)
1. Download from: https://www.postgresql.org/download/windows/
2. Choose PostgreSQL 16.x (latest stable)
3. Run installer as Administrator
4. **Important settings:**
   - Installation Directory: `C:\Program Files\PostgreSQL\16` (default)
   - **Password**: Set a strong password for `postgres` user (REMEMBER THIS!)
   - Port: `5432` (default)
   - **Components to install:**
     - ✅ PostgreSQL Server
     - ✅ pgAdmin 4
     - ✅ Stack Builder
     - ✅ Command Line Tools

### Option B: Chocolatey (if you have it)
```cmd
choco install postgresql
```

## Step 2: Verify Installation

After installation, open a new Command Prompt and test:

```cmd
psql --version
```

You should see something like: `psql (PostgreSQL) 16.1`

## Step 3: Start PostgreSQL Service

PostgreSQL should start automatically, but you can verify:

```cmd
# Check service status
sc query postgresql-x64-16

# Start service if needed
net start postgresql-x64-16
```

## Step 4: Test Database Connection

Run our test script:

```cmd
python test_postgres_connection.py
```

This will:
- Test PostgreSQL connection
- Create a local `qrproject_local` database
- Generate environment configuration
- Test our database manager

## Step 5: Configure Environment

After running the test script, you'll get a `local_postgres.env` file with:

```bash
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/qrproject_local
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=yourpassword
PGDATABASE=qrproject_local
```

## Step 6: Run the Application

```cmd
# Set environment variable (Windows CMD)
set DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/qrproject_local

# Or (Windows PowerShell)
$env:DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/qrproject_local"

# Run the application
python main.py
```

## Troubleshooting

### PostgreSQL not starting
- Check Windows Services: Look for "postgresql-x64-16"
- Restart the service: `net stop postgresql-x64-16` then `net start postgresql-x64-16`

### Connection refused
- Verify PostgreSQL is running
- Check firewall settings
- Verify port 5432 is not blocked

### Password authentication failed
- Double-check the password you set during installation
- Use pgAdmin to test connection first

### psycopg2 import errors
- Make sure you have `psycopg2-binary` installed: `pip install psycopg2-binary`

## VS Code PostgreSQL Extension

Your existing extension should work once PostgreSQL is installed:
- `cweijan.vscode-postgresql-client2` - Already installed ✅

To connect in VS Code:
1. Open Command Palette (Ctrl+Shift+P)
2. Search "PostgreSQL: Add Connection"
3. Enter connection details:
   - Host: localhost
   - Port: 5432
   - Username: postgres
   - Password: (your password)
   - Database: qrproject_local

## Next Steps

Once PostgreSQL is working locally:
1. Test bulk QR generation with PostgreSQL
2. Compare performance vs SQLite
3. Deploy to Railway with PostgreSQL backend
