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
from datetime import datetime
import tempfile
import shutil
import hashlib
import secrets
import random
import string
import urllib.request
import logging
from database import get_db_manager

# Configure logging
logger = logging.getLogger(__name__)

def download_fonts():
    """Minimal font setup - no external downloads"""
    # Simple directory creation - no external downloads
    try:
        os.makedirs("fonts", exist_ok=True)
    except:
        pass  # Silent fail if directory creation fails

# Always run this to create the directory structure
download_fonts()

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
db_manager = get_db_manager()
db_manager.init_tables()

def generate_qr_code(data, size=(300, 300)):
    """Generate QR code as PIL Image with bulletproof fallback system"""
    try:
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
        
        # Ultra-robust font loading with comprehensive fallbacks
        bottom_font = None
        vertical_font = None
        
        print(f"Starting font loading process for QR generation...")
        
        # Priority 1: Try downloaded/bundled fonts
        font_paths = [
            # Downloaded fonts (highest priority)
            "fonts/DejaVuSans-Bold.ttf",
            "fonts/DejaVuSans.ttf",
            # Bundled fonts
            "fonts/LiberationSans-Bold.ttf", 
            "fonts/LiberationSans-Regular.ttf",
            # Windows fonts (development)
            "arialbd.ttf",
            "arial.ttf",
            # Linux system fonts
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Regular.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            # macOS fonts
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/ArialBold.ttf"
        ]
        
        # Try each font path
        for i, font_path in enumerate(font_paths):
            try:
                print(f"Attempting font {i+1}/{len(font_paths)}: {font_path}")
                if os.path.exists(font_path):
                    bottom_font = ImageFont.truetype(font_path, BOTTOM_TEXT_SIZE)
                    vertical_font = ImageFont.truetype(font_path, VERTICAL_TEXT_SIZE)
                    print(f"SUCCESS: Loaded TrueType font: {font_path}")
                    break
                else:
                    print(f"Font file not found: {font_path}")
            except Exception as e:
                print(f"Failed to load {font_path}: {e}")
                continue
        
        # Priority 2: Try default font with size (newer PIL)
        if bottom_font is None:
            try:
                print("Trying PIL default font with size parameter...")
                bottom_font = ImageFont.load_default(size=BOTTOM_TEXT_SIZE)
                vertical_font = ImageFont.load_default(size=VERTICAL_TEXT_SIZE)
                print("SUCCESS: Using default font with size parameter")
            except (TypeError, AttributeError) as e:
                print(f"Default font with size failed: {e}")
                bottom_font = None
        
        # Priority 3: Enhanced default font (bitmap scaling approach)
        if bottom_font is None:
            try:
                print("Creating enhanced default font with bitmap scaling...")
                default_font = ImageFont.load_default()
                
                class SafeEnhancedDefaultFont:
                    def __init__(self, base_font, scale_factor=2):
                        self.base_font = base_font
                        self.scale_factor = scale_factor
                    
                    def getsize(self, text):
                        try:
                            return self.base_font.getsize(text)
                        except AttributeError:
                            # Ultra-safe fallback
                            return (len(text) * 8, 16)
                    
                    def getbbox(self, text):
                        try:
                            return self.base_font.getbbox(text)
                        except AttributeError:
                            # Fallback for older PIL versions
                            try:
                                w, h = self.base_font.getsize(text)
                                return (0, 0, w, h)
                            except:
                                # Ultra-safe fallback
                                w, h = len(text) * 8, 16
                                return (0, 0, w, h)
                
                bottom_font = SafeEnhancedDefaultFont(default_font, 2)
                vertical_font = SafeEnhancedDefaultFont(default_font, 2)
                print("SUCCESS: Created enhanced default font")
                
            except Exception as e:
                print(f"Enhanced default font creation failed: {e}")
                # This should never happen, but just in case...
                bottom_font = None
        
        # Priority 4: Last resort - create dummy font object
        if bottom_font is None:
            print("CRITICAL: Creating emergency dummy font...")
            
            class EmergencyFont:
                def getsize(self, text):
                    return (len(text) * 10, 20)
                
                def getbbox(self, text):
                    w, h = len(text) * 10, 20
                    return (0, 0, w, h)
            
            bottom_font = EmergencyFont()
            vertical_font = EmergencyFont()
            print("Emergency font created")
        
        print(f"Final font selection: {type(bottom_font)}")
        
        # Ultra-safe text drawing function
        def safe_draw_text(draw, position, text, font, fill="black"):
            x, y = position
            
            try:
                # Method 1: Enhanced font with bitmap scaling
                if hasattr(font, 'scale_factor') and hasattr(font, 'base_font'):
                    for dx in range(2):
                        for dy in range(2):
                            draw.text((x + dx, y + dy), text, fill=fill, font=font.base_font)
                    return True
            except Exception as e:
                print(f"Enhanced font drawing failed: {e}")
            
            try:
                # Method 2: Regular font
                if hasattr(font, 'base_font'):
                    draw.text(position, text, fill=fill, font=font.base_font)
                else:
                    draw.text(position, text, fill=fill, font=font)
                return True
            except Exception as e:
                print(f"Regular font drawing failed: {e}")
            
            try:
                # Method 3: Default font fallback
                default_font = ImageFont.load_default()
                draw.text(position, text, fill=fill, font=default_font)
                return True
            except Exception as e:
                print(f"Default font fallback failed: {e}")
            
            try:
                # Method 4: No font (PIL handles this)
                draw.text(position, text, fill=fill)
                return True
            except Exception as e:
                print(f"Emergency text drawing failed: {e}")
                return False
        
        # Safe text measurement function
        def safe_measure_text(font, text):
            try:
                if hasattr(font, 'getbbox'):
                    bbox = font.getbbox(text)
                    return bbox[2] - bbox[0], bbox[3] - bbox[1]
            except:
                pass
            
            try:
                if hasattr(font, 'getsize'):
                    return font.getsize(text)
            except:
                pass
            
            # Ultimate fallback
            return (len(text) * 10, 20)
        
        # Measure text dimensions safely
        bottom_text = "ptm.id/"
        bottom_text_width, _ = safe_measure_text(bottom_font, bottom_text)
        
        vertical_text_width, vertical_text_height = safe_measure_text(vertical_font, unique_code)
        
        # Calculate QR code size with safe minimums
        min_qr_width = max(bottom_text_width + 10, size[0] - CODE_WIDTH, 200)
        min_qr_height = max(vertical_text_width + 10, size[1] - TEXT_HEIGHT, 200)
        qr_size = max(min_qr_width, min_qr_height, 250)  # Increased minimum
        
        # Generate QR code with extra error handling
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            
        except Exception as e:
            print(f"QR code generation failed: {e}")
            # Create a simple placeholder image
            qr_img = Image.new('RGB', (qr_size, qr_size), 'white')
            draw_placeholder = ImageDraw.Draw(qr_img)
            draw_placeholder.rectangle([10, 10, qr_size-10, qr_size-10], outline='black', width=3)
            draw_placeholder.text((qr_size//4, qr_size//2), "QR ERROR", fill='black')
        
        # Create final image
        final_width = qr_size + CODE_WIDTH
        final_height = qr_size + TEXT_HEIGHT
        final_img = Image.new('RGB', (final_width, final_height), 'white')
        
        # Paste QR code
        final_img.paste(qr_img, (0, 0))
        
        # Add text with safe drawing
        draw = ImageDraw.Draw(final_img)
        
        # Bottom text positioning
        text_x = max(0, (qr_size - bottom_text_width) // 2)
        text_y = qr_size - 25
        
        success = safe_draw_text(draw, (text_x, text_y), bottom_text, bottom_font, fill="black")
        if not success:
            print("WARNING: Bottom text drawing completely failed")
        
        # Vertical text with safe handling
        try:
            # Create vertical text image
            temp_vertical_img = Image.new('RGB', (vertical_text_width + 20, vertical_text_height + 20), 'white')
            temp_vertical_draw = ImageDraw.Draw(temp_vertical_img)
            
            if safe_draw_text(temp_vertical_draw, (10, 10), unique_code, vertical_font, fill="black"):
                # Rotate and paste
                rotated_text = temp_vertical_img.rotate(90, expand=True)
                vertical_x = qr_size - 25  # Moved 10px to the left from original position
                vertical_y = max(0, (qr_size - rotated_text.height) // 2)
                final_img.paste(rotated_text, (vertical_x, vertical_y))
            else:
                print("WARNING: Vertical text creation failed")
                
        except Exception as e:
            print(f"Vertical text processing failed: {e}")
        
        print("QR code generation completed successfully")
        return final_img
        
    except Exception as e:
        print(f"CRITICAL ERROR in generate_qr_code: {e}")
        # Emergency fallback - create a simple error image
        try:
            emergency_img = Image.new('RGB', (400, 400), 'white')
            emergency_draw = ImageDraw.Draw(emergency_img)
            emergency_draw.rectangle([20, 20, 380, 380], outline='red', width=5)
            emergency_draw.text((50, 180), "QR Generation", fill='black')
            emergency_draw.text((50, 200), "Error Occurred", fill='black')
            return emergency_img
        except:
            # If even this fails, create the most basic image possible
            return Image.new('RGB', (300, 300), 'white')

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
        # Test database connection
        result = db_manager.execute_query('SELECT 1', fetch='one')
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'db_type': db_manager.db_type,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'db_type': db_manager.db_type,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/debug/fonts')
def debug_fonts():
    """Debug endpoint to check available fonts and download status"""
    try:
        import subprocess
        import glob
        
        debug_info = {
            'timestamp': datetime.now().isoformat(),
            'environment': {
                'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
                'app_exists': os.path.exists('/app'),
                'current_dir': os.getcwd(),
                'python_version': os.sys.version
            }
        }
        
        # Check downloaded fonts directory
        fonts_dir = "fonts"
        debug_info['downloaded_fonts'] = {}
        
        if os.path.exists(fonts_dir):
            try:
                font_files = os.listdir(fonts_dir)
                debug_info['downloaded_fonts']['directory_exists'] = True
                debug_info['downloaded_fonts']['files'] = []
                
                for font_file in font_files:
                    font_path = os.path.join(fonts_dir, font_file)
                    file_info = {
                        'name': font_file,
                        'size': os.path.getsize(font_path) if os.path.exists(font_path) else 0,
                        'exists': os.path.exists(font_path)
                    }
                    debug_info['downloaded_fonts']['files'].append(file_info)
                    
            except Exception as e:
                debug_info['downloaded_fonts']['error'] = str(e)
        else:
            debug_info['downloaded_fonts']['directory_exists'] = False
        
        # Test font download manually
        debug_info['font_download_test'] = {}
        try:
            test_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
            import urllib.request
            
            req = urllib.request.Request(test_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content_length = response.headers.get('Content-Length', 'unknown')
                debug_info['font_download_test']['url_accessible'] = True
                debug_info['font_download_test']['content_length'] = content_length
                debug_info['font_download_test']['status_code'] = response.getcode()
                
        except Exception as e:
            debug_info['font_download_test']['url_accessible'] = False
            debug_info['font_download_test']['error'] = str(e)
        
        # Check fc-list output
        try:
            result = subprocess.run(['fc-list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                fonts_list = result.stdout.split('\n')[:20]  # First 20 fonts
                debug_info['fc_list_sample'] = fonts_list
            else:
                debug_info['fc_list_error'] = result.stderr
        except Exception as e:
            debug_info['fc_list_exception'] = str(e)
        
        # Check font directories
        font_dirs = [
            '/usr/share/fonts/truetype/dejavu/',
            '/usr/share/fonts/truetype/liberation/',
            '/usr/share/fonts/truetype/ubuntu/',
            '/usr/share/fonts/TTF/'
        ]
        
        debug_info['system_font_directories'] = {}
        for font_dir in font_dirs:
            try:
                files = glob.glob(f"{font_dir}*.ttf")
                debug_info['system_font_directories'][font_dir] = files[:10]  # First 10 files
            except Exception as e:
                debug_info['system_font_directories'][font_dir] = f"Error: {e}"
        
        # Test font loading with PIL
        debug_info['pil_font_tests'] = {}
        
        # Test 1: Default font
        try:
            from PIL import ImageFont
            default_font = ImageFont.load_default()
            debug_info['pil_font_tests']['default_font'] = "SUCCESS"
        except Exception as e:
            debug_info['pil_font_tests']['default_font'] = f"FAILED: {e}"
        
        # Test 2: Default font with size
        try:
            sized_font = ImageFont.load_default(size=24)
            debug_info['pil_font_tests']['default_font_with_size'] = "SUCCESS"
        except Exception as e:
            debug_info['pil_font_tests']['default_font_with_size'] = f"FAILED: {e}"
        
        # Test 3: Downloaded DejaVu font
        try:
            if os.path.exists("fonts/DejaVuSans.ttf"):
                dejavu_font = ImageFont.truetype("fonts/DejaVuSans.ttf", 24)
                debug_info['pil_font_tests']['downloaded_dejavu'] = "SUCCESS"
            else:
                debug_info['pil_font_tests']['downloaded_dejavu'] = "FILE_NOT_FOUND"
        except Exception as e:
            debug_info['pil_font_tests']['downloaded_dejavu'] = f"FAILED: {e}"
        
        # Test 4: System DejaVu font
        try:
            system_dejavu = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            debug_info['pil_font_tests']['system_dejavu'] = "SUCCESS"
        except Exception as e:
            debug_info['pil_font_tests']['system_dejavu'] = f"FAILED: {e}"
        
        # Test QR generation
        debug_info['qr_generation_test'] = {}
        try:
            # Test the actual QR generation function
            test_qr = generate_qr_code("https://test.com/test")
            debug_info['qr_generation_test']['status'] = "SUCCESS"
            debug_info['qr_generation_test']['image_size'] = test_qr.size
        except Exception as e:
            debug_info['qr_generation_test']['status'] = "FAILED"
            debug_info['qr_generation_test']['error'] = str(e)
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'critical_error': str(e)}), 500

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
        
        if search_query:
            # Search by company name (case-insensitive)
            query = '''
                SELECT bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count,
                       COUNT(qr.id) as qr_count
                FROM business_cards bc
                LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
                WHERE bc.company_name ILIKE %s
                GROUP BY bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count
                ORDER BY bc.created_at DESC
            '''
            params = (f'%{search_query}%',)
        else:
            # Get all business cards
            query = '''
                SELECT bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count,
                       COUNT(qr.id) as qr_count
                FROM business_cards bc
                LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
                GROUP BY bc.id, bc.name, bc.company_name, bc.phone, bc.created_at, bc.scan_count
                ORDER BY bc.created_at DESC
            '''
            params = None
        
        results = db_manager.execute_query(query, params, fetch='all')
        
        cards = []
        for row in results:
            # Handle both dict-like (PostgreSQL) and tuple-like (SQLite) rows
            if hasattr(row, 'keys'):  # Dict-like
                cards.append({
                    'id': str(row['id']),
                    'name': row['name'] or '',
                    'company_name': row['company_name'],
                    'phone': row['phone'] or '',
                    'created_at': str(row['created_at']),
                    'scan_count': row['scan_count'],
                    'qr_count': row['qr_count']
                })
            else:  # Tuple-like
                cards.append({
                    'id': str(row[0]),
                    'name': row[1] or '',
                    'company_name': row[2],
                    'phone': row[3] or '',
                    'created_at': str(row[4]),
                    'scan_count': row[5],
                    'qr_count': row[6]
                })
        
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
        
        # Generate UUID for PostgreSQL
        card_id = str(uuid.uuid4())
        
        # Insert business card
        query = 'INSERT INTO business_cards (id, name, company_name, phone) VALUES (%s, %s, %s, %s)'
        db_manager.execute_query(query, (card_id, name, company_name, phone))
        
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
        # Define queries for PostgreSQL
        check_query = 'SELECT name FROM business_cards WHERE id = %s'
        delete_qr_query = 'DELETE FROM qr_codes WHERE business_card_id = %s'
        delete_card_query = 'DELETE FROM business_cards WHERE id = %s'
        
        # Check if card exists
        result = db_manager.execute_query(check_query, (card_id,), fetch='one')
        
        if not result:
            return jsonify({'error': 'Kartu nama tidak ditemukan'}), 404
        
        # Get card name for response
        card_name = result[0] if isinstance(result, (list, tuple)) else result['name']
        
        # Delete all QR codes associated with this business card
        db_manager.execute_query(delete_qr_query, (card_id,))
        
        # Delete the business card
        db_manager.execute_query(delete_card_query, (card_id,))
        
        return jsonify({
            'success': True,
            'message': f'Kartu nama "{card_name}" dan QR codes berhasil dihapus'
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
        
        # Check if business card exists using database manager
        check_query = 'SELECT id, name FROM business_cards WHERE id = %s'
        insert_query = 'INSERT INTO qr_codes (id, code_data, business_card_id) VALUES (%s, %s, %s)'
        
        result = db_manager.execute_query(check_query, (card_id,), fetch='one')
        
        if not result:
            return jsonify({'error': 'Kartu nama tidak ditemukan'}), 404
        
        # Get card name for response
        card_name = result[1] if isinstance(result, (list, tuple)) else result['name']
        
        # Generate QR codes
        codes = []
        for _ in range(quantity):
            code_id = str(uuid.uuid4())
            scan_url = f"{base_url}/card/{card_id}?qr={code_id}"
            
            # Store in database with business card reference
            db_manager.execute_query(insert_query, (code_id, scan_url, card_id))
            
            codes.append({
                'id': code_id,
                'url': scan_url
            })
        
        return jsonify({
            'success': True,
            'codes': codes,
            'quantity': quantity,
            'card_name': card_name
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-qr/<code_id>')
@login_required
def download_single_qr(code_id):
    """Download single QR code as PNG file"""
    try:
        # Get QR code info using database manager
        query = '''
            SELECT qr.code_data, bc.name 
            FROM qr_codes qr 
            LEFT JOIN business_cards bc ON qr.business_card_id = bc.id 
            WHERE qr.id = %s
        '''
        
        result = db_manager.execute_query(query, (code_id,), fetch='one')
        
        if not result:
            return jsonify({'error': 'QR code tidak ditemukan'}), 404
        
        # Get data from result
        code_data = result[0] if isinstance(result, (list, tuple)) else result['code_data']
        card_name = result[1] if isinstance(result, (list, tuple)) else result['name']
        
        # Generate QR code image
        qr_img = generate_qr_code(code_data)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        qr_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Create filename
        safe_card_name = (card_name or 'QR_Code').replace(' ', '_')
        filename = f"{safe_card_name}_qr_{code_id[:8]}.png"
        
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
        
        if qr_id:
            # Optimized query with INNER JOIN for faster QR code scanning
            query = '''
                SELECT bc.name, bc.company_name, bc.phone, bc.scan_count,
                       qr.id, qr.is_expired
                FROM qr_codes qr
                INNER JOIN business_cards bc ON qr.business_card_id = bc.id
                WHERE qr.id = %s AND qr.business_card_id = %s
            '''
            fallback_query = 'SELECT name FROM business_cards WHERE id = %s'
            update_qr_query = '''
                UPDATE qr_codes 
                SET is_expired = true, scanned_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            '''
            update_card_query = '''
                UPDATE business_cards 
                SET scan_count = scan_count + 1 
                WHERE id = %s
            '''
            
            result = db_manager.execute_query(query, (qr_id, card_id), fetch='one')
            
            if not result:
                # Fallback: check if business card exists but QR doesn't belong to it
                fallback_result = db_manager.execute_query(fallback_query, (card_id,), fetch='one')
                if fallback_result:
                    return render_template('scan_result.html', 
                                         status='error', 
                                         message='QR code tidak valid')
                else:
                    return render_template('scan_result.html', 
                                         status='error', 
                                         message='Kartu nama tidak ditemukan')
            
            # Extract data (handle both dict and tuple formats)
            if isinstance(result, (list, tuple)):
                name, company_name, phone, scan_count = result[:4]
                qr_exists, is_expired = result[4], result[5]
            else:  # Dict-like
                name = result['name']
                company_name = result['company_name']
                phone = result['phone']
                scan_count = result['scan_count']
                qr_exists = result['id']
                is_expired = result['is_expired']
            
            if is_expired:  # Already used - fast path, no database updates needed
                return render_template('scan_result.html', 
                                     status='expired', 
                                     message='QR code ini sudah pernah digunakan')
            
            # First-time scan: Execute both updates in a single transaction for better performance
            # This reduces network round trips from 2 to 1 and ensures data consistency
            transaction_queries = [
                (update_qr_query, (qr_id,)),
                (update_card_query, (card_id,))
            ]
            
            try:
                db_manager.execute_transaction(transaction_queries)
                # Use the incremented scan count
                updated_count = scan_count + 1
            except Exception as e:
                logger.error(f"Transaction failed during QR scan: {e}")
                return render_template('scan_result.html', 
                                     status='error', 
                                     message='Error memproses scan QR code')
            
        else:
            # Direct access without QR code - single query
            direct_query = 'SELECT name, company_name, phone, scan_count FROM business_cards WHERE id = %s'
            
            result = db_manager.execute_query(direct_query, (card_id,), fetch='one')
            
            if not result:
                return render_template('scan_result.html', 
                                     status='error', 
                                     message='Kartu nama tidak ditemukan')
            
            # Extract data
            if isinstance(result, (list, tuple)):
                name, company_name, phone, updated_count = result
            else:  # Dict-like
                name = result['name']
                company_name = result['company_name']
                phone = result['phone']
                updated_count = result['scan_count']
        
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
        # Total business cards
        result = db_manager.execute_query('SELECT COUNT(*) FROM business_cards', fetch='one')
        total_cards = result[0] if isinstance(result, (list, tuple)) else result['count']
        
        # Total QR codes generated
        result = db_manager.execute_query('SELECT COUNT(*) FROM qr_codes WHERE business_card_id IS NOT NULL', fetch='one')
        total_qr_codes = result[0] if isinstance(result, (list, tuple)) else result['count']
        
        # Total scans (used QR codes)
        query = 'SELECT COUNT(*) FROM qr_codes WHERE business_card_id IS NOT NULL AND is_expired = true'
        result = db_manager.execute_query(query, fetch='one')
        total_scans = result[0] if isinstance(result, (list, tuple)) else result['count']
        
        # Unused QR codes
        unused_qr_codes = total_qr_codes - total_scans
        
        return jsonify({
            'total_business_cards': total_cards,
            'total_qr_codes': total_qr_codes,
            'total_scans': total_scans,
            'unused_qr_codes': unused_qr_codes,
            'database_type': db_manager.db_type
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
