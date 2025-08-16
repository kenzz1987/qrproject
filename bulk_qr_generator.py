#!/usr/bin/env python3
"""
Bulk QR Code Generator for Production Migration
Generates large batches of QR codes (up to 200k) for business cards
All QR codes point to production URL for migration purposes
Includes QR code image generation and file organization
"""

import uuid
import time
import sys
import os
import zipfile
import shutil
import tempfile
from datetime import datetime
from database import get_db_manager

# Import QR generation from main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import generate_qr_code

# Production URL - all QR codes will point here
PRODUCTION_URL = "https://web-production-b1d67.up.railway.app"

class BulkQRGenerator:
    def __init__(self):
        self.db_manager = get_db_manager()
        self.total_generated = 0
        self.total_images_created = 0
        self.start_time = None
        self.output_dir = None
        
    def generate_bulk_qr_codes(self, card_id, quantity, batch_size=1000, create_images=True, zip_output=True):
        """
        Generate bulk QR codes for a business card with optional image generation
        
        Args:
            card_id (str): Business card UUID
            quantity (int): Number of QR codes to generate
            batch_size (int): Number of codes to insert per batch (default 1000)
            create_images (bool): Whether to generate QR code image files (default True)
            zip_output (bool): Whether to create ZIP archives of images (default True)
        """
        print(f"\n🚀 Starting bulk QR generation for card {card_id}")
        print(f"📊 Target quantity: {quantity:,} QR codes")
        print(f"🔗 Production URL: {PRODUCTION_URL}")
        print(f"📦 Batch size: {batch_size:,}")
        print(f"🖼️  Generate images: {'Yes' if create_images else 'No'}")
        print(f"📁 Create ZIP files: {'Yes' if zip_output else 'No'}")
        
        # Verify business card exists and get details
        card_info = self._verify_business_card(card_id)
        if not card_info:
            print(f"❌ Error: Business card {card_id} not found")
            return False
        
        # Setup output directories if creating images
        if create_images:
            if not self._setup_output_directory(card_info['company_name'], card_id):
                return False
            
        self.start_time = time.time()
        
        # Prepare SQL for PostgreSQL
        insert_query = 'INSERT INTO qr_codes (id, code_data, business_card_id) VALUES (%s, %s, %s)'
        
        # Generate QR codes in batches
        generated_count = 0
        batch_data = []
        image_batch = []
        
        try:
            for i in range(quantity):
                # Generate unique QR code
                code_id = str(uuid.uuid4())
                scan_url = f"{PRODUCTION_URL}/card/{card_id}?qr={code_id}"
                
                batch_data.append((code_id, scan_url, card_id))
                
                # Add to image batch if creating images
                if create_images:
                    image_batch.append({
                        'id': code_id,
                        'url': scan_url,
                        'index': i + 1
                    })
                
                # Process batch when full or at end
                if len(batch_data) >= batch_size or i == quantity - 1:
                    # Insert database batch
                    self._insert_batch(insert_query, batch_data)
                    generated_count += len(batch_data)
                    
                    # Generate images if requested
                    if create_images:
                        self._generate_image_batch(image_batch, card_info['company_name'])
                    
                    # Clear batches
                    batch_data = []
                    image_batch = []
                    
                    # Progress update
                    self._print_progress(generated_count, quantity)
                    
            # Create ZIP files if requested
            if create_images and zip_output:
                self._create_zip_archives(card_info['company_name'], quantity)
                
            self.total_generated += generated_count
            self._print_completion_stats(generated_count, card_info['company_name'])
            return True
            
        except Exception as e:
            print(f"\n❌ Error during bulk generation: {e}")
            print(f"📊 Generated {generated_count:,} codes before error")
            return False
    
    def _verify_business_card(self, card_id):
        """Verify that the business card exists and return its details"""
        try:
            query = 'SELECT id, company_name, name FROM business_cards WHERE id = %s'
            result = self.db_manager.execute_query(query, (card_id,), fetch='one')
            
            if result:
                if isinstance(result, (list, tuple)):
                    card_id, company_name, name = result
                else:
                    card_id = result['id']
                    company_name = result['company_name']
                    name = result['name']
                
                card_info = {
                    'id': card_id,
                    'company_name': company_name,
                    'name': name or ''
                }
                
                print(f"✅ Business card found: {company_name}")
                return card_info
            return None
            
        except Exception as e:
            print(f"❌ Error verifying business card: {e}")
            return None
    
    def _setup_output_directory(self, company_name, card_id):
        """Setup output directory structure for QR code images"""
        try:
            # Create safe directory name
            safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_company_name = safe_company_name.replace(' ', '_')
            
            # Create output directory structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = f"qr_exports/{safe_company_name}_{timestamp}"
            
            # Create directories
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(f"{self.output_dir}/images", exist_ok=True)
            os.makedirs(f"{self.output_dir}/archives", exist_ok=True)
            
            print(f"📁 Output directory: {self.output_dir}")
            
            # Create info file
            info_file = f"{self.output_dir}/generation_info.txt"
            with open(info_file, 'w') as f:
                f.write(f"QR Code Generation Info\n")
                f.write(f"=======================\n")
                f.write(f"Company: {company_name}\n")
                f.write(f"Card ID: {card_id}\n")
                f.write(f"Production URL: {PRODUCTION_URL}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Database: {self.db_manager.db_type}\n\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up output directory: {e}")
            return False
    
    def _generate_image_batch(self, image_batch, company_name):
        """Generate QR code images for a batch"""
        try:
            for qr_info in image_batch:
                # Generate QR code image
                qr_img = generate_qr_code(qr_info['url'])
                
                # Create filename
                safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_company_name = safe_company_name.replace(' ', '_')
                filename = f"{safe_company_name}_qr_{qr_info['index']:06d}_{qr_info['id'][:8]}.png"
                filepath = f"{self.output_dir}/images/{filename}"
                
                # Save image
                qr_img.save(filepath, 'PNG')
                self.total_images_created += 1
                
        except Exception as e:
            print(f"\n❌ Error generating image batch: {e}")
            raise
    
    def _create_zip_archives(self, company_name, total_quantity):
        """Create ZIP archives for easy distribution"""
        try:
            print(f"\n📦 Creating ZIP archives...")
            
            images_dir = f"{self.output_dir}/images"
            archives_dir = f"{self.output_dir}/archives"
            
            # Create safe company name for files
            safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_company_name = safe_company_name.replace(' ', '_')
            
            # Split into multiple ZIP files if quantity is large (max 50k per ZIP)
            max_per_zip = 50000
            zip_count = (total_quantity + max_per_zip - 1) // max_per_zip
            
            image_files = sorted([f for f in os.listdir(images_dir) if f.endswith('.png')])
            
            for zip_index in range(zip_count):
                start_idx = zip_index * max_per_zip
                end_idx = min(start_idx + max_per_zip, len(image_files))
                
                if zip_count > 1:
                    zip_filename = f"{safe_company_name}_qr_codes_part_{zip_index + 1:02d}_of_{zip_count:02d}.zip"
                else:
                    zip_filename = f"{safe_company_name}_qr_codes.zip"
                
                zip_path = f"{archives_dir}/{zip_filename}"
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for i in range(start_idx, end_idx):
                        image_file = image_files[i]
                        image_path = f"{images_dir}/{image_file}"
                        zipf.write(image_path, image_file)
                
                file_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
                print(f"   📦 Created: {zip_filename} ({file_size:.1f} MB, {end_idx - start_idx:,} images)")
            
            print(f"✅ Created {zip_count} ZIP archive(s) in: {archives_dir}")
            
        except Exception as e:
            print(f"❌ Error creating ZIP archives: {e}")
            # Don't fail the whole process for ZIP creation errors
            pass
    
    def _insert_batch(self, query, batch_data):
        """Insert a batch of QR codes"""
        try:
            # Use executemany for better performance
            if hasattr(self.db_manager, 'execute_many'):
                self.db_manager.execute_many(query, batch_data)
            else:
                # Fallback to individual inserts
                for data in batch_data:
                    self.db_manager.execute_query(query, data)
                    
        except Exception as e:
            print(f"\n❌ Error inserting batch: {e}")
            raise
    
    def _print_progress(self, current, total):
        """Print progress update"""
        percentage = (current / total) * 100
        elapsed = time.time() - self.start_time
        rate = current / elapsed if elapsed > 0 else 0
        
        # Estimate remaining time
        if rate > 0:
            remaining = (total - current) / rate
            eta_str = f"ETA: {self._format_time(remaining)}"
        else:
            eta_str = "ETA: calculating..."
        
        print(f"\r🔄 Progress: {current:,}/{total:,} ({percentage:.1f}%) - "
              f"Rate: {rate:.0f}/sec - {eta_str}", end='', flush=True)
    
    def _print_progress(self, current, total):
        """Print progress update"""
        percentage = (current / total) * 100
        elapsed = time.time() - self.start_time
        rate = current / elapsed if elapsed > 0 else 0
        
        # Estimate remaining time
        if rate > 0:
            remaining = (total - current) / rate
            eta_str = f"ETA: {self._format_time(remaining)}"
        else:
            eta_str = "ETA: calculating..."
        
        # Show image creation progress
        image_info = f" | Images: {self.total_images_created:,}" if self.total_images_created > 0 else ""
        
        print(f"\r🔄 Progress: {current:,}/{total:,} ({percentage:.1f}%) - "
              f"Rate: {rate:.0f}/sec - {eta_str}{image_info}", end='', flush=True)
    
    def _print_completion_stats(self, generated_count, company_name):
        """Print completion statistics"""
        elapsed = time.time() - self.start_time
        rate = generated_count / elapsed if elapsed > 0 else 0
        
        print(f"\n✅ Bulk generation completed!")
        print(f"🏢 Company: {company_name}")
        print(f"📊 Generated: {generated_count:,} QR codes")
        print(f"🖼️  Images created: {self.total_images_created:,}")
        print(f"⏱️  Time taken: {self._format_time(elapsed)}")
        print(f"🚀 Average rate: {rate:.0f} codes/second")
        
        if self.output_dir:
            print(f"📁 Output directory: {self.output_dir}")
            print(f"   📂 Images: {self.output_dir}/images/")
            print(f"   📦 ZIP files: {self.output_dir}/archives/")
            
            # Show directory size
            try:
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(self.output_dir):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                
                size_mb = total_size / (1024 * 1024)
                print(f"💾 Total output size: {size_mb:.1f} MB")
            except:
                pass
    
    def _format_time(self, seconds):
        """Format seconds into readable time"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def list_business_cards(self):
        """List all business cards for selection"""
        try:
            query = '''
                SELECT bc.id, bc.company_name, bc.name, 
                       COUNT(qr.id) as existing_qr_count
                FROM business_cards bc
                LEFT JOIN qr_codes qr ON bc.id = qr.business_card_id
                GROUP BY bc.id, bc.company_name, bc.name
                ORDER BY bc.created_at DESC
            '''
            
            results = self.db_manager.execute_query(query, fetch='all')
            
            print("\n📋 Available Business Cards:")
            print("=" * 80)
            
            for i, row in enumerate(results, 1):
                if isinstance(row, (list, tuple)):
                    card_id, company_name, name, qr_count = row
                else:
                    card_id = row['id']
                    company_name = row['company_name']
                    name = row['name']
                    qr_count = row['existing_qr_count']
                
                name_display = f" ({name})" if name else ""
                print(f"{i:2d}. {company_name}{name_display}")
                print(f"    ID: {card_id}")
                print(f"    Existing QR codes: {qr_count:,}")
                print()
            
            return results
            
        except Exception as e:
            print(f"❌ Error listing business cards: {e}")
            return []
    
    def get_database_stats(self):
        """Get current database statistics"""
        try:
            # Total business cards
            result = self.db_manager.execute_query('SELECT COUNT(*) FROM business_cards', fetch='one')
            total_cards = result[0] if isinstance(result, (list, tuple)) else result['count']
            
            # Total QR codes
            result = self.db_manager.execute_query('SELECT COUNT(*) FROM qr_codes', fetch='one')
            total_qr_codes = result[0] if isinstance(result, (list, tuple)) else result['count']
            
            print(f"\n📊 Database Statistics:")
            print(f"🏢 Total Business Cards: {total_cards:,}")
            print(f"📱 Total QR Codes: {total_qr_codes:,}")
            print(f"🗄️  Database Type: {self.db_manager.db_type}")
            
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")

def main():
    """Main function for interactive bulk QR generation"""
    print("🎯 Bulk QR Code Generator for Production Migration")
    print("=" * 60)
    
    generator = BulkQRGenerator()
    
    # Show database stats
    generator.get_database_stats()
    
    # List business cards
    cards = generator.list_business_cards()
    
    if not cards:
        print("❌ No business cards found. Please create some business cards first.")
        return
    
    try:
        # Get user selection
        print("📝 Select a business card by number (or 'q' to quit):")
        choice = input("Enter choice: ").strip()
        
        if choice.lower() == 'q':
            print("👋 Goodbye!")
            return
        
        card_index = int(choice) - 1
        if card_index < 0 or card_index >= len(cards):
            print("❌ Invalid selection")
            return
        
        # Get selected card
        selected_card = cards[card_index]
        if isinstance(selected_card, (list, tuple)):
            card_id, company_name = selected_card[0], selected_card[1]
        else:
            card_id = selected_card['id']
            company_name = selected_card['company_name']
        
        print(f"\n✅ Selected: {company_name}")
        
        # Get quantity
        print(f"\n📊 How many QR codes to generate?")
        print(f"💡 Recommended: 200000 for production migration")
        quantity_input = input("Enter quantity (default 200000): ").strip()
        
        if not quantity_input:
            quantity = 200000
        else:
            quantity = int(quantity_input)
        
        if quantity <= 0:
            print("❌ Quantity must be positive")
            return
        
        if quantity > 500000:
            print("⚠️  Warning: Generating more than 500k codes may take a very long time")
            confirm = input("Continue? (y/N): ").strip().lower()
            if confirm != 'y':
                print("👋 Operation cancelled")
                return
        
        # Get batch size
        print(f"\n📦 Batch size for database inserts?")
        print(f"💡 Recommended: 1000 (larger batches = faster, but more memory)")
        batch_input = input("Enter batch size (default 1000): ").strip()
        
        if not batch_input:
            batch_size = 1000
        else:
            batch_size = int(batch_input)
        
        if batch_size <= 0 or batch_size > 10000:
            print("❌ Batch size must be between 1 and 10000")
            return
        
        # Ask about image generation
        print(f"\n🖼️  Generate QR code image files?")
        print(f"💡 Recommended: Yes (creates PNG files for download)")
        print(f"⚠️  Note: {quantity:,} images will require ~{quantity * 50 / 1024:.0f} MB disk space")
        create_images_input = input("Generate images? (Y/n): ").strip().lower()
        create_images = create_images_input != 'n'
        
        # Ask about ZIP creation if generating images
        zip_output = False
        if create_images:
            print(f"\n📦 Create ZIP archives for easy download?")
            print(f"💡 Recommended: Yes (organizes images into downloadable ZIP files)")
            zip_input = input("Create ZIP files? (Y/n): ").strip().lower()
            zip_output = zip_input != 'n'
        
        # Confirm generation
        print(f"\n🎯 Generation Summary:")
        print(f"🏢 Business Card: {company_name}")
        print(f"📊 Quantity: {quantity:,} QR codes")
        print(f"📦 Batch Size: {batch_size:,}")
        print(f"🔗 Target URL: {PRODUCTION_URL}")
        print(f"🖼️  Generate Images: {'Yes' if create_images else 'No'}")
        if create_images:
            print(f"📁 Create ZIP Files: {'Yes' if zip_output else 'No'}")
            estimated_size = quantity * 50 / 1024  # ~50KB per QR image
            print(f"💾 Estimated Size: ~{estimated_size:.0f} MB")
        
        confirm = input(f"\n⚠️  This will generate {quantity:,} QR codes. Continue? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("👋 Operation cancelled")
            return
        
        # Start generation
        print(f"\n🚀 Starting bulk generation...")
        success = generator.generate_bulk_qr_codes(card_id, quantity, batch_size, create_images, zip_output)
        
        if success:
            print(f"\n🎉 Bulk generation completed successfully!")
            generator.get_database_stats()
        else:
            print(f"\n❌ Bulk generation failed")
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Generation interrupted by user")
        print(f"📊 Total generated in this session: {generator.total_generated:,}")
    except ValueError:
        print("❌ Invalid input. Please enter a valid number.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
