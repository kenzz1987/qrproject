# Railway Database Protection Setup Guide

This guide explains how to protect your database from being wiped during Railway deployments.

## Automatic Setup (Recommended)

The application is now configured to automatically use persistent volumes. When you deploy:

1. Railway will create a persistent volume at `/data`
2. The application will automatically migrate your existing database to `/app/data/qr_codes.db`
3. All future deployments will preserve your data

## Manual Railway Console Setup

If you need to manually configure the persistent volume in Railway's dashboard:

### Step 1: Add Persistent Volume
1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Variables" tab
4. Add environment variable:
   - Name: `DATABASE_PATH`
   - Value: `/app/data/qr_codes.db`

### Step 2: Configure Volume Mount
1. In your service settings, go to "Volumes"
2. Click "Add Volume"
3. Mount Path: `/app/data`
4. Size: 1GB (or more if needed)

### Step 3: Deploy
The application will automatically handle the database migration on the next deployment.

## Before Deploying

### Option 1: Backup Current Data (Recommended)
Before deploying these changes, create a backup of your current database:

1. Go to Railway dashboard
2. Open your service's shell/terminal
3. Run: `python backup_db.py`
4. Download the backup file if needed

### Option 2: Export Current Data
If you want to manually export your data:

```python
# Connect to current database and export data
import sqlite3
import json

conn = sqlite3.connect('qr_codes.db')
cursor = conn.cursor()

# Export business cards
cursor.execute('SELECT * FROM business_cards')
cards_data = cursor.fetchall()

# Export QR codes  
cursor.execute('SELECT * FROM qr_codes')
qr_data = cursor.fetchall()

# Save to JSON for backup
with open('backup_data.json', 'w') as f:
    json.dump({
        'business_cards': cards_data,
        'qr_codes': qr_data
    }, f)
```

## Verification

After deployment, verify your data is preserved:

1. Check the `/health` endpoint - it will show the database path
2. Log into admin panel and verify your business cards are still there
3. Test scanning existing QR codes

## Troubleshooting

### If Data is Missing
1. Check Railway logs for migration messages
2. Verify the volume is properly mounted
3. Check if backup files exist in `/app/data/backups`

### If Migration Fails
1. The old database file should still exist
2. You can manually copy it using Railway's shell
3. Contact support with the error logs

## Database Backup Strategy

The application now includes automatic backup functionality:
- Backups are created in `/app/data/backups`
- Old backups are automatically cleaned up (keeps last 5)
- Backups are compressed to save space

To create manual backup:
```bash
python backup_db.py
```

## Important Notes

1. **Volume Persistence**: Railway volumes persist across deployments and restarts
2. **Data Safety**: Your data will only be lost if you explicitly delete the volume
3. **Backup Regularly**: Set up automated backups for production use
4. **Monitor Space**: Check volume usage periodically

## Production Recommendations

1. **Automated Backups**: Schedule regular backups
2. **External Backups**: Store critical backups outside Railway
3. **Monitoring**: Set up alerts for database issues
4. **Testing**: Test disaster recovery procedures
