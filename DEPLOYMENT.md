# 🚀 Production Deployment Guide

This guide covers deploying the QR Business Cards application to various free hosting platforms.

## 📋 Prerequisites

- Git repository with your code
- GitHub account (recommended for easy deployments)

## 🆓 Free Hosting Options

### 1. Railway (Recommended) ⭐
**Why Railway?** Easy deployment, generous free tier, built-in PostgreSQL support.

#### Steps:
1. Go to [Railway.app](https://railway.app/)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add PostgreSQL database service to your project
6. Railway will automatically set DATABASE_URL environment variable
7. Your app will be deployed with a free subdomain

**Features:**
- ✅ Free tier: 512MB RAM, $5 credit/month
- ✅ Custom domains supported
- ✅ Automatic HTTPS
- ✅ PostgreSQL database included

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

## 🗄️ Database Setup

### PostgreSQL (Production Database)
The application uses PostgreSQL for production deployments:

- ✅ **Railway**: Provides managed PostgreSQL automatically
- ✅ **Render**: Free PostgreSQL database available
- ✅ **Heroku**: Offers free PostgreSQL add-on
- ⚠️ **Vercel**: Requires external PostgreSQL service

### Database Configuration
The application automatically detects PostgreSQL via the `DATABASE_URL` environment variable:

```bash
# Railway/Heroku format (automatically provided)
DATABASE_URL=postgresql://username:password@host:port/database

# Manual configuration (if needed)
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=yourpassword
PGDATABASE=qrproject
```

### Free PostgreSQL Options
For platforms that don't provide databases:
- **Supabase**: 500MB free
- **Aiven**: 1-month free trial
- **ElephantSQL**: 20MB free
- **Railway**: Free PostgreSQL with project

## 🚀 Recommended Deployment Strategy

**For beginners:** Start with **Railway** - it's the easiest with built-in PostgreSQL support.

**Steps:**
1. Push your code to GitHub
2. Connect Railway to your repository
3. Add PostgreSQL database service
4. Your app will be live in minutes!

## 🌐 Environment Variables

Set these in your hosting platform:

| Variable | Value | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | (auto-provided) | PostgreSQL connection |
| `FLASK_ENV` | `production` | Disables debug mode |
| `SECRET_KEY` | (random string) | Session security |
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
