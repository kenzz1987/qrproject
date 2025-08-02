#!/usr/bin/env python3
"""
QR Code Generation Web Application
A Flask web app for batch QR code generation and download
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect
import qrcode
from PIL import Image
import io
import zipfile
import uuid
import os
import sqlite3
from datetime import datetime
import tempfile
import shutil

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('qr_codes.db')
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
            name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scan_count INTEGER DEFAULT 0
        )
    ''')
    
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

app = Flask(__name__)

# Initialize database when the module is imported
init_db()

def generate_qr_code(data, size=(300, 300)):
    """Generate QR code as PIL Image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize(size, Image.Resampling.LANCZOS)
    return img

@app.route('/')
def index():
    """Main page - Business cards management"""
    return render_template('business_cards.html')

@app.route('/business-cards')
def business_cards():
    """Business cards management page (redirect to main)"""
    return redirect('/')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        conn = sqlite3.connect('qr_codes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/business-cards', methods=['GET'])
def get_business_cards():
    """Get all business cards with optional search"""
    try:
        search_query = request.args.get('search', '').strip()
        
        conn = sqlite3.connect('qr_codes.db')
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
def create_business_card():
    """Create a new business card"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        company_name = data.get('company_name', '').strip()
        phone = data.get('phone', '').strip()
        
        if not name or not company_name or not phone:
            return jsonify({'error': 'Nama, nama perusahaan, dan telepon wajib diisi'}), 400
        
        card_id = str(uuid.uuid4())
        
        conn = sqlite3.connect('qr_codes.db')
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
def delete_business_card(card_id):
    """Delete a business card and all its QR codes"""
    try:
        conn = sqlite3.connect('qr_codes.db')
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
def generate_business_card_qr(card_id):
    """Generate batch of one-time QR codes for a business card"""
    try:
        data = request.get_json()
        quantity = int(data.get('quantity', 1))
        base_url = request.host_url.rstrip('/')
        
        if quantity < 1 or quantity > 100:
            return jsonify({'error': 'Jumlah harus antara 1 dan 100'}), 400
        
        conn = sqlite3.connect('qr_codes.db')
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
def download_single_qr(code_id):
    """Download single QR code as PNG file"""
    try:
        conn = sqlite3.connect('qr_codes.db')
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
        
        conn = sqlite3.connect('qr_codes.db')
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
def get_stats():
    """Get business card statistics"""
    try:
        conn = sqlite3.connect('qr_codes.db')
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
