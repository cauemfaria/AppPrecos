# Backend / Supabase Review

A practical audit of `backend/` and how it talks to Supabase. The first
section lists what was changed in this PR; the second lists larger
recommendations that were intentionally left for a follow-up.

## Changes shipped in this PR

| Area | Change |
|---|---|
| `supabase_client.py` (new) | Single Supabase client + env validation. Replaces four duplicate `create_client` call sites. |
| `constants.py` (new) | Status / placeholder strings used to live as magic literals scattered across the codebase. |
| `app.py` | Configurable CORS allowlist via `CORS_ALLOWED_ORIGINS` (was hardcoded `*`). Production logs a warning when not set. |
| `app.py` | `/` healthcheck no longer hits the DB (Render hits it constantly); `/health` still does the deep DB ping. |
| `app.py` | `datetime.utcnow()` → `datetime.now(timezone.utc)` everywhere (deprecation + naive-TZ bugs). |
| `app.py` | `resolve_nfce_url` falls back to streamed GET when HEAD returns 403/405/501 — some SEFAZ tenants reject HEAD. |
| `enrichment_worker.py` | `purchases` query now `.order('created_at')` so old items can't starve under continuous insert load. |
| `enrichment_worker.py`, `enrichment_service.py`, `migrate_to_cnpj.py`, `fix_purchase_dates.py`, `task_queue.py`, `quick_status.py` | All import `supabase` from `supabase_client` — no more duplicated env loading and no more hardcoded Windows path. |
| `.env.example` (new) | Documents every env var the backend reads, with safety notes on the service-role key. |

## Findings not addressed in this PR (recommended next steps)

These are larger changes that affect schema, deploy, or architecture, so they're listed here rather than rolled into a refactor PR.

### 1. Row Level Security is effectively disabled
`supabase_migrations.py` creates tables without any RLS policies, and the backend uses the **service-role key** for every query. Combined with the previous `CORS: "*"`, this meant that anyone on the public internet could trigger any endpoint, and the service-role key in the backend would happily execute any of those queries. The CORS allowlist fixes the *origin* control, but:

- Enable `ALTER TABLE … ENABLE ROW LEVEL SECURITY` on every table.
- Add at least a "deny by default, allow service role" policy.
- If you ever expose Supabase directly to the frontend, you'll need real policies anyway.

### 2. Migrations live in a Python `print()` script
`supabase_migrations.py` literally just prints SQL and tells the operator to paste it into the Supabase web editor. It also starts with `DROP TABLE … CASCADE` — running it against prod by accident would erase the database. Suggested: move SQL into versioned `.sql` files under `backend/migrations/` (like `migration_scanned_prices.sql` already does), one per change, and document the order. Tools like `dbmate`, `sqitch`, or Supabase's own CLI migrations are good fits.

### 3. `app.py` is monolithic (1100+ lines)
A natural split would be Flask blueprints: `markets.py`, `nfce.py`, `products.py`, `enrichment.py`, `scan.py`. The `process_nfce_in_background` function is 180+ lines and deeply nested; the duplicate-check + lock-acquire + extract + save phases could each be their own function.

### 4. Extraction lock has a TOCTOU window
`acquire_extraction_lock` does `select → update → 0.2s sleep → select` to detect races. A cleaner solution is a Postgres advisory lock (`SELECT pg_try_advisory_lock(…)`) or a unique constraint on a "currently extracting" sentinel row. Both eliminate the sleep + recheck.

### 5. NFCe HTML parsing is regex-based
`nfce_extractor.py` parses HTML with regex. SEFAZ tweaks markup occasionally and a missing space breaks extraction silently. BeautifulSoup or, better, Playwright locators (`page.locator(...)` and `.inner_text()`) would be more resilient and easier to debug.

### 6. No idempotency on `purchases` insert
If the same NFCe URL is somehow processed twice (e.g. retry after the API call timed out but the DB write succeeded), every product is duplicated. Only `processed_urls.nfce_url` is `UNIQUE`. Consider a composite uniqueness on `(nfce_url, ncm, ean, product_name)` for `purchases`, or check before insert.

### 7. Inconsistent logging
`app.py` uses bare `print()`; `enrichment_worker.py` uses `logging`. Pick one (logging is the right answer for production), add a structured formatter, and route Gunicorn's logs through it.

### 8. Cosmos token rotation persists pointer globally
`_current_cosmos_token_idx` is a module-level int that rotates on 429. Over time, every fresh request starts on whichever token was last rate-limited. Resetting to 0 after a successful request, or tracking per-token cooldowns, would distribute load more evenly.

### 9. Stale-lock detection on naive timestamps
The `processed_urls.processed_at` column is `TIMESTAMP` (no TZ). The Python code patches missing `+00:00` onto strings before parsing — fragile. Changing the column type to `TIMESTAMPTZ` removes a whole category of "off by 3 hours" bugs.

### 10. Health-check path mismatch
`render.yaml` had `healthCheckPath: /`, while there was also a `/health` doing a DB ping. We made `/` cheap on this PR, but for serious monitoring Render should hit `/health` (DB-aware), or there should be a separate uptime monitor (Uptime Robot, Better Uptime) on `/health`.

### 11. `requirements.txt` over-pins low-level deps
Packages like `httpx`, `realtime`, `gotrue`, `postgrest`, `storage3`, `supafunc` are transitive dependencies of `supabase` and shouldn't be pinned here — the right version is whatever `supabase==X` resolves to. Pinning them invites conflicts on the next `supabase` upgrade.

### 12. Frontend uses unauthenticated REST
Both frontends call the Flask API without any auth header. If multi-tenant or per-user state ever becomes a requirement, the backend will need JWT (or Supabase Auth tokens passed through). Worth designing for now even if not implementing.
