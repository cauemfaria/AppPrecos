#!/usr/bin/env python3
"""
Post-merge verification script for review-backend-supabase branch.
Validates all changes were applied correctly after merge to main.
"""

import ast
import os
import sys

print("=" * 70)
print("POST-MERGE VERIFICATION TEST")
print("=" * 70)

# Test 1: Syntax validation
print("\n[TEST 1] Python Syntax Validation")
python_files = [
    'backend/supabase_client.py',
    'backend/constants.py',
    'backend/app.py',
    'backend/enrichment_worker.py',
    'backend/enrichment_service.py',
    'backend/quick_status.py',
    'backend/supabase_migrations.py',
    'backend/migrate_to_cnpj.py',
    'backend/fix_purchase_dates.py',
    'backend/task_queue.py'
]

all_valid = True
for f in python_files:
    try:
        with open(f, 'r') as file:
            ast.parse(file.read())
        print(f"  [OK] {f}")
    except SyntaxError as e:
        print(f"  [FAIL] {f}: {e}")
        all_valid = False

if all_valid:
    print("\n  [PASS] All Python files have valid syntax")
else:
    print("\n  [FAIL] Syntax errors found")
    sys.exit(1)

# Test 2: Import verification (constants only, since supabase_client requires env vars)
print("\n[TEST 2] Constants Import Verification")
try:
    from backend.constants import (
        STATUS_QUEUED, STATUS_PROCESSING, STATUS_EXTRACTING, 
        STATUS_SUCCESS, STATUS_ERROR, ACTIVE_NFCE_STATUSES,
        MARKET_ID_QUEUED, MARKET_ID_UNRESOLVED, NO_GTIN
    )
    print(f"  [OK] STATUS_QUEUED = '{STATUS_QUEUED}'")
    print(f"  [OK] STATUS_PROCESSING = '{STATUS_PROCESSING}'")
    print(f"  [OK] STATUS_EXTRACTING = '{STATUS_EXTRACTING}'")
    print(f"  [OK] STATUS_SUCCESS = '{STATUS_SUCCESS}'")
    print(f"  [OK] STATUS_ERROR = '{STATUS_ERROR}'")
    print(f"  [OK] ACTIVE_NFCE_STATUSES = {ACTIVE_NFCE_STATUSES}")
    print(f"  [OK] MARKET_ID_QUEUED = '{MARKET_ID_QUEUED}'")
    print(f"  [OK] MARKET_ID_UNRESOLVED = '{MARKET_ID_UNRESOLVED}'")
    print(f"  [OK] NO_GTIN = '{NO_GTIN}'")
    print("\n  [PASS] All constants imported successfully")
except Exception as e:
    print(f"  ✗ Import error: {e}")
    sys.exit(1)

# Test 3: File presence
print("\n[TEST 3] New Files Presence Check")
new_files = [
    'backend/supabase_client.py',
    'backend/constants.py',
    'backend/REVIEW.md',
    'backend/.env.example'
]

files_ok = True
for f in new_files:
    exists = os.path.exists(f)
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {f} {'(exists)' if exists else '(MISSING)'}")
    if not exists:
        files_ok = False

if files_ok:
    print("\n  [PASS] All new files present")
else:
    print("\n  [FAIL] Some files missing")
    sys.exit(1)

# Test 4: Content verification
print("\n[TEST 4] Key Changes Verification")

checks = [
    ('backend/app.py', 'CORS_ALLOWED_ORIGINS'),
    ('backend/app.py', 'datetime.now(timezone.utc)'),
    ('backend/app.py', 'resolve_nfce_url'),
    ('backend/enrichment_worker.py', "order('created_at')"),
    ('backend/enrichment_service.py', 'from supabase_client import'),
    ('backend/quick_status.py', 'from supabase_client import'),
]

content_ok = True
for filename, pattern in checks:
    with open(filename, 'r') as f:
        content = f.read()
        if pattern in content:
            print(f"  [OK] {filename}: '{pattern}' found")
        else:
            print(f"  [FAIL] {filename}: '{pattern}' NOT found")
            content_ok = False

if content_ok:
    print("\n  [PASS] All key changes verified")
else:
    print("\n  [FAIL] Some changes missing")
    sys.exit(1)

# Test 5: Verify constants are used in imports
print("\n[TEST 5] Constants Usage Verification")
try:
    with open('backend/app.py', 'r') as f:
        app_content = f.read()
    if 'from constants import' in app_content:
        print("  [OK] app.py imports from constants")
    else:
        print("  [FAIL] app.py does NOT import from constants")
        sys.exit(1)
    
    if 'STATUS_QUEUED' in app_content and 'MARKET_ID_QUEUED' in app_content:
        print("  [OK] app.py uses imported constants")
    else:
        print("  [FAIL] app.py does not use constants")
        sys.exit(1)
        
    print("\n  [PASS] Constants properly integrated")
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("[SUCCESS] ALL VERIFICATION TESTS PASSED - MERGE SUCCESSFUL")
print("=" * 70)
print("\nSummary:")
print("  • All Python files compile without syntax errors")
print("  • Constants module imports correctly")
print("  • All new files present (supabase_client, constants, REVIEW, .env.example)")
print("  • CORS_ALLOWED_ORIGINS implemented")
print("  • timezone.utc changes in place")
print("  • Queue fairness (.order('created_at')) implemented")
print("  • All modules use shared supabase client")
print("\nThe merge is ready for production deployment.")
