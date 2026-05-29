"""
Standalone NFCe extraction worker for use as a separate Render Background Worker.

Usage:
    RUN_INPROCESS_WORKER=false python nfce_worker.py

When deployed as a separate service, set RUN_INPROCESS_WORKER=false on the
web service so the API only enqueues to processed_urls and this worker drains it.
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone

# Ensure backend/ is in path when run directly
sys.path.insert(0, os.path.dirname(__file__))

from supabase_client import supabase
from constants import ACTIVE_NFCE_STATUSES

POLL_INTERVAL_SECONDS = int(os.getenv('WORKER_POLL_INTERVAL', '5'))
STALE_AGE_SECONDS = 120


def _utcnow():
    return datetime.now(timezone.utc)


def drain_queue():
    """Pick up queued/stale tasks from processed_urls and process them."""
    from app import process_nfce_in_background

    cutoff = (_utcnow() - timedelta(seconds=STALE_AGE_SECONDS)).isoformat()
    result = supabase.table('processed_urls') \
        .select('id, nfce_url') \
        .in_('status', ['queued', 'processing']) \
        .lt('processed_at', cutoff) \
        .execute()

    if result.data:
        print(f"[WORKER] Processing {len(result.data)} queued tasks")
        for record in result.data:
            try:
                process_nfce_in_background(record['nfce_url'], record['id'])
            except Exception as e:
                print(f"[WORKER] Error processing record #{record['id']}: {e}")
    else:
        print("[WORKER] No tasks pending")


if __name__ == '__main__':
    print("[WORKER] economiX NFCe worker started")
    print(f"[WORKER] Polling every {POLL_INTERVAL_SECONDS}s")
    while True:
        try:
            drain_queue()
        except Exception as e:
            print(f"[WORKER] Unexpected error: {e}")
        time.sleep(POLL_INTERVAL_SECONDS)
