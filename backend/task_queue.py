"""
NFCe Task Queue - Single-threaded background processor.

Replaces the thread-per-request pattern with a single daemon consumer thread
and an in-process queue. This prevents thread explosion (50 threads -> 1 thread)
and keeps memory usage under the 512MB Render limit.

The database lock (acquire_extraction_lock) still coordinates across Gunicorn workers.
"""

import queue
import threading
import time
from datetime import datetime, timedelta, timezone

_task_queue = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()

STALE_RECOVERY_AGE_SECONDS = 120


def _consumer_loop():
    """Single consumer thread that processes NFCe tasks sequentially."""
    while True:
        try:
            url, record_id = _task_queue.get(block=True)
            print(f"[QUEUE] Dequeued record #{record_id}, {_task_queue.qsize()} remaining")

            from app import process_nfce_in_background
            process_nfce_in_background(url, record_id)

        except Exception as e:
            print(f"[QUEUE] Consumer error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            _task_queue.task_done()


def _ensure_worker_started():
    """Start the consumer thread once (lazy initialization)."""
    global _worker_started
    if _worker_started:
        return
    with _worker_lock:
        if _worker_started:
            return
        t = threading.Thread(target=_consumer_loop, daemon=True)
        t.start()
        _worker_started = True
        print("[QUEUE] Consumer thread started")


def reset_after_fork():
    """Reset thread state after Gunicorn fork. Threads don't survive os.fork()."""
    global _worker_started
    _worker_started = False


def enqueue_nfce(url: str, record_id: int):
    """Add an NFCe URL to the processing queue. Starts the consumer if needed."""
    _ensure_worker_started()
    _task_queue.put((url, record_id))
    print(f"[QUEUE] Enqueued record #{record_id}, queue size: {_task_queue.qsize()}")


def is_empty() -> bool:
    """Check if the task queue has no pending items."""
    return _task_queue.empty()


def queue_size() -> int:
    return _task_queue.qsize()


def recover_orphaned_tasks():
    """
    On startup, find records stuck in 'queued' or 'processing' and re-enqueue them.
    Handles items orphaned by worker restarts or crashes.
    """
    try:
        from app import supabase

        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=STALE_RECOVERY_AGE_SECONDS)).isoformat()

        result = supabase.table('processed_urls') \
            .select('id, nfce_url') \
            .in_('status', ['queued', 'processing']) \
            .lt('processed_at', cutoff) \
            .execute()

        if result.data:
            print(f"[QUEUE] Recovering {len(result.data)} orphaned tasks")
            for record in result.data:
                enqueue_nfce(record['nfce_url'], record['id'])
        else:
            print("[QUEUE] No orphaned tasks found")

    except Exception as e:
        print(f"[QUEUE] Recovery error: {e}")
