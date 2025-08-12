#!/usr/bin/env python3
"""
QR Code Generation Web Application
A Flask web app for batch QR code generation and download
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import uuid
import os
import sqlite3
from datetime import datetime
import tempfile
import shutil
import hashlib
import secrets
import random
import string

# Database setup
def get_db_path():
    """Get database path - use persistent volume on Railway"""
    # Check if we're running on Railway (persistent volume)
    railway_data_path = os.environ.get('DATABASE_PATH', '/app/data/qr_codes.db')
    if os.path.exists('/app/data'):
        # Ensure the data directory exists
        os.makedirs('/app/data', exist_ok=True)
        return railway_data_path
    else:
        # Local development
        return 'qr_codes.db'

def init_db():
    """Initialize SQLite database"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # QR codes table
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
    
    # Business cards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS business_cards (
            id TEXT PRIMARY KEY,
            name TEXT,
            company_name TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scan_count INTEGER DEFAULT 0
        )
    ''')
    
    # Check if we need to migrate existing table structure
    cursor.execute("PRAGMA table_info(business_cards)")
    columns_info = cursor.fetchall()
    
    # Check if name and phone columns are still NOT NULL
    name_is_not_null = any(col[1] == 'name' and col[3] == 1 for col in columns_info)
    phone_is_not_null = any(col[1] == 'phone' and col[3] == 1 for col in columns_info)
    
    if name_is_not_null or phone_is_not_null:
        # Need to recreate table to allow NULL values for name and phone
        cursor.execute('BEGIN TRANSACTION')
        
        # Create new table with correct schema
        cursor.execute('''
            CREATE TABLE business_cards_new (
                id TEXT PRIMARY KEY,
                name TEXT,
                company_name TEXT NOT NULL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_count INTEGER DEFAULT 0
            )
        ''')
        
        # Copy data from old table to new table
        cursor.execute('''
            INSERT INTO business_cards_new (id, name, company_name, phone, created_at, scan_count)
            SELECT id, name, company_name, phone, created_at, scan_count
            FROM business_cards
        ''')
        
        # Drop old table and rename new table
        cursor.execute('DROP TABLE business_cards')
        cursor.execute('ALTER TABLE business_cards_new RENAME TO business_cards')
        
        cursor.execute('COMMIT')
    
    # Check if business_card_id column exists in qr_codes table
    cursor.execute("PRAGMA table_info(qr_codes)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'business_card_id' not in columns:
        # Add the business_card_id column if it doesn't exist
        cursor.execute('ALTER TABLE qr_codes ADD COLUMN business_card_id TEXT NULL')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_qr_codes_business_card_id ON qr_codes(business_card_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_qr_codes_expired ON qr_codes(is_expired)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_qr_codes_lookup ON qr_codes(id, business_card_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_business_cards_company ON business_cards(company_name COLLATE NOCASE)')
    
    conn.commit()
    conn.close()

# User class for authentication
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "feda659b4f3c925a95d992466d2b0c39a5533890287d9540efdd2999a011cbde5ed1f7cdd36357456fc8cb59d7ecd45eb88007be03449841ce4c9ab75315f1cc"  # SHA-512 hash of admin password

def verify_password(password):
    """Verify password against stored hash"""
    return hashlib.sha512(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses halaman admin.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return User(user_id)
    return None

# Initialize database when the module is imported
init_db()

def generate_qr_code(data, size=(300, 300)):
    """Generate QR code as PIL Image with fixed text size and scaled QR code"""
    # Fixed text sizes for consistency
    BOTTOM_TEXT_SIZE = 50  # Fixed size for "ptm.id/" text
    VERTICAL_TEXT_SIZE = 46  # Fixed size for vertical code
    
    # Fixed spacing (reverted to original values)
    TEXT_HEIGHT = 65  # Fixed height for bottom text area
    CODE_WIDTH = 60   # Fixed width for vertical text area
    
    # Generate unique 5-character code starting with "tg"
    def generate_unique_code():
        # Start with "tg"
        code = "tg"
        # Add 3 random characters (mix of upper and lower case)
        chars = string.ascii_letters  # a-z, A-Z
        for _ in range(3):
            code += random.choice(chars)
        return code
    
    unique_code = generate_unique_code()
    
    # Load fonts with fixed sizes
    try:
        # Try to use bold Arial with fixed sizes
        bottom_font = ImageFont.truetype("arialbd.ttf", BOTTOM_TEXT_SIZE)
        vertical_font = ImageFont.truetype("arialbd.ttf", VERTICAL_TEXT_SIZE)
    except:
        try:
            # Fallback to regular Arial
            bottom_font = ImageFont.truetype("arial.ttf", BOTTOM_TEXT_SIZE)
            vertical_font = ImageFont.truetype("arial.ttf", VERTICAL_TEXT_SIZE)
        except:
            # Final fallback to default font
            bottom_font = ImageFont.load_default()
            vertical_font = ImageFont.load_default()
    
    # Create temporary image to measure text dimensions
    temp_img = Image.new('RGB', (400, 100), 'white')
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Measure bottom text dimensions
    bottom_text = "ptm.id/"
    bottom_bbox = temp_draw.textbbox((0, 0), bottom_text, font=bottom_font)
    bottom_text_width = bottom_bbox[2] - bottom_bbox[0]
    
    # Measure vertical text dimensions (before rotation)
    vertical_bbox = temp_draw.textbbox((0, 0), unique_code, font=vertical_font)
    vertical_text_width = vertical_bbox[2] - vertical_bbox[0]
    vertical_text_height = vertical_bbox[3] - vertical_bbox[1]
    
    # Calculate required QR code size to accommodate the text
    # The QR code should be wide enough for the bottom text and tall enough for the vertical text
    min_qr_width = max(bottom_text_width + 10, size[0] - CODE_WIDTH)  # 10px padding
    min_qr_height = max(vertical_text_width + 10, size[1] - TEXT_HEIGHT)  # vertical_text_width becomes height after rotation
    
    # Use the larger dimension to keep QR code square
    qr_size = max(min_qr_width, min_qr_height, 200)  # Minimum 200px
    
    # Generate QR code with calculated size
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Generate the QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    # Create final image with calculated dimensions
    final_width = qr_size + CODE_WIDTH
    final_height = qr_size + TEXT_HEIGHT
    final_img = Image.new('RGB', (final_width, final_height), 'white')
    
    # Paste the QR code at the top-left
    final_img.paste(qr_img, (0, 0))
    
    # Add bottom text
    draw = ImageDraw.Draw(final_img)
    
    # Center the bottom text under the QR code (moved much closer to QR code)
    text_x = (qr_size - bottom_text_width) // 2
    text_y = qr_size - 25  # Moved 25px closer to QR code (overlapping more)
    
    # Draw the bottom text
    draw.text((text_x, text_y), bottom_text, fill="black", font=bottom_font)
    
    # Create vertical text for the 5-character code
    # Create a temporary image for the vertical text with extra padding for descenders
    temp_vertical_img = Image.new('RGB', (vertical_text_width + 20, vertical_text_height + 20), 'white')
    temp_vertical_draw = ImageDraw.Draw(temp_vertical_img)
    temp_vertical_draw.text((10, 10), unique_code, fill="black", font=vertical_font)
    
    # Rotate the text 90 degrees counterclockwise
    rotated_text = temp_vertical_img.rotate(90, expand=True)
    
    # Position the vertical text closer to QR code horizontally, centered vertically
    # Reduce left padding by 15px to bring it closer to QR code (optimal balance)
    vertical_x = qr_size - 15  # Moved 15px closer to QR edge (was -25px, now -15px)
    vertical_y = (qr_size - rotated_text.height) // 2  # Center vertically relative to QR code
    
    # Paste the rotated text onto the final image
    final_img.paste(rotated_text, (vertical_x, vertical_y))
    
    return final_img

@app.route('/')
@login_required
def index():
    """Main page - Business cards management (protected)"""
    return render_template('business_cards.html')

@app.route('/admin')
@login_required
def admin():
    """Admin page redirect"""
    return redirect(url_for('index'))

@app.route('/business-cards')
@login_required
def business_cards():
    """Business cards management page (redirect to main)"""
    return redirect('/')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'db_path': db_path,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username == ADMIN_USERNAME and verify_password(password):
            user = User("admin")
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Username atau password salah', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Admin logout"""
    logout_user()
    flash('Anda telah logout', 'info')
    return redirect(url_for('business_card_public'))

@app.route('/public')
def business_card_public():
    """Public page - shows message that this is for QR code access only"""
    return render_template('public.html')

@app.route('/api/business-cards', methods=['GET'])
@login_required
def get_business_cards():
    """Get all business cards with optional search"""
    try:
        search_query = request.args.get('search', '').strip()
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if search_query:
            # Search by company name (case-insensitive)
            cursor.execute('''
                SELECT bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count,
                       COUNT(qr.id) as qr_count
                FROM business_cards bc
                LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
                WHERE LOWER(bc.company_name) LIKE LOWER(?)
                GROUP BY bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count
                ORDER BY bc.created_at DESC
            ''', (f'%{search_query}%',))
        else:
            # Get all business cards
            cursor.execute('''
                SELECT bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count,
                       COUNT(qr.id) as qr_count
                FROM business_cards bc
                LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
                GROUP BY bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count
                ORDER BY bc.created_at DESC
            ''')
        
        cards = []
        for row in cursor.fetchall():
            cards.append({
                'id': row[0],
                'name': row[1],
                'company_name': row[2],
                'phone': row[3],
                'created_at': row[4],
                'scan_count': row[5],
                'qr_count': row[6]
            })
        
        conn.close()
        return jsonify({'success': True, 'cards': cards})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business-cards', methods=['POST'])
@login_required
def create_business_card():
    """Create a new business card"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        company_name = data.get('company_name', '').strip()
        phone = data.get('phone', '').strip()
        
        if not company_name:
            return jsonify({'error': 'Nama perusahaan wajib diisi'}), 400
        
        # Set default values for optional fields
        if not name:
            name = ''
        if not phone:
            phone = ''
        
        card_id = str(uuid.uuid4())
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO business_cards (id, name, company_name, phone) VALUES (?, ?, ?, ?)',
            (card_id, name, company_name, phone)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'card': {
                'id': card_id,
                'name': name,
                'company_name': company_name,
                'phone': phone
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business-cards/<card_id>', methods=['DELETE'])
@login_required
def delete_business_card(card_id):
    """Delete a business card and all its QR codes"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if business card exists
        cursor.execute('SELECT name FROM business_cards WHERE id = ?', (card_id,))
        card = cursor.fetchone()
        
        if not card:
            return jsonify({'error': 'Kartu nama tidak ditemukan'}), 404
        
        # Delete all QR codes associated with this business card
        cursor.execute('DELETE FROM qr_codes WHERE business_card_id = ?', (card_id,))
        deleted_qr_count = cursor.rowcount
        
        # Delete the business card
        cursor.execute('DELETE FROM business_cards WHERE id = ?', (card_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Kartu nama "{card[0]}" dan {deleted_qr_count} QR code berhasil dihapus'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business-cards/<card_id>/generate-qr', methods=['POST'])
@login_required
def generate_business_card_qr(card_id):
    """Generate batch of one-time QR codes for a business card"""
    try:
        data = request.get_json()
        quantity = int(data.get('quantity', 1))
        base_url = request.host_url.rstrip('/')
        
        if quantity < 1 or quantity > 100:
            return jsonify({'error': 'Jumlah harus antara 1 dan 100'}), 400
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if business card exists
        cursor.execute('SELECT id, name FROM business_cards WHERE id = ?', (card_id,))
        card = cursor.fetchone()
        
        if not card:
            return jsonify({'error': 'Kartu nama tidak ditemukan'}), 404
        
        # Generate QR codes
        codes = []
        for _ in range(quantity):
            code_id = str(uuid.uuid4())
            scan_url = f"{base_url}/card/{card_id}?qr={code_id}"
            
            # Store in database with business card reference
            cursor.execute(
                'INSERT INTO qr_codes (id, code_data, business_card_id) VALUES (?, ?, ?)',
                (code_id, scan_url, card_id)
            )
            codes.append({
                'id': code_id,
                'url': scan_url
            })
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'codes': codes,
            'quantity': quantity,
            'card_name': card[1]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-qr/<code_id>')
@login_required
def download_single_qr(code_id):
    """Download single QR code as PNG file"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get QR code info
        cursor.execute(
            'SELECT qr.code_data, bc.name FROM qr_codes qr LEFT JOIN business_cards bc ON qr.business_card_id = bc.id WHERE qr.id = ?',
            (code_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'QR code tidak ditemukan'}), 404
        
        # Generate QR code image
        qr_img = generate_qr_code(result[0])
        
        # Save to bytes
        img_bytes = io.BytesIO()
        qr_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Create filename
        card_name = result[1] or 'QR_Code'
        filename = f"{card_name.replace(' ', '_')}_qr_{code_id[:8]}.png"
        
        conn.close()
        
        return send_file(
            img_bytes,
            as_attachment=True,
            download_name=filename,
            mimetype='image/png'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-batch', methods=['POST'])
@login_required
def download_batch_qr():
    """Download batch of QR codes as ZIP file"""
    try:
        data = request.get_json()
        codes = data.get('codes', [])
        card_name = data.get('card_name', 'QR_Codes')
        
        if not codes:
            return jsonify({'error': 'Tidak ada kode yang diberikan'}), 400
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'qr_codes.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for i, code in enumerate(codes, 1):
                # Generate QR code image
                qr_img = generate_qr_code(code['url'])
                
                # Save to bytes
                img_bytes = io.BytesIO()
                qr_img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Add to ZIP
                filename = f"qr_code_{i:03d}_{code['id'][:8]}.png"
                zip_file.writestr(filename, img_bytes.getvalue())
        
        # Create download filename
        safe_card_name = card_name.replace(' ', '_').replace('/', '_')
        download_filename = f"{safe_card_name}_qr_codes.zip"
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/zip'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/card/<card_id>')
def business_card_landing(card_id):
    """Business card landing page"""
    try:
        qr_id = request.args.get('qr')
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if qr_id:
            # Single optimized query to get both business card and QR code info
            cursor.execute('''
                SELECT bc.name, bc.company_name, bc.phone, bc.scan_count,
                       qr.id, qr.is_expired
                FROM business_cards bc
                LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
                WHERE bc.id = ? AND qr.id = ?
            ''', (card_id, qr_id))
            
            result = cursor.fetchone()
            
            if not result:
                # Fallback: check if business card exists but QR doesn't belong to it
                cursor.execute('SELECT name FROM business_cards WHERE id = ?', (card_id,))
                if cursor.fetchone():
                    conn.close()
                    return render_template('scan_result.html', 
                                         status='error', 
                                         message='QR code tidak valid')
                else:
                    conn.close()
                    return render_template('scan_result.html', 
                                         status='error', 
                                         message='Kartu nama tidak ditemukan')
            
            # Extract data
            name, company_name, phone, scan_count = result[:4]
            qr_exists, is_expired = result[4], result[5]
            
            if is_expired:  # Already used - fast path, no database updates needed
                conn.close()
                return render_template('scan_result.html', 
                                     status='expired', 
                                     message='QR code ini sudah pernah digunakan')
            
            # First-time scan: Mark QR as used and increment scan count in single transaction
            cursor.execute('''
                UPDATE qr_codes 
                SET is_expired = TRUE, scanned_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (qr_id,))
            
            cursor.execute('''
                UPDATE business_cards 
                SET scan_count = scan_count + 1 
                WHERE id = ?
            ''', (card_id,))
            
            conn.commit()
            
            # Use the incremented scan count
            updated_count = scan_count + 1
            
        else:
            # Direct access without QR code - single query
            cursor.execute(
                'SELECT name, company_name, phone, scan_count FROM business_cards WHERE id = ?',
                (card_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return render_template('scan_result.html', 
                                     status='error', 
                                     message='Kartu nama tidak ditemukan')
            
            name, company_name, phone, updated_count = result
        
        conn.close()
        
        card_data = {
            'name': name,
            'company_name': company_name,
            'phone': phone,
            'scan_count': updated_count
        }
        
        return render_template('business_card.html', card=card_data)
    
    except Exception as e:
        return render_template('scan_result.html', 
                             status='error', 
                             message=f'Error memuat kartu nama: {str(e)}')

@app.route('/api/stats')
@login_required
def get_stats():
    """Get business card statistics"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total business cards
        cursor.execute('SELECT COUNT(*) FROM business_cards')
        total_cards = cursor.fetchone()[0]
        
        # Total QR codes generated
        cursor.execute('SELECT COUNT(*) FROM qr_codes WHERE business_card_id IS NOT NULL')
        total_qr_codes = cursor.fetchone()[0]
        
        # Total scans (used QR codes)
        cursor.execute('SELECT COUNT(*) FROM qr_codes WHERE business_card_id IS NOT NULL AND is_expired = TRUE')
        total_scans = cursor.fetchone()[0]
        
        # Unused QR codes
        unused_qr_codes = total_qr_codes - total_scans
        
        conn.close()
        
        return jsonify({
            'total_business_cards': total_cards,
            'total_qr_codes': total_qr_codes,
            'total_scans': total_scans,
            'unused_qr_codes': unused_qr_codes
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
