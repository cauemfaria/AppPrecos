# Scalability Guide — economiX Backend

## Current setup (default)

One Render web service runs both the API and the in-process NFCe extraction worker:

```
Render Web Service (gunicorn, 2 workers)
  └── API endpoints  (/api/nfce/extract, /api/scan/save, ...)
  └── In-process NFCe queue (task_queue.py consumer thread)
```

This works well for moderate traffic. The bottleneck is Playwright Chromium (~200MB/instance),
which limits gunicorn to 2 workers on Render's 512MB Starter plan.

## What already scales without changes

- **Auth is stateless** — JWT verification is local (PyJWT), no shared session store.
  Add Render instances freely; auth throughput scales linearly.
- **NFCe queue is durable in the DB** — `processed_urls` is the source of truth.
  If a worker restarts, `recover_orphaned_tasks()` re-enqueues stale jobs automatically.
- **Frontends are static CDN** — already horizontally scaled.
- **Per-user concurrency guard** — `MAX_ACTIVE_NFCE_PER_USER` (default: 5) prevents
  one user from monopolizing the extraction queue.

## Scaling the API (many concurrent users)

On Render, upgrade the backend to a Standard or Pro plan and enable autoscaling:

```yaml
# backend/render.yaml — add under the service:
scaling:
  minInstances: 1
  maxInstances: 3          # adjust based on load
  targetMemoryPercent: 75
  targetCPUPercent: 75
```

Gunicorn stays at `workers = 2` per instance (Playwright memory cap).
Auth scales linearly; extraction throughput scales with instances × 2 workers each.

## Separating extraction into a dedicated worker (high-throughput NFCe scanning)

When many users scan NFCe simultaneously, move extraction to a separate Render Background Worker:

### Step 1 — Update the web service

Set on the Render web service:
```
RUN_INPROCESS_WORKER=false
```

The API will enqueue to `processed_urls` but NOT consume it.

### Step 2 — Add a Render Background Worker

Add to `backend/render.yaml`:

```yaml
  - type: worker
    name: economix-nfce-worker
    env: python
    region: oregon
    plan: starter        # can use a plan with more memory for Playwright
    buildCommand: "./render-build.sh"
    startCommand: "python nfce_worker.py"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: SUPABASE_JWT_SECRET
        sync: false
      - key: PLAYWRIGHT_BROWSERS_PATH
        value: /opt/render/project/.playwright
      - key: WORKER_POLL_INTERVAL
        value: "5"
```

Scale worker instances in the Render dashboard (each additional instance can run one
Playwright extraction at a time; the DB lock in `system_locks` prevents duplicate processing).

### Architecture after separation

```
Render Web (autoscaled, no Playwright)
  └── API only → enqueues to processed_urls

Render Worker (scaled independently)
  └── nfce_worker.py → drains processed_urls → Playwright extraction
```

## Database connection pooling

The Flask backend uses PostgREST (Supabase REST API) which pools connections server-side.
If you add direct `psycopg2` queries, use the Supabase **Supavisor pooler URL**
(`DATABASE_URL` env var, already in render.yaml):

- **Transaction mode** (port 6543): for short-lived queries
- **Session mode** (port 5432): for queries using session-level features

## Auth email at scale

Supabase's built-in SMTP is limited to ~4 emails/hour. For production with many signups:
1. Create an account at [Resend](https://resend.com) or AWS SES
2. Dashboard → Authentication → SMTP Settings → configure custom provider
3. Do this before enabling email confirmation in production
