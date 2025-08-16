@echo off
set DATABASE_URL=postgresql://postgres:pyAZxwAFXBoorHetiEjHrwMdNxiXsOMH@shuttle.proxy.rlwy.net:48806/railway
echo Testing Railway database connection...
E:/Python/python.exe -c "from database import get_db_manager; dm = get_db_manager(); result = dm.execute_query('SELECT COUNT(*) FROM business_cards', fetch='one'); print(f'Business cards: {result[0]}'); result = dm.execute_query('SELECT COUNT(*) FROM qr_codes', fetch='one'); print(f'QR codes: {result[0]}')"
