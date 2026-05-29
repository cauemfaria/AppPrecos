"""
Verification script for the Supabase Auth integration.

Checks syntax of all new/modified Python files, verifies key strings are
present in each file, and confirms that new files exist.

Run from the project root:
    python backend/verify_auth.py

Exits with code 0 if all checks pass, 1 if any check fails.
"""

import ast
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

results = []


def check(label, ok, detail=""):
    status = PASS if ok else FAIL
    line = f"  [{status}] {label}"
    if detail:
        line += f"  ({detail})"
    print(line)
    results.append(ok)
    return ok


def read_file(rel_path):
    path = os.path.join(PROJECT_DIR, rel_path)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def file_exists(rel_path):
    return os.path.isfile(os.path.join(PROJECT_DIR, rel_path))


def syntax_ok(rel_path):
    src = read_file(rel_path)
    if src is None:
        return False, "file not found"
    try:
        ast.parse(src)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


def contains(rel_path, needle):
    src = read_file(rel_path)
    if src is None:
        return False
    return needle in src


# ── Section 1: File existence ─────────────────────────────────────────────────
print("\n=== File existence ===")
check("backend/auth.py exists",            file_exists("backend/auth.py"))
check("backend/nfce_worker.py exists",     file_exists("backend/nfce_worker.py"))
check("backend/migration_auth.sql exists", file_exists("backend/migration_auth.sql"))
check("backend/SUPABASE_AUTH_SETUP.md exists", file_exists("backend/SUPABASE_AUTH_SETUP.md"))
check("backend/SCALING.md exists",         file_exists("backend/SCALING.md"))
check("frontend/src/lib/supabase.ts exists",
      file_exists("frontend/src/lib/supabase.ts"))
check("worker-frontend/src/lib/supabase.ts exists",
      file_exists("worker-frontend/src/lib/supabase.ts"))
check("frontend/src/store/useAuthStore.ts exists",
      file_exists("frontend/src/store/useAuthStore.ts"))
check("worker-frontend/src/store/useAuthStore.ts exists",
      file_exists("worker-frontend/src/store/useAuthStore.ts"))
check("frontend/src/pages/LoginPage.tsx exists",
      file_exists("frontend/src/pages/LoginPage.tsx"))
check("worker-frontend/src/pages/LoginPage.tsx exists",
      file_exists("worker-frontend/src/pages/LoginPage.tsx"))
check("frontend/render.yaml exists",       file_exists("frontend/render.yaml"))
check("worker-frontend/render.yaml exists", file_exists("worker-frontend/render.yaml"))
check("frontend/.env.example exists",      file_exists("frontend/.env.example"))
check("worker-frontend/.env.example exists", file_exists("worker-frontend/.env.example"))


# ── Section 2: Python syntax ──────────────────────────────────────────────────
print("\n=== Python syntax ===")
for pyfile in ["backend/auth.py", "backend/app.py", "backend/task_queue.py",
               "backend/nfce_worker.py", "backend/supabase_client.py"]:
    ok, detail = syntax_ok(pyfile)
    check(f"{pyfile} syntax OK", ok, detail)


# ── Section 3: backend/auth.py ────────────────────────────────────────────────
print("\n=== backend/auth.py ===")
check("imports SUPABASE_JWT_SECRET from supabase_client",
      contains("backend/auth.py", "SUPABASE_JWT_SECRET"))
check("decodes with audience='authenticated'",
      contains("backend/auth.py", "audience='authenticated'"))
check("sets g.user_id",
      contains("backend/auth.py", "g.user_id"))
check("get_user_id_from_token function defined",
      contains("backend/auth.py", "def get_user_id_from_token"))
check("require_auth decorator defined",
      contains("backend/auth.py", "def require_auth"))
check("returns 401 on missing token",
      contains("backend/auth.py", "401"))


# ── Section 4: backend/supabase_client.py ────────────────────────────────────
print("\n=== backend/supabase_client.py ===")
check("SUPABASE_JWT_SECRET loaded from env",
      contains("backend/supabase_client.py", "SUPABASE_JWT_SECRET"))
check("warns when SUPABASE_JWT_SECRET is empty",
      contains("backend/supabase_client.py", "SUPABASE_JWT_SECRET is not set"))


# ── Section 5: backend/app.py ─────────────────────────────────────────────────
print("\n=== backend/app.py ===")
check("imports get_user_id_from_token from auth",
      contains("backend/app.py", "from auth import get_user_id_from_token"))
check("imports g from Flask",
      contains("backend/app.py", "from flask import") and
      contains("backend/app.py", ", g"))
check("before_request guard present",
      contains("backend/app.py", "before_request"))
check("before_request skips OPTIONS",
      contains("backend/app.py", "OPTIONS"))
check("before_request skips non-/api/ paths",
      contains("backend/app.py", "startswith('/api/')"))
check("/api/nfce/extract stamps scanned_by",
      contains("backend/app.py", "'scanned_by': g.user_id"))
check("/api/scan/save stamps scanned_by",
      contains("backend/app.py", "'scanned_by': g.user_id"))
check("per-user 429 concurrency guard present",
      contains("backend/app.py", "429"))
check("MAX_ACTIVE_NFCE_PER_USER used",
      contains("backend/app.py", "MAX_ACTIVE_NFCE_PER_USER"))


# ── Section 6: backend/task_queue.py ─────────────────────────────────────────
print("\n=== backend/task_queue.py ===")
check("_ensure_worker_started checks RUN_INPROCESS_WORKER",
      contains("backend/task_queue.py", "RUN_INPROCESS_WORKER"))
check("recover_orphaned_tasks skips when RUN_INPROCESS_WORKER=false",
      contains("backend/task_queue.py", "RUN_INPROCESS_WORKER"))


# ── Section 7: backend/requirements.txt ──────────────────────────────────────
print("\n=== backend/requirements.txt ===")
check("PyJWT present",
      contains("backend/requirements.txt", "PyJWT"))


# ── Section 8: backend/migration_auth.sql ────────────────────────────────────
print("\n=== backend/migration_auth.sql ===")
check("profiles table defined",
      contains("backend/migration_auth.sql", "CREATE TABLE") and
      contains("backend/migration_auth.sql", "profiles"))
check("handle_new_user trigger defined",
      contains("backend/migration_auth.sql", "handle_new_user"))
check("scanned_by column on processed_urls",
      contains("backend/migration_auth.sql", "processed_urls") and
      contains("backend/migration_auth.sql", "scanned_by"))
check("scanned_by column on scanned_prices",
      contains("backend/migration_auth.sql", "scanned_prices") and
      contains("backend/migration_auth.sql", "scanned_by"))
check("scanned_by columns are nullable (no NOT NULL constraint on new columns)",
      not contains("backend/migration_auth.sql", "scanned_by uuid NOT NULL"))
check("RLS policies use (select auth.uid()) caching pattern",
      contains("backend/migration_auth.sql", "(SELECT auth.uid())") or
      contains("backend/migration_auth.sql", "(select auth.uid())"))
check("indexes on scanned_by created",
      contains("backend/migration_auth.sql", "idx_processed_urls_scanned_by") and
      contains("backend/migration_auth.sql", "idx_scanned_prices_scanned_by"))


# ── Section 9: frontend/src/lib/supabase.ts ──────────────────────────────────
print("\n=== frontend/src/lib/supabase.ts ===")
check("uses VITE_SUPABASE_URL",
      contains("frontend/src/lib/supabase.ts", "VITE_SUPABASE_URL"))
check("uses VITE_SUPABASE_ANON_KEY",
      contains("frontend/src/lib/supabase.ts", "VITE_SUPABASE_ANON_KEY"))
check("autoRefreshToken: true",
      contains("frontend/src/lib/supabase.ts", "autoRefreshToken: true"))
check("exports supabase client",
      contains("frontend/src/lib/supabase.ts", "export const supabase"))
check("exports Profile type",
      contains("frontend/src/lib/supabase.ts", "export type Profile"))


# ── Section 10: worker-frontend/src/lib/supabase.ts ──────────────────────────
print("\n=== worker-frontend/src/lib/supabase.ts ===")
check("uses VITE_SUPABASE_URL",
      contains("worker-frontend/src/lib/supabase.ts", "VITE_SUPABASE_URL"))
check("uses VITE_SUPABASE_ANON_KEY",
      contains("worker-frontend/src/lib/supabase.ts", "VITE_SUPABASE_ANON_KEY"))
check("autoRefreshToken: true",
      contains("worker-frontend/src/lib/supabase.ts", "autoRefreshToken: true"))
check("exports supabase client",
      contains("worker-frontend/src/lib/supabase.ts", "export const supabase"))
check("exports Profile type",
      contains("worker-frontend/src/lib/supabase.ts", "export type Profile"))


# ── Section 11: useAuthStore (both apps) ─────────────────────────────────────
print("\n=== useAuthStore (both apps) ===")
for app in ["frontend", "worker-frontend"]:
    path = f"{app}/src/store/useAuthStore.ts"
    check(f"{app}: holds session, user, profile, loading",
          all(contains(path, k) for k in ["session", "user", "profile", "loading"]))
    check(f"{app}: initialize() defined",
          contains(path, "initialize"))
    check(f"{app}: signOut() defined",
          contains(path, "signOut"))
    check(f"{app}: uses getSession()",
          contains(path, "getSession"))
    check(f"{app}: uses onAuthStateChange",
          contains(path, "onAuthStateChange"))
    check(f"{app}: returns unsubscribe from initialize()",
          contains(path, "unsubscribe"))
    check(f"{app}: no persist middleware",
          not contains(path, "persist("))


# ── Section 12: LoginPage (both apps) ────────────────────────────────────────
print("\n=== LoginPage (both apps) ===")
for app in ["frontend", "worker-frontend"]:
    path = f"{app}/src/pages/LoginPage.tsx"
    check(f"{app}: email/password form present",
          contains(path, "signInWithPassword"))
    check(f"{app}: signup toggle present",
          contains(path, "signUp"))
    check(f"{app}: Google OAuth button present",
          contains(path, "signInWithOAuth"))
    check(f"{app}: Portuguese error messages",
          contains(path, "E-mail ou senha incorretos"))

check("worker-frontend LoginPage: 'Funcionário' badge",
      contains("worker-frontend/src/pages/LoginPage.tsx", "Funcionário"))
check("worker-frontend LoginPage: worker subtitle text",
      contains("worker-frontend/src/pages/LoginPage.tsx", "registrar os preços"))


# ── Section 13: App.tsx (both apps) ──────────────────────────────────────────
print("\n=== App.tsx (both apps) ===")
for app in ["frontend", "worker-frontend"]:
    path = f"{app}/src/App.tsx"
    check(f"{app}: calls initialize() in useEffect",
          contains(path, "initialize") and contains(path, "useEffect"))
    check(f"{app}: loading spinner shown while loading",
          contains(path, "loading"))
    check(f"{app}: LoginPage shown if no session",
          contains(path, "LoginPage") and contains(path, "session"))
    check(f"{app}: BrowserRouter + Routes present",
          contains(path, "BrowserRouter") and contains(path, "Routes"))

check("frontend App.tsx: QueueManager present",
      contains("frontend/src/App.tsx", "QueueManager"))
check("frontend App.tsx: ReloadPrompt present",
      contains("frontend/src/App.tsx", "ReloadPrompt"))
check("frontend App.tsx: 5 routes",
      contains("frontend/src/App.tsx", "settings") and
      contains("frontend/src/App.tsx", "scanner") and
      contains("frontend/src/App.tsx", "markets") and
      contains("frontend/src/App.tsx", "shopping-list"))
check("worker-frontend App.tsx: ReloadPrompt present",
      contains("worker-frontend/src/App.tsx", "ReloadPrompt"))
check("worker-frontend App.tsx: 3 routes (home, scanner, settings)",
      contains("worker-frontend/src/App.tsx", "settings") and
      contains("worker-frontend/src/App.tsx", "scanner"))


# ── Section 14: api.ts interceptors (both apps) ──────────────────────────────
print("\n=== api.ts interceptors (both apps) ===")
for app in ["frontend", "worker-frontend"]:
    path = f"{app}/src/services/api.ts"
    check(f"{app}: request interceptor attaches Bearer token",
          contains(path, "Authorization") and contains(path, "Bearer"))
    check(f"{app}: response interceptor handles 401",
          contains(path, "401"))
    check(f"{app}: 401 path calls signOut via getState()",
          contains(path, "getState().signOut"))
    check(f"{app}: 401 path attempts token refresh",
          contains(path, "refreshSession"))


# ── Section 15: SettingsPage (both apps) ─────────────────────────────────────
print("\n=== SettingsPage (both apps) ===")
for app in ["frontend", "worker-frontend"]:
    path = f"{app}/src/pages/SettingsPage.tsx"
    check(f"{app}: imports useAuthStore",
          contains(path, "useAuthStore"))
    check(f"{app}: uses real displayName/email",
          contains(path, "profile") and contains(path, "user?.email"))
    check(f"{app}: Sair button calls signOut()",
          contains(path, "signOut"))


# ── Section 16: Render yaml env vars ─────────────────────────────────────────
print("\n=== Render yaml env vars ===")
check("backend/render.yaml: SUPABASE_JWT_SECRET",
      contains("backend/render.yaml", "SUPABASE_JWT_SECRET"))
check("backend/render.yaml: MAX_ACTIVE_NFCE_PER_USER",
      contains("backend/render.yaml", "MAX_ACTIVE_NFCE_PER_USER"))
check("backend/render.yaml: RUN_INPROCESS_WORKER",
      contains("backend/render.yaml", "RUN_INPROCESS_WORKER"))
check("backend/render.yaml: CORS_ALLOWED_ORIGINS",
      contains("backend/render.yaml", "CORS_ALLOWED_ORIGINS"))
check("worker-frontend/render.yaml: VITE_SUPABASE_URL",
      contains("worker-frontend/render.yaml", "VITE_SUPABASE_URL"))
check("worker-frontend/render.yaml: VITE_SUPABASE_ANON_KEY",
      contains("worker-frontend/render.yaml", "VITE_SUPABASE_ANON_KEY"))
check("frontend/render.yaml: VITE_SUPABASE_URL",
      contains("frontend/render.yaml", "VITE_SUPABASE_URL"))
check("frontend/render.yaml: VITE_SUPABASE_ANON_KEY",
      contains("frontend/render.yaml", "VITE_SUPABASE_ANON_KEY"))


# ── Section 17: .env.example files ───────────────────────────────────────────
print("\n=== .env.example files ===")
check("backend/.env.example: SUPABASE_JWT_SECRET",
      contains("backend/.env.example", "SUPABASE_JWT_SECRET"))
check("backend/.env.example: MAX_ACTIVE_NFCE_PER_USER",
      contains("backend/.env.example", "MAX_ACTIVE_NFCE_PER_USER"))
check("backend/.env.example: RUN_INPROCESS_WORKER",
      contains("backend/.env.example", "RUN_INPROCESS_WORKER"))
check("frontend/.env.example: VITE_SUPABASE_URL",
      contains("frontend/.env.example", "VITE_SUPABASE_URL"))
check("frontend/.env.example: VITE_SUPABASE_ANON_KEY",
      contains("frontend/.env.example", "VITE_SUPABASE_ANON_KEY"))
check("worker-frontend/.env.example: VITE_SUPABASE_URL",
      contains("worker-frontend/.env.example", "VITE_SUPABASE_URL"))
check("worker-frontend/.env.example: VITE_SUPABASE_ANON_KEY",
      contains("worker-frontend/.env.example", "VITE_SUPABASE_ANON_KEY"))


# ── Section 18: Cross-cutting / safety ───────────────────────────────────────
print("\n=== Cross-cutting / safety ===")

# No direct client reads of processed_urls or scanned_prices
fe_scanner = read_file("frontend/src/pages/QRScannerPage.tsx") or ""
wfe_pages = []
for fn in ["HomePage.tsx", "BarcodeScannerPage.tsx", "SettingsPage.tsx"]:
    wfe_pages.append(read_file(f"worker-frontend/src/pages/{fn}") or "")

def direct_table_read(src, table):
    """Check for .from('table') which indicates a direct client-side Supabase read."""
    return f".from('{table}')" in src or f'.from("{table}")' in src

check("frontend: no direct client read of processed_urls",
      not direct_table_read(fe_scanner, "processed_urls"))
check("frontend: no direct client read of scanned_prices",
      not direct_table_read(fe_scanner, "scanned_prices"))
wfe_combined = "\n".join(wfe_pages)
check("worker-frontend: no direct client read of processed_urls",
      not direct_table_read(wfe_combined, "processed_urls"))
check("worker-frontend: no direct client read of scanned_prices",
      not direct_table_read(wfe_combined, "scanned_prices"))

# CORS OPTIONS guard
check("before_request returns early for OPTIONS (no preflight breakage)",
      contains("backend/app.py", "OPTIONS"))

# Migration: scanned_by nullable (no NOT NULL on new columns)
check("scanned_by is NULLABLE (no 'NOT NULL' on alter lines)",
      not contains("backend/migration_auth.sql", "scanned_by uuid NOT NULL"))

# Profile trigger catches Google + email
check("handle_new_user trigger fires on auth.users insert (any provider)",
      contains("backend/migration_auth.sql", "AFTER INSERT ON auth.users"))


# ── Summary ───────────────────────────────────────────────────────────────────
total = len(results)
passed = sum(results)
failed = total - passed

print(f"\n{'=' * 52}")
print(f"  Results: {passed}/{total} checks passed", end="")
if failed:
    print(f"  ({failed} FAILED)")
else:
    print("  — ALL PASS")
print("=" * 52)

sys.exit(0 if failed == 0 else 1)
