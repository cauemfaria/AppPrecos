# Supabase Auth — Setup Guide

## 1. Apply the database migration

Run the SQL in `migration_auth.sql` in the Supabase SQL Editor:
- Dashboard → SQL Editor → New query → paste contents → Run

## 2. Configure authentication providers

### Email/Password
- Dashboard → Authentication → Providers → Email
- Enable: ✅
- Confirm email: your choice (recommended: ON for production, OFF for dev)
- If you enable email confirmation:
  - Configure a custom SMTP provider (e.g. Resend, SES) for production
  - Supabase's built-in SMTP is rate-limited to ~4 emails/hour
  - Settings → Auth → SMTP Settings

### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Google+ API** or **Google Identity**
4. Create **OAuth 2.0 Client ID** (Web application type)
5. Add authorized redirect URIs:
   - `https://your-project.supabase.co/auth/v1/callback`
   (found in: Dashboard → Authentication → Providers → Google → Callback URL)
6. Copy Client ID and Client Secret
7. Dashboard → Authentication → Providers → Google → Enable → paste credentials

## 3. Set allowed redirect URLs

Dashboard → Authentication → URL Configuration → Redirect URLs:

Add:
- `http://localhost:5173` (main app dev)
- `http://localhost:5174` (worker app dev — may vary)
- `https://your-main-app.onrender.com`
- `https://your-worker-app.onrender.com`

## 4. Get your keys for .env files

Dashboard → Project Settings → API:

| Key | Use |
|-----|-----|
| **Project URL** | `VITE_SUPABASE_URL` (both frontends) |
| **anon public** key | `VITE_SUPABASE_ANON_KEY` (both frontends) |
| **JWT Secret** | `SUPABASE_JWT_SECRET` (backend only — keep secret) |
| **service_role** key | `SUPABASE_SERVICE_ROLE_KEY` (backend only — already set) |

**Never expose `service_role` or `JWT Secret` in frontend code or public repos.**

## 5. Set Render environment variables

In the Render dashboard, for each service, add:

**Backend (`appprecos-backend`):**
- `SUPABASE_JWT_SECRET` = JWT Secret from above
- `CORS_ALLOWED_ORIGINS` = comma-separated deployed app origins
- `RUN_INPROCESS_WORKER` = `true` (default; see SCALING.md to change)

**Frontend static sites:**
- `VITE_SUPABASE_URL` = Project URL
- `VITE_SUPABASE_ANON_KEY` = anon public key
