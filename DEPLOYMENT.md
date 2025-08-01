# 🚀 Production Deployment Guide

This guide covers deploying the QR Business Cards application to various free hosting platforms.

## 📋 Prerequisites

- Git repository with your code
- GitHub account (recommended for easy deployments)

## 🆓 Free Hosting Options

### 1. Railway (Recommended) ⭐
**Why Railway?** Easy deployment, generous free tier, supports SQLite databases.

#### Steps:
1. Go to [Railway.app](https://railway.app/)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect the `railway.toml` and `Procfile`
6. Your app will be deployed with a free subdomain

**Features:**
- ✅ Free tier: 512MB RAM, $5 credit/month
- ✅ Custom domains supported
- ✅ Automatic HTTPS
- ✅ File persistence (SQLite works)

### 2. Render
**Why Render?** Good free tier, easy to use, reliable.

#### Steps:
1. Go to [Render.com](https://render.com/)
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Render will detect the `render.yaml` configuration
6. Deploy!

**Features:**
- ✅ Free tier: 512MB RAM, 100GB bandwidth/month
- ✅ Custom domains supported
- ✅ Automatic HTTPS
- ⚠️ Spins down after 15 minutes of inactivity

### 3. Heroku (Limited Free Tier)
**Note:** Heroku ended free tier but offers credits for students/new users.

#### Steps:
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Deploy: `git push heroku main`

**Features:**
- ✅ Easy deployment with `Procfile`
- ✅ Custom domains supported
- ✅ Add-ons ecosystem
- ❌ No longer free (requires payment method)

### 4. Vercel (For Static + Serverless)
**Note:** Best for serverless functions, may have limitations with SQLite.

#### Steps:
1. Go to [Vercel.com](https://vercel.com/)
2. Sign up with GitHub
3. Import your repository
4. Vercel will use the `vercel.json` configuration
5. Deploy!

**Features:**
- ✅ Free tier: Generous limits
- ✅ Global CDN
- ✅ Custom domains
- ⚠️ Serverless limitations (database persistence issues)

## 🛠️ Configuration Files Included

| File | Purpose | Platform |
|------|---------|----------|
| `Procfile` | Process definition | Heroku, Railway |
| `requirements.txt` | Python dependencies | All platforms |
| `runtime.txt` | Python version | Heroku, Render |
| `railway.toml` | Railway configuration | Railway |
| `render.yaml` | Render configuration | Render |
| `vercel.json` | Vercel configuration | Vercel |

## 🗄️ Database Considerations

### SQLite (Current Setup)
- ✅ **Works on:** Railway, Heroku, local development
- ❌ **Issues on:** Vercel (ephemeral filesystem), Render (resets on restart)

### For Render/Vercel (Alternative Options)
If you need persistent data on platforms that don't support file persistence:

1. **PostgreSQL (Free Options):**
   - Supabase (1GB free)
   - PlanetScale (5GB free)
   - Railway PostgreSQL

2. **Quick Migration to PostgreSQL:**
```python
# Add to requirements.txt
psycopg2-binary>=2.9.0

# Update connection in main.py
import os
if 'DATABASE_URL' in os.environ:
    # Use PostgreSQL for production
    DATABASE_URL = os.environ['DATABASE_URL']
else:
    # Use SQLite for development
    DATABASE_URL = 'sqlite:///qr_codes.db'
```

## 🚀 Recommended Deployment Strategy

**For beginners:** Start with **Railway** - it's the easiest and supports SQLite out of the box.

**Steps:**
1. Push your code to GitHub
2. Connect Railway to your repository
3. Your app will be live in minutes!

## 🌐 Environment Variables

Set these in your hosting platform:

| Variable | Value | Purpose |
|----------|-------|---------|
| `FLASK_ENV` | `production` | Disables debug mode |
| `PORT` | `8080` (Railway) / `10000` (Render) | Server port |

## 📱 Testing Your Deployment

After deployment:
1. ✅ Create a business card
2. ✅ Generate QR codes
3. ✅ Scan QR codes with your phone
4. ✅ Test one-time use functionality
5. ✅ Test delete functionality

## 🔧 Troubleshooting

### Common Issues:
1. **"Module not found"** → Check `requirements.txt`
2. **"Database locked"** → Restart the service
3. **"Port already in use"** → Check PORT environment variable
4. **QR codes not working** → Verify your deployed domain in generated URLs

### Logs:
- **Railway:** View logs in dashboard
- **Render:** Check build and runtime logs
- **Heroku:** `heroku logs --tail`

## 🎉 You're Live!

Once deployed, your QR Business Cards application will be accessible worldwide. Share your URL and start creating digital business cards! 

**Default URL formats:**
- Railway: `https://your-project-name.up.railway.app`
- Render: `https://your-service-name.onrender.com`
- Vercel: `https://your-project-name.vercel.app`
