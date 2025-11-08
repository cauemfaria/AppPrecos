# Quick Start - Deploy to Render in 5 Minutes

## Step 1: Get Supabase Credentials (2 min)

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. **Settings** → **API** → Copy:
   - `Project URL` 
   - `service_role` key (secret)
   - `anon` key
4. **Settings** → **Database** → Copy `Connection string`

## Step 2: Deploy to Render (3 min)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Fill in:
   - **Name**: `appprecos-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `./render-build.sh`
   - **Start Command**: `gunicorn --config gunicorn_config.py app:app`
   - **Plan**: **Starter** ($7/month)

5. Add Environment Variables:
   ```
   SUPABASE_URL=<your-supabase-url>
   SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
   SUPABASE_ANON_KEY=<your-anon-key>
   DATABASE_URL=<your-connection-string>
   FLASK_ENV=production
   ```

6. Click **Create Web Service**

## Step 3: Make Build Script Executable

Before first deploy:
```bash
cd backend
chmod +x render-build.sh
git add .
git commit -m "Add Render deployment config"
git push
```

## Step 4: Verify Deployment

Once deployed, test your API:
```bash
# Replace with your Render URL
curl https://appprecos-backend.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-08T..."
}
```

## Step 5: Update Android App

Find your API service file and update the URL:

```kotlin
// Update BASE_URL to your Render URL
private const val BASE_URL = "https://appprecos-backend.onrender.com"
```

## Done! 🎉

Your backend is now:
- ✅ Running 24/7 on Render
- ✅ Connected to Supabase
- ✅ Ready for multiple users
- ✅ Optimized for production

**Your API URL**: `https://appprecos-backend.onrender.com`

## Monitoring

- **Logs**: Render Dashboard → Your Service → Logs
- **Health**: `https://appprecos-backend.onrender.com/health`
- **Stats**: `https://appprecos-backend.onrender.com/api/stats`

