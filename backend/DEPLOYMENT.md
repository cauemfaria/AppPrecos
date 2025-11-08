# AppPrecos Backend - Render Deployment Guide

## Overview
This backend is a production-ready Flask API that uses:
- **Supabase** for PostgreSQL database
- **Playwright** for web scraping NFCe receipts
- **Gunicorn** for production WSGI server
- **Multi-worker** configuration for handling concurrent users

## Render Setup Instructions

### 1. Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your Git repository
4. Configure the service:
   - **Name**: `appprecos-backend`
   - **Region**: Oregon (or closest to your users)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `./render-build.sh`
   - **Start Command**: `gunicorn --config gunicorn_config.py app:app`
   - **Plan**: **Starter** ($7/month) or **Standard** for production

### 2. Environment Variables

Add these in Render Dashboard → Environment:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
FLASK_ENV=production
PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.playwright
```

**Get Supabase Credentials:**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - Project URL → `SUPABASE_URL`
   - service_role key (secret) → `SUPABASE_SERVICE_ROLE_KEY`
   - anon public key → `SUPABASE_ANON_KEY`
5. Go to **Settings** → **Database** → Copy connection string → `DATABASE_URL`

### 3. Make Build Script Executable

Before deploying, run locally:
```bash
chmod +x backend/render-build.sh
git add backend/render-build.sh
git commit -m "Make build script executable"
git push
```

### 4. Deploy

Click **"Create Web Service"** - Render will:
1. Install Python dependencies
2. Install Playwright + Chromium
3. Start Gunicorn with multiple workers
4. Your API will be live at: `https://appprecos-backend.onrender.com`

## Production Features

### Security
✅ CORS configured for mobile apps  
✅ Environment variables for sensitive data  
✅ Request size limits (16MB max)  
✅ Service role key for admin operations  

### Performance
✅ Multi-worker Gunicorn (handles concurrent users)  
✅ Worker formula: `(2 × CPU cores) + 1`  
✅ Connection pooling  
✅ Async NFCe processing with threading  
✅ 120s timeout for scraping operations  

### Monitoring
✅ Health check endpoint: `/health`  
✅ Structured logging  
✅ Request/response tracking  
✅ Database connection monitoring  

## API Endpoints

### Health & Info
- `GET /` - API information
- `GET /health` - Health check

### Markets
- `GET /api/markets` - List all markets
- `GET /api/markets/{market_id}` - Get market details
- `GET /api/markets/{market_id}/products` - Get market products

### NFCe Processing
- `POST /api/nfce/extract` - Extract and save NFCe data
- `GET /api/nfce/status/{url}` - Check processing status
- `GET /api/stats` - Database statistics

## Update Android App

Update your Android app's API URL to point to Render:

**File**: `android/app/src/main/java/com/appprecos/network/ApiService.kt`

```kotlin
object ApiService {
    private const val BASE_URL = "https://appprecos-backend.onrender.com"
    
    // ... rest of code
}
```

## Scaling Considerations

### Free Tier
- ⚠️ Spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- ❌ Not recommended for production

### Starter Plan ($7/month)
- ✅ Always running (no spin-down)
- ✅ 512MB RAM
- ✅ Good for 10-50 concurrent users
- ✅ **Recommended for production**

### Standard Plan ($25/month)
- ✅ 2GB RAM
- ✅ More CPU
- ✅ Good for 100+ concurrent users
- ✅ Recommended for high traffic

## Monitoring & Logs

View logs in Render Dashboard:
1. Go to your service
2. Click **"Logs"** tab
3. Monitor requests, errors, and performance

## Troubleshooting

### Issue: Build fails on Playwright
**Solution**: Ensure `render-build.sh` has execute permissions

### Issue: Timeout on NFCe extraction
**Solution**: Already configured with 120s timeout in gunicorn_config.py

### Issue: Database connection errors
**Solution**: Verify `DATABASE_URL` includes password and correct host

### Issue: CORS errors from Android
**Solution**: CORS is pre-configured for all origins in production

## Database Setup

Ensure your Supabase tables exist:

```sql
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS markets (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(20) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS purchases (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(20) REFERENCES markets(market_id),
    ncm VARCHAR(8) NOT NULL,
    quantity DECIMAL(10,3),
    unidade_comercial VARCHAR(5),
    total_price DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    nfce_url TEXT,
    purchase_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS unique_products (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(20) REFERENCES markets(market_id),
    ncm VARCHAR(8) NOT NULL,
    unidade_comercial VARCHAR(5),
    price DECIMAL(10,2),
    nfce_url TEXT,
    last_updated TIMESTAMP,
    UNIQUE(market_id, ncm)
);

CREATE TABLE IF NOT EXISTS processed_urls (
    id SERIAL PRIMARY KEY,
    nfce_url TEXT UNIQUE NOT NULL,
    market_id VARCHAR(20),
    products_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing',
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_purchases_market ON purchases(market_id);
CREATE INDEX idx_purchases_ncm ON purchases(ncm);
CREATE INDEX idx_unique_products_market ON unique_products(market_id);
CREATE INDEX idx_processed_urls ON processed_urls(nfce_url);
```

## Cost Breakdown

| Service | Plan | Cost | Purpose |
|---------|------|------|---------|
| Supabase | Free | $0 | Database (500MB included) |
| Render | Starter | $7/mo | Backend API hosting |
| **Total** | | **$7/mo** | Production-ready |

## Support

For issues, check:
1. Render logs
2. Supabase logs
3. Health check endpoint: `https://your-app.onrender.com/health`

