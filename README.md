# Virtual Business Cards with One-Time QR Codes

A Flask-based web application for creating virtual business cards with one-time QR codes. Each business card can generate unique QR codes that expire after a single scan, perfect for networking and contact sharing.

## 🚀 Features

### Virtual Business Cards 💼
- **Personal Landing Pages**: Each business card gets a beautiful, professional landing page
- **Contact Information**: Store name, company, and phone number
- **Batch QR Generation**: Generate 1-100 one-time QR codes per business card
- **Search Functionality**: Find business cards by company name
- **Delete with Cleanup**: Remove business cards and all associated QR codes
- **Scan Analytics**: Track how many times each business card is viewed
- **vCard Download**: Visitors can save contact info to their phone
- **Professional Design**: Modern, responsive business card display with interactive effects
- **Flexible Downloads**: Single PNG or ZIP batch downloads

### Key Benefits
✅ **Eco-Friendly**: No paper business cards needed  
✅ **Trackable**: See engagement with your contact info  
✅ **Professional**: Beautiful, modern landing pages  
✅ **Secure**: One-time use prevents misuse  
✅ **Mobile-First**: Perfect on all devices  
✅ **Easy Sharing**: Just print QR codes or share digitally  

## 🛠️ Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Local Installation

1. Clone or download this project
2. Navigate to the project directory:
   ```cmd
   cd qrproject
   ```

3. Create a virtual environment:
   ```cmd
   python -m venv venv
   ```

4. Activate the virtual environment:
   ```cmd
   venv\Scripts\activate
   ```

5. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

6. Run the application:
   ```cmd
   python main.py
   ```

7. Open your browser and go to: `http://localhost:5000`

## 🚀 Production Deployment

This application is ready for deployment on free hosting platforms. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guides.

### Quick Deploy Options:

| Platform | Difficulty | Database Support | Free Tier |
|----------|------------|------------------|-----------|
| **Railway** ⭐ | Easy | ✅ SQLite | $5 credit/month |
| **Render** | Easy | ⚠️ Resets | 100GB bandwidth |
| **Vercel** | Medium | ❌ Serverless only | Generous limits |
| **Heroku** | Easy | ✅ SQLite | No longer free |

**Recommended:** Use Railway for the easiest deployment with full SQLite support.

### Environment Variables for Production:
```bash
FLASK_ENV=production
PORT=8080
```

## 🌐 Usage
4. Your app will be live with automatic HTTPS

### Render
1. Fork this repository
2. Connect to Render: https://render.com
3. Create new Web Service from GitHub
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn main:app`

### Heroku
1. Install Heroku CLI
2. Run these commands:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

## 📱 Usage

### Create Virtual Business Cards
1. Open the application in your browser
2. Enter your name, company name, and phone number
3. Click "Create Business Card"
4. Enter quantity (1-100) and generate QR codes for your business card
5. Download as single PNG (for 1 code) or ZIP file (for multiple codes)
6. Print or share the QR codes

### Search and Manage Cards
- **Search**: Type company name to find specific business cards
- **Generate More**: Create additional QR code batches as needed
- **Delete**: Remove business cards and all associated QR codes
- **Track Usage**: Monitor scan counts and QR code usage

### How One-Time QR Codes Work
- Each QR code can only be scanned once
- When someone scans it → they see your professional landing page
- The QR code becomes invalid after first use
- Generate new QR codes as needed for different occasions

### Business Card Landing Pages
- Clean, professional design with your contact information
- "Call Now" button for instant phone calls
- "Save Contact" button downloads vCard file to their phone
- View counter shows total engagement
- Mobile-responsive design works on all devices

### API Endpoints

**Business Cards:**
- `GET /api/business-cards` - Get all business cards (with optional ?search= parameter)
- `POST /api/business-cards` - Create new business card
- `DELETE /api/business-cards/{id}` - Delete business card and all QR codes
- `POST /api/business-cards/{id}/generate-qr` - Generate batch of QR codes (1-100)
- `GET /api/download-qr/{qr_id}` - Download single QR code as PNG
- `POST /api/download-batch` - Download multiple QR codes as ZIP
- `GET /card/{card_id}` - Business card landing page
- `GET /api/stats` - Get usage statistics

## 🗄️ Database Schema

```sql
-- Business cards table
business_cards:
- id (TEXT PRIMARY KEY) - Unique identifier
- name (TEXT) - Full name
- company_name (TEXT) - Company name
- phone (TEXT) - Phone number
- created_at (TIMESTAMP) - When card was created
- scan_count (INTEGER) - Total number of scans

-- QR codes table
qr_codes:
- id (TEXT PRIMARY KEY) - Unique identifier
- code_data (TEXT) - The URL stored in QR code
- created_at (TIMESTAMP) - When code was generated
- scanned_at (TIMESTAMP) - When code was first scanned
- is_expired (BOOLEAN) - Whether code has been used
- metadata (TEXT) - Additional data (JSON)
- business_card_id (TEXT) - Foreign key to business_cards (nullable)
```

## 🔧 Configuration

### Environment Variables
- `PORT`: Port number (default: 5000)
- `DEBUG`: Enable debug mode (default: True in development)

## 📂 Project Structure
```
qrproject/
├── main.py                 # Flask application
├── templates/
│   ├── index.html         # Main web interface
│   └── scan_result.html   # Scan result page
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku deployment
├── runtime.txt           # Python version for Heroku
├── railway.toml          # Railway deployment config
├── qr_codes.db           # SQLite database (created automatically)
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## 🎯 Use Cases

### Perfect For:
- **Networking Events**: Share contact info instantly with one-time codes
- **Trade Shows**: Professional digital presence with tracking
- **Sales Teams**: Track prospect engagement and prevent code sharing
- **Entrepreneurs**: Modern, eco-friendly business cards
- **Real Estate Agents**: Secure property contact sharing
- **Restaurants**: Staff contact information for VIP customers
- **Conferences**: Speaker contact sharing with attendee limits
- **Business Meetings**: Controlled contact information distribution

## 🛡️ Security Features

- Input validation (quantity limits)
- SQL injection protection
- Unique UUID generation
- One-time use enforcement
- Error handling and logging

## 🔄 Future Enhancements

- [ ] PostgreSQL support for production
- [ ] Custom QR code styling (colors, logos)
- [ ] Time-based expiration
- [ ] Batch management and grouping
- [ ] API authentication
- [ ] Advanced analytics dashboard
- [ ] Export data to CSV
- [ ] Rate limiting

## 📝 License

Open source - feel free to use and modify for your projects!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
