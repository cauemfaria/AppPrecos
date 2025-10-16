# Deployment Guide

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js (optional, for frontend tools)
- Android Studio
- Git

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# 6. Run server
python app.py
```

Server runs at: `http://localhost:5000`

### Android Setup

```bash
# 1. Navigate to android
cd android

# 2. Open in Android Studio
# File → Open → Select android/ folder

# 3. Update API base URL in code
# Change to your backend URL (localhost or deployed)

# 4. Build and run
./gradlew assembleDebug
```

---

## Production Deployment

### Backend Deployment Options

#### Option 1: Heroku

```bash
# Install Heroku CLI
# heroku login

cd backend

# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Create heroku app
heroku create appprecos-backend

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key

# Deploy
git push heroku main

# Initialize database
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### Option 2: Railway.app

```bash
# 1. Create account at railway.app
# 2. Connect GitHub repo
# 3. Select backend/ folder as root
# 4. Add PostgreSQL database
# 5. Set environment variables
# 6. Deploy automatically on git push
```

#### Option 3: Docker

```bash
cd backend

# Build image
docker build -t appprecos-backend .

# Run container
docker run -p 5000:5000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  appprecos-backend

# Or use docker-compose
docker-compose up
```

#### Option 4: AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu)
# 2. SSH into instance
# 3. Install dependencies
sudo apt update
sudo apt install python3-pip postgresql nginx

# 4. Clone repository
git clone https://github.com/yourusername/AppPrecos.git
cd AppPrecos/backend

# 5. Install Python packages
pip3 install -r requirements.txt
playwright install chromium

# 6. Set up systemd service
# Create /etc/systemd/system/appprecos.service

# 7. Configure Nginx as reverse proxy
# 8. Set up SSL with Let's Encrypt
```

---

### Android Deployment

#### Google Play Store

```bash
# 1. Update API base URL to production
# In ApiClient.kt:
const val BASE_URL = "https://your-backend-url.com/api"

# 2. Update version in build.gradle.kts
versionCode = 1
versionName = "1.0"

# 3. Generate signed APK
# Android Studio → Build → Generate Signed Bundle/APK

# 4. Upload to Google Play Console
# Create app listing, upload APK, submit for review
```

#### Direct APK Distribution

```bash
# Generate release APK
cd android
./gradlew assembleRelease

# APK located at:
# app/build/outputs/apk/release/app-release.apk
```

---

## Environment Variables

### Backend (Production)

Create `.env` file:
```bash
FLASK_ENV=production
SECRET_KEY=your-very-secret-key-here
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ALLOWED_ORIGINS=https://your-frontend.com
```

### Android

Update in `build.gradle.kts`:
```kotlin
buildConfigField("String", "API_BASE_URL", "\"https://api.yourserver.com\"")
```

---

## Database Migration

### From SQLite to PostgreSQL

```bash
# 1. Export data from SQLite
python -c "
from app import app, db, Market, Purchase, UniqueProduct
import json
with app.app_context():
    markets = [m.to_dict() for m in Market.query.all()]
    # ... export logic
"

# 2. Update DATABASE_URL
export DATABASE_URL=postgresql://...

# 3. Import to PostgreSQL
# Run migration script
```

---

## Monitoring & Logging

### Recommended Tools

**Backend:**
- Sentry (error tracking)
- Loguru (logging)
- Prometheus (metrics)

**Database:**
- pgAdmin (PostgreSQL management)
- Query monitoring

**Infrastructure:**
- Uptime monitoring (UptimeRobot)
- Performance monitoring (New Relic)

---

## Backup Strategy

### Database Backups

**Automated:**
```bash
# Daily backup cron job
0 2 * * * pg_dump appprecos > /backups/db_$(date +\%Y\%m\%d).sql
```

**Manual:**
```bash
# PostgreSQL
pg_dump appprecos > backup.sql

# SQLite
cp appprecos.db appprecos_backup.db
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
tail -f app.log

# Verify database connection
python -c "from app import db; db.create_all()"

# Check port availability
netstat -an | grep 5000
```

### NFCe extraction failing
```bash
# Verify Playwright installation
playwright install chromium

# Test manually
python backend/nfce_crawler_ultimate.py

# Check network connectivity
```

### Android can't connect to backend
```bash
# Verify backend URL in code
# Check if backend is running
# Check firewall settings
# Use ngrok for local testing: ngrok http 5000
```

