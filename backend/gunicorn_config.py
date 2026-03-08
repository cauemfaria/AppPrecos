"""
Gunicorn production configuration for AppPrecos Backend
Optimized for multiple concurrent users
"""
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
backlog = 2048

# Worker processes - fixed at 2 to stay within Render's 512MB memory limit.
# Playwright (Chromium) uses ~200MB, so more workers would cause OOM.
workers = 2
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120  # Increased for Playwright scraping operations
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'appprecos_backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True


def post_fork(server, worker):
    """
    Reset task queue after Gunicorn fork.
    With preload_app=True, module-level code runs in the master process.
    Threads don't survive fork(), so the consumer thread must be re-created
    and orphaned tasks re-enqueued in each worker.
    """
    import task_queue
    task_queue.reset_after_fork()
    task_queue.recover_orphaned_tasks()

