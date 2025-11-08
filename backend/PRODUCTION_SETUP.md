# 🚀 Production Setup - Complete Guide

## What Service to Choose on Render?

**Answer: Web Services** ✅

### Why Web Service?
Your Flask backend is a **dynamic web application** that needs to:
- ✅ Run 24/7 to handle API requests
- ✅ Execute Playwright for web scraping
- ✅ Handle multiple concurrent users
- ✅ Connect to external database (Supabase)

### NOT the other services:
- ❌ **Static Sites** - Only for HTML/CSS/JS files (no backend logic)
- ❌ **Background Workers** - For queue-based jobs (not HTTP APIs)
- ❌ **Cron Jobs** - For scheduled tasks (not always-on APIs)
- ❌ **Private Services** - For internal-only services
- ❌ **PostgreSQL** - You already use Supabase
- ❌ **Key Value** - For Redis-like caching only

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         YOUR SETUP                                │
└──────────────────────────────────────────────────────────────────┘

    📱 Android App (Kotlin)
         │
         │ HTTPS Requests
         │
         ▼
    ┌─────────────────────────────────┐
    │   RENDER WEB SERVICE ($7/mo)    │
    │                                  │
    │   ┌─────────────────────────┐   │
    │   │   Gunicorn WSGI Server  │   │
    │   │   - Multi-worker        │   │
    │   │   - Load balancing      │   │
    │   └──────────┬──────────────┘   │
    │              │                   │
    │              ▼                   │
    │   ┌─────────────────────────┐   │
    │   │   Flask App (Python)    │   │
    │   │   ├─ /api/markets       │   │
    │   │   ├─ /api/nfce/extract  │   │
    │   │   ├─ /health            │   │
    │   │   └─ Async processing   │   │
    │   └──────────┬──────────────┘   │
    │              │                   │
    │              ▼                   │
    │   ┌─────────────────────────┐   │
    │   │   Playwright/Chromium   │   │
    │   │   - NFCe web scraping   │   │
    │   └─────────────────────────┘   │
    │                                  │
    └────────────┬─────────────────────┘
                 │
                 │ PostgreSQL Protocol
                 │
                 ▼
    ┌──────────────────────────────┐
    │   SUPABASE (Free tier)       │
    │   - PostgreSQL Database      │
    │   - 4 Tables:                │
    │     • markets                │
    │     • purchases              │
    │     • unique_products        │
    │     • processed_urls         │
    └──────────────────────────────┘
```

---

## Security Features Implemented

### 🔒 Production Security Checklist

✅ **Environment Variables**
- All sensitive data in environment variables
- No hardcoded credentials
- `.env` file in `.gitignore`

✅ **CORS Configuration**
- Restricted to API endpoints only (`/api/*`)
- Proper headers configuration
- No unrestricted access

✅ **Request Validation**
- 16MB max request size (prevents abuse)
- Input validation on all endpoints
- Error handling without exposing internals

✅ **Database Security**
- Service role key (not anon key) for admin operations
- Connection via secure PostgreSQL protocol
- Supabase row-level security ready (if needed)

✅ **API Security**
- Health check endpoint for monitoring
- Structured error responses
- No sensitive data in logs (production mode)

---

## Performance Optimizations

### ⚡ Speed & Efficiency

✅ **Gunicorn Multi-Worker**
```python
workers = (2 × CPU_cores) + 1
# On Starter plan (1 vCPU): 3 workers
# Handles 3 concurrent requests simultaneously
```

✅ **Connection Management**
- Keep-alive connections (5s)
- Connection pooling
- Efficient database queries

✅ **Async Processing**
- Background threads for NFCe extraction
- Non-blocking operations
- Immediate response with status polling

✅ **Timeouts Configured**
- 120s for Playwright operations
- No premature request cancellations
- Optimal for web scraping

✅ **Preload App**
- Application loaded once
- Shared across workers
- Faster response times

---

## Scalability Path

### 👥 Expected Load Capacity

| Plan | RAM | vCPU | Workers | Concurrent Users | Monthly Cost |
|------|-----|------|---------|------------------|--------------|
| **Starter** ⭐ | 512MB | 1 | 3 | 10-50 | $7 |
| **Standard** | 2GB | 2 | 5 | 50-200 | $25 |
| **Pro** | 4GB | 4 | 9 | 200-500 | $85 |

### When to Scale Up?

**From Starter to Standard:**
- Response times > 5s consistently
- Memory usage > 80%
- More than 50 concurrent users
- Database queries getting slow

**From Standard to Pro:**
- Need 100+ concurrent users
- Heavy NFCe processing load
- Multiple markets with frequent updates

---

## Monitoring & Observability

### 📊 What to Monitor

1. **Health Endpoint** - `GET /health`
   - Database connectivity
   - Response time
   - Timestamp

2. **Render Dashboard**
   - CPU usage
   - Memory usage
   - Request count
   - Error rate

3. **Supabase Dashboard**
   - Database size
   - Active connections
   - Query performance
   - Row counts

### 🚨 Alerts to Set Up

Configure in Render:
- Health check failures
- High memory usage (>80%)
- Error rate spikes
- Slow response times (>10s)

---

## Cost Analysis

### 💰 Monthly Breakdown

```
REQUIRED:
- Render Starter: $7/month
  ✓ 512MB RAM
  ✓ Always-on (no cold starts)
  ✓ Auto-deploy from Git
  ✓ SSL certificate included
  ✓ Custom domain support

- Supabase Free: $0/month
  ✓ 500MB database storage
  ✓ 2GB file storage
  ✓ 50k monthly active users
  ✓ Unlimited API requests

TOTAL: $7/month
```

### When to Upgrade Supabase?

**Supabase Pro ($25/month):**
- Database > 500MB
- Need > 50k monthly active users
- Want daily backups
- Need priority support

**Current usage estimate:**
- 100 markets × 1KB = 100KB
- 10,000 purchases × 0.5KB = 5MB
- 5,000 unique products × 0.5KB = 2.5MB
- **Total: ~8MB (well within free tier)**

---

## Testing Checklist

### ✅ Before Going Live

**Backend Tests:**
- [ ] Health check returns 200
- [ ] `/api/markets` returns data
- [ ] `/api/stats` shows correct counts
- [ ] NFCe extraction works with test URL
- [ ] Error handling works (test with invalid data)
- [ ] Response times acceptable (<5s)

**Android App Tests:**
- [ ] App connects to production backend
- [ ] QR code scanning works
- [ ] NFCe data displays correctly
- [ ] Market list populates
- [ ] Product prices show up
- [ ] Error messages display properly

**Database Tests:**
- [ ] All 4 tables exist in Supabase
- [ ] Indexes created
- [ ] Data inserts successfully
- [ ] Queries perform well
- [ ] No duplicate entries

---

## Deployment Commands

### For Windows PowerShell:

```powershell
# Navigate to backend
cd C:\AppPrecos\backend

# Make build script executable (git tracks this)
git update-index --chmod=+x render-build.sh

# Add all changes
git add .

# Commit
git commit -m "Add Render production deployment configuration"

# Push to trigger deploy
git push origin main
```

### For Git Bash / Linux:

```bash
cd backend
chmod +x render-build.sh
git add .
git commit -m "Add Render production deployment configuration"
git push origin main
```

---

## Environment Variables Reference

Copy these to Render Dashboard → Environment:

```env
# Supabase (Get from https://supabase.com/dashboard → Settings → API)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Database (Get from Supabase → Settings → Database → Connection String)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres

# Flask
FLASK_ENV=production

# Playwright
PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.playwright
```

⚠️ **Important**: Replace `[YOUR-PASSWORD]` in DATABASE_URL with your actual password!

---

## FAQ

### Q: Why Render and not Heroku/AWS/GCP?

**A:** Render is simpler and more cost-effective for your use case:
- ✅ $7/month vs Heroku's $25/month
- ✅ Automatic SSL certificates
- ✅ Easy Git integration
- ✅ No credit card for initial setup
- ✅ Playwright/Chromium works out of the box

### Q: Will it handle multiple users simultaneously?

**A:** Yes! Gunicorn multi-worker configuration:
- 3 workers on Starter plan
- Each handles 1 request at a time
- Total: 3 concurrent requests
- Queue system for additional requests
- Typical app usage: 10-50 users comfortably

### Q: What about cold starts?

**A:** Starter plan ($7/mo) = **NO cold starts**
- App runs 24/7
- Immediate responses
- No spin-down delays

Free plan = 15min spin-down (not recommended for production)

### Q: Can I use a custom domain?

**A:** Yes! Render supports custom domains:
1. Go to Render Dashboard → Your Service → Settings
2. Add custom domain (e.g., api.appprecos.com)
3. Update DNS records (Render provides instructions)
4. SSL certificate auto-provisioned

### Q: How do I update the backend code?

**A:** Simply push to GitHub:
```bash
git add .
git commit -m "Update backend"
git push origin main
```
Render auto-deploys in 2-5 minutes!

### Q: What if Render goes down?

**A:** Render has 99.9% uptime SLA:
- Geographic redundancy
- Automatic failover
- Status page: https://status.render.com
- For critical apps: Deploy to multiple regions

### Q: Can I see real-time logs?

**A:** Yes! Two ways:
1. Render Dashboard → Your Service → Logs tab
2. API: `https://api.render.com/v1/services/YOUR_SERVICE_ID/logs`

---

## Next Steps

1. ✅ Read `backend/DEPLOY_CHECKLIST.txt` - Step-by-step deployment
2. ✅ Read `backend/QUICK_START.md` - 5-minute quick guide
3. ✅ Read `backend/DEPLOYMENT.md` - Detailed documentation
4. ✅ Deploy to Render
5. ✅ Update Android app URL
6. ✅ Test end-to-end

---

## Support Resources

- 📚 Render Docs: https://render.com/docs
- 📚 Supabase Docs: https://supabase.com/docs
- 📚 Flask Docs: https://flask.palletsprojects.com/
- 📚 Gunicorn Docs: https://docs.gunicorn.org/

---

**You're all set! Follow the checklist and you'll be live in production within 10 minutes!** 🎉

