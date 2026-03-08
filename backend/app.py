"""
AppPrecos Backend API
3-Table Architecture: markets, purchases, unique_products
Using Supabase REST API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs, unquote
import os
import sys
import threading
import time
import requests
from dotenv import load_dotenv
from supabase import create_client

# Database-based lock for extraction (works across Gunicorn workers)
# We use the processed_urls table status='extracting' as the lock

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Validate required environment variables
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Enable CORS for Android app
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Get Supabase admin client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("[OK] Supabase client initialized")

# ============================================================================
# NFCe URL Resolution - Get final browser URL after redirect
# ============================================================================
def resolve_nfce_url(url: str) -> str:
    """
    Resolve NFCe URL to its final browser URL by following redirects.
    
    QR code URLs redirect to browser URLs:
    - Input:  https://www.nfce.fazenda.sp.gov.br/qrcode?p=...
    - Output: https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=...
    
    This ensures consistent URL storage and duplicate detection.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print(f"[WARN] Failed to resolve NFCe URL, using original: {e}")
        return url


def _check_nfce_duplicate(raw_url: str, exclude_id: int | None = None):
    """
    3-step duplicate check for a raw QR code URL.

    Step 1: original_url = raw_url  (new records, fast)
    Step 2: nfce_url = raw_url      (records never resolved, fast)
    Step 3: resolve URL then nfce_url = resolved_url  (old records where nfce_url was overwritten)

    Returns the first matching processed_urls row dict, or None if no duplicate found.
    Each step is isolated so a failure in one doesn't prevent the others from running.
    """
    match_statuses = ['success', 'processing', 'extracting', 'queued']

    def _query(col, val):
        q = supabase.table('processed_urls') \
            .select('id, status, market_name, products_count') \
            .eq(col, val) \
            .in_('status', match_statuses)
        if exclude_id is not None:
            q = q.neq('id', exclude_id)
        result = q.limit(1).execute()
        return result.data[0] if result.data else None

    # Step 1: original_url column (may not exist on older schemas — isolated try)
    try:
        row = _query('original_url', raw_url)
        if row:
            print(f"[CHECK] Duplicate found via original_url: {raw_url}")
            return row
    except Exception as e:
        print(f"[CHECK] Step 1 (original_url) failed: {e}")

    # Step 2: nfce_url exact match
    try:
        row = _query('nfce_url', raw_url)
        if row:
            print(f"[CHECK] Duplicate found via nfce_url (exact): {raw_url}")
            return row
    except Exception as e:
        print(f"[CHECK] Step 2 (nfce_url exact) failed: {e}")

    # Step 3: resolve then compare (handles old records with overwritten nfce_url)
    try:
        resolved = resolve_nfce_url(raw_url)
        if resolved != raw_url:
            row = _query('nfce_url', resolved)
            if row:
                print(f"[CHECK] Duplicate found via resolved nfce_url: {resolved}")
                return row
    except Exception as e:
        print(f"[CHECK] Step 3 (resolve) failed: {e}")

    return None


# ============================================================================
# Enrichment Service - Product data enhancement (GTIN, Images, Names)
# ============================================================================
from enrichment_service import (
    get_product_from_cosmos,
    search_product_on_cosmos,
    log_product_lookup
)

# ============================================================================
# NFCe URL Resolution - Get final browser URL after redirect
# ============================================================================


# ============================================================================
# Database-based extraction lock (works across Gunicorn workers)
# ============================================================================
STALE_LOCK_TIMEOUT_SECONDS = 300  # 5 minutes - if lock is older than this, consider it stale

def cleanup_stale_locks():
    """Clean up any stale 'extracting' status from crashed workers"""
    try:
        # Find records stuck in 'extracting' status for too long
        # We mark them as errors so they can be retried
        stale = supabase.table('processed_urls').select('id,processed_at').eq('status', 'extracting').execute()
        
        if stale.data:
            now = datetime.now(timezone.utc)
            
            for record in stale.data:
                if record.get('processed_at'):
                    try:
                        processed_at_str = record['processed_at']
                        # Handle both timezone-aware and naive timestamps
                        if processed_at_str.endswith('Z'):
                            processed_at_str = processed_at_str[:-1] + '+00:00'
                        elif '+' not in processed_at_str and '-' not in processed_at_str[-6:]:
                            # Naive datetime - assume UTC
                            processed_at_str = processed_at_str + '+00:00'
                        
                        processed_at = datetime.fromisoformat(processed_at_str)
                        
                        # Make sure processed_at is timezone-aware
                        if processed_at.tzinfo is None:
                            processed_at = processed_at.replace(tzinfo=timezone.utc)
                        
                        age_seconds = (now - processed_at).total_seconds()
                        
                        if age_seconds > STALE_LOCK_TIMEOUT_SECONDS:
                            supabase.table('processed_urls').update({
                                'status': 'error',
                                'error_message': f'Stale lock cleaned up (stuck for {age_seconds:.0f}s)'
                            }).eq('id', record['id']).execute()
                            print(f"[LOCK] Cleaned stale lock for record #{record['id']} (age: {age_seconds:.0f}s)")
                    except Exception as e:
                        print(f"[LOCK] Error checking stale lock for record #{record.get('id')}: {e}")
    except Exception as e:
        print(f"[LOCK] Error in cleanup_stale_locks: {e}")

def acquire_extraction_lock(record_id, max_wait_seconds=600):
    """
    Try to acquire extraction lock using database.
    Returns True if lock acquired, False if timeout.
    Uses processed_urls table with status='extracting' as the lock.
    """
    start_time = time.time()
    check_interval = 2  # seconds
    stale_check_interval = 30  # Check for stale locks every 30 seconds
    last_stale_check = 0
    
    while True:
        # Periodically clean up stale locks
        elapsed = time.time() - start_time
        if elapsed - last_stale_check >= stale_check_interval:
            cleanup_stale_locks()
            last_stale_check = elapsed
        
        # Check if any other record is currently extracting
        extracting = supabase.table('processed_urls').select('id').eq('status', 'extracting').execute()
        
        if not extracting.data:
            # No one is extracting, try to claim the lock
            try:
                supabase.table('processed_urls').update({
                    'status': 'extracting',
                    'processed_at': datetime.utcnow().isoformat()  # Update timestamp for stale detection
                }).eq('id', record_id).eq('status', 'processing').execute()
                
                # Small delay to let any concurrent updates settle
                time.sleep(0.2)
                
                # CRITICAL: Verify we're the ONLY one extracting (race condition check)
                all_extracting = supabase.table('processed_urls').select('id').eq('status', 'extracting').execute()
                
                if all_extracting.data and len(all_extracting.data) == 1 and all_extracting.data[0]['id'] == record_id:
                    # We're the only one - lock acquired successfully
                    print(f"[LOCK #{record_id}] Acquired! Will query fresh data including all previous extractions")
                    return True
                elif all_extracting.data and len(all_extracting.data) > 1:
                    # Race condition! Multiple workers got the lock simultaneously
                    # Back off: revert to 'processing' and wait
                    print(f"[LOCK #{record_id}] Race condition detected ({len(all_extracting.data)} extracting), backing off...")
                    supabase.table('processed_urls').update({
                        'status': 'processing'
                    }).eq('id', record_id).execute()
                    time.sleep(check_interval + (record_id % 3))  # Jittered backoff
                    continue
                    
            except Exception as e:
                print(f"[LOCK] Error acquiring lock: {e}")
        
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed >= max_wait_seconds:
            print(f"[LOCK] Timeout waiting for lock after {elapsed:.1f}s")
            return False
        
        # Wait and retry
        print(f"[LOCK #{record_id}] Waiting... ({elapsed:.0f}s elapsed, other extraction in progress)")
        time.sleep(check_interval)

def release_extraction_lock(record_id, final_status, **kwargs):
    """Release lock by updating status to final state"""
    try:
        update_data = {'status': final_status, **kwargs}
        supabase.table('processed_urls').update(update_data).eq('id', record_id).execute()
        print(f"[LOCK #{record_id}] Released with status: {final_status}")
        if final_status == 'success':
            print(f"[LOCK #{record_id}] Database fully updated - next worker can now start and see new data")
    except Exception as e:
        print(f"[LOCK] Error releasing lock: {e}")

print(f"[OK] API URL: {SUPABASE_URL}")

# NOTE: Orphan recovery runs per-worker via gunicorn_config.py post_fork hook.
# For local dev (python app.py), recovery is triggered in __main__ below.
import task_queue


# ==================== UTILITY FUNCTIONS ====================

def extract_cnpj_from_url(url: str) -> str:
    """Extract the 14-digit CNPJ from an NFCe URL's access key (positions 7-20, 1-based)."""
    parsed = urlparse(url)
    p_value = parse_qs(parsed.query).get('p', [''])[0]
    p_decoded = unquote(p_value)
    access_key = p_decoded.split('|')[0]
    if len(access_key) != 44 or not access_key.isdigit():
        raise ValueError(f"Invalid NFCe access key: {access_key}")
    return access_key[6:20]


def trigger_enrichment(worker_id="auto"):
    """Trigger enrichment process in a background thread if not already running"""
    from enrichment_worker import process_pending_purchases
    thread = threading.Thread(
        target=process_pending_purchases,
        args=(worker_id,),
        daemon=True
    )
    thread.start()
    return True

def process_nfce_in_background(url, url_record_id):
    """Background task to process NFCe extraction and save to database.
    Called by the task_queue consumer thread (one at a time)."""
    import task_queue
    start_time = time.time()

    # Atomic claim: only proceed if still 'queued' (prevents duplicate work across workers)
    try:
        claim = supabase.table('processed_urls') \
            .update({'status': 'processing'}) \
            .eq('id', url_record_id) \
            .eq('status', 'queued') \
            .execute()
        if not claim.data:
            print(f"[BACKGROUND #{url_record_id}] Already claimed by another worker, skipping")
            return
    except Exception as claim_err:
        print(f"[BACKGROUND #{url_record_id}] Claim check failed: {claim_err}")

    # --- Pre-extraction phase (resolve URL, duplicate check) ---
    # Wrapped in try/except so any failure marks the record as error instead of leaving it stuck.
    try:
        print(f"\n[BACKGROUND #{url_record_id}] Resolving URL...")
        resolved_url = resolve_nfce_url(url)

        if resolved_url != url:
            try:
                supabase.table('processed_urls').update({
                    'nfce_url': resolved_url
                }).eq('id', url_record_id).execute()
            except Exception as update_err:
                # UNIQUE constraint violation = another record already has this resolved URL → duplicate
                err_str = str(update_err).lower()
                if 'unique' in err_str or 'duplicate' in err_str or '23505' in err_str:
                    supabase.table('processed_urls').update({
                        'status': 'error',
                        'error_message': 'Duplicado (URL resolvida já existe no banco)'
                    }).eq('id', url_record_id).execute()
                    print(f"[BACKGROUND #{url_record_id}] UNIQUE constraint on resolved URL — duplicate")
                    return
                raise

        # Backfill original_url for records inserted before the column existed
        try:
            row_check = supabase.table('processed_urls').select('original_url').eq('id', url_record_id).limit(1).execute()
            if row_check.data and not row_check.data[0].get('original_url'):
                supabase.table('processed_urls').update({'original_url': url}).eq('id', url_record_id).execute()
        except Exception as e:
            print(f"[BACKGROUND #{url_record_id}] original_url backfill skipped: {e}")

        # Post-resolve duplicate check (two different QR URLs can resolve to the same page)
        dup = _check_nfce_duplicate(resolved_url, exclude_id=url_record_id)
        if dup:
            supabase.table('processed_urls').update({
                'status': 'error',
                'error_message': 'Duplicado (URL já em processamento ou processada)'
            }).eq('id', url_record_id).execute()
            print(f"[BACKGROUND #{url_record_id}] Duplicate detected after resolve, skipping")
            return

    except Exception as pre_err:
        print(f"[FAIL] [BACKGROUND #{url_record_id}] Pre-extraction error: {pre_err}")
        import traceback
        traceback.print_exc()
        try:
            supabase.table('processed_urls').update({
                'status': 'error',
                'error_message': f'Erro na preparação: {str(pre_err)[:200]}'
            }).eq('id', url_record_id).execute()
        except Exception:
            pass
        return

    # Refresh timestamp (status already 'processing' from atomic claim above)
    supabase.table('processed_urls').update({
        'processed_at': datetime.utcnow().isoformat()
    }).eq('id', url_record_id).execute()

    print(f"[BACKGROUND #{url_record_id}] Waiting for extraction slot (database lock)...")

    if not acquire_extraction_lock(url_record_id, max_wait_seconds=1800):
        supabase.table('processed_urls').update({
            'status': 'error',
            'error_message': 'Timeout waiting for extraction slot'
        }).eq('id', url_record_id).execute()
        print(f"[FAIL] [BACKGROUND #{url_record_id}] Timeout waiting for lock")
        return

    wait_time = time.time() - start_time
    print(f"[BACKGROUND #{url_record_id}] Got extraction slot after {wait_time:.1f}s")

    try:
        print(f"[BACKGROUND #{url_record_id}] Starting Playwright extraction...")

        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from nfce_extractor import extract_full_nfce_data

        extraction_start = time.time()
        result = extract_full_nfce_data(resolved_url, headless=True)
        extraction_time = time.time() - extraction_start
        print(f"[BACKGROUND #{url_record_id}] Playwright extraction completed in {extraction_time:.1f}s")

        market_info = result.get('market_info', {})
        products = result.get('products', [])
        purchase_date_str = result.get('purchase_date')

        purchase_date = None
        if purchase_date_str:
            try:
                purchase_date = datetime.strptime(purchase_date_str, "%d/%m/%Y %H:%M:%S%z")
                print(f"[BACKGROUND #{url_record_id}] Emission date: {purchase_date.isoformat()}")
            except Exception:
                try:
                    purchase_date = datetime.strptime(purchase_date_str, "%d/%m/%Y %H:%M:%S")
                    print(f"[BACKGROUND #{url_record_id}] Emission date (no tz): {purchase_date.isoformat()}")
                except Exception as date_err:
                    print(f"[BACKGROUND #{url_record_id}] Could not parse emission date '{purchase_date_str}': {date_err}")

        if not products or not market_info.get('name') or not market_info.get('address'):
            release_extraction_lock(url_record_id, 'error',
                error_message='No products or market info extracted'
            )
            print(f"[FAIL] [BACKGROUND #{url_record_id}] No products or market info extracted")
            return

        print(f"[BACKGROUND #{url_record_id}] Extracted {len(products)} products from {market_info.get('name')}")

        cnpj = extract_cnpj_from_url(resolved_url)
        print(f"[BACKGROUND #{url_record_id}] Checking/creating market (CNPJ: {cnpj})...")
        market_result = supabase.table('markets').select('*').eq('market_id', cnpj).execute()

        if market_result.data:
            market = market_result.data[0]
            print(f"[BACKGROUND #{url_record_id}] Found existing market: {market['market_id']}")
        else:
            market_data = {
                'market_id': cnpj,
                'name': market_info['name'].title(),
                'address': market_info['address']
            }
            market_insert = supabase.table('markets').insert(market_data).execute()
            market = market_insert.data[0]
            print(f"[BACKGROUND #{url_record_id}] Created new market: {market['market_id']}")

        print(f"[BACKGROUND #{url_record_id}] Saving {len(products)} products...")
        save_result = save_products_to_supabase(market['market_id'], products, resolved_url, purchase_date=purchase_date)

        release_extraction_lock(url_record_id, 'success',
            market_id=market['market_id'],
            market_name=market['name'],
            products_count=len(products)
        )

        total_time = time.time() - start_time
        print(f"[OK] [BACKGROUND #{url_record_id}] Complete in {total_time:.1f}s: {save_result['saved_to_purchases']} products saved")

        # Only trigger enrichment when the queue is empty (last item in a batch).
        # This bunches up all products for one enrichment run, maximizing local
        # cache hits and minimizing Cosmos API calls.
        if task_queue.is_empty():
            print(f"[BACKGROUND #{url_record_id}] Queue empty, triggering enrichment...")
            trigger_enrichment(f"auto-{url_record_id}")
        else:
            print(f"[BACKGROUND #{url_record_id}] {task_queue.queue_size()} items still queued, deferring enrichment")

    except Exception as e:
        release_extraction_lock(url_record_id, 'error',
            error_message=str(e)[:200]
        )
        total_time = time.time() - start_time
        print(f"[FAIL] [BACKGROUND #{url_record_id}] Error after {total_time:.1f}s: {e}")
        import traceback
        traceback.print_exc()


def save_products_to_supabase(market_id, products, nfce_url, purchase_date=None):
    """
    Save products to Supabase PostgreSQL database (PURCHASES table only).
    Uses a single batch insert for atomicity and speed.
    """
    if purchase_date is None:
        purchase_date = datetime.utcnow()

    print(f"[SAVE] Batch inserting {len(products)} products for market {market_id}")

    all_purchase_data = []
    for product in products:
        all_purchase_data.append({
            'market_id': market_id,
            'ncm': product['ncm'],
            'ean': product.get('ean', 'SEM GTIN'),
            'product_name': product.get('product', ''),
            'quantity': product.get('quantity', 0),
            'unidade_comercial': product.get('unidade_comercial', 'UN'),
            'total_price': product.get('total_price', 0),
            'unit_price': product.get('unit_price', 0),
            'nfce_url': nfce_url,
            'purchase_date': purchase_date.isoformat(),
            'enriched': False,
            'enrichment_status': 'pending'
        })

    response = supabase.table('purchases').insert(all_purchase_data).execute()

    if not response.data or len(response.data) != len(products):
        raise Exception(f"Batch insert returned {len(response.data) if response.data else 0}/{len(products)} rows")

    print(f"[OK] Batch inserted {len(response.data)} products to PURCHASES")

    return {
        'saved_to_purchases': len(response.data),
        'updated_unique': 0,
        'created_unique': 0,
        'skipped_products': 0,
        'llm_calls': 0
    }


# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """API information endpoint"""
    return jsonify({
        'name': 'AppPrecos API',
        'status': 'running',
        'endpoints': {
            'markets': '/api/markets',
            'market_products': '/api/markets/{market_id}/products',
            'nfce_extract': '/api/nfce/extract',
            'nfce_status': '/api/nfce/status/{record_id}',
            'products_search': '/api/products/search',
            'products_compare': '/api/products/compare',
            'enrich_trigger': '/api/enrich/trigger',
            'health': '/health'
        }
    })


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        supabase.table('markets').select('id').limit(1).execute()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@app.route('/api/markets', methods=['GET'])
def get_markets():
    """Get all markets"""
    try:
        result = supabase.table('markets').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/markets/<string:market_id>/products', methods=['GET'])
def get_market_products(market_id):
    """Get unique products for a specific market"""
    try:
        market_result = supabase.table('markets').select('*').eq('market_id', market_id).execute()
        if not market_result.data:
            return jsonify({'error': 'Mercado não encontrado'}), 404
        
        products_result = supabase.table('unique_products').select('*').eq('market_id', market_id).execute()
        
        return jsonify({
            'market': market_result.data[0],
            'products': products_result.data,
            'total': len(products_result.data)
        })
    except Exception as e:
        return jsonify({'error': f'Falha ao buscar produtos: {e}'}), 500


@app.route('/api/products/price-history', methods=['GET'])
def get_product_price_history():
    """Get price history for a product by EAN + market_id (falls back to NCM if EAN missing)"""
    try:
        ean = request.args.get('ean', '').strip()
        ncm = request.args.get('ncm', '').strip()
        market_id = request.args.get('market_id', '').strip()

        query = supabase.table('purchases').select('unit_price,purchase_date')

        if ean:
            query = query.eq('ean', ean)
        elif ncm:
            query = query.eq('ncm', ncm)
        else:
            return jsonify({'error': 'ean or ncm required'}), 400

        if market_id:
            query = query.eq('market_id', market_id)

        result = query.order('purchase_date', desc=False).limit(60).execute()

        # Deduplicate to one entry per calendar day (keep last price of that day)
        seen = {}
        for row in result.data:
            day = row['purchase_date'][:10]  # YYYY-MM-DD
            seen[day] = round(row['unit_price'], 2)

        history = [{'date': d, 'price': p} for d, p in sorted(seen.items())]

        return jsonify({'history': history, 'total': len(history)})
    except Exception as e:
        return jsonify({'error': f'Falha ao buscar histórico: {e}'}), 500


@app.route('/api/nfce/extract', methods=['POST'])
def extract_nfce():
    """
    Extract data from NFCe URL and save to database
    Request body: { "url": "...", "save": true/false, "async": true/false }
    """
    import task_queue

    data = request.get_json()

    if not data.get('url'):
        return jsonify({'error': 'URL da NFCe é obrigatória'}), 400

    raw_url = data['url'].strip()

    try:
        # 3-step duplicate check: original_url → nfce_url → resolve then nfce_url
        dup = _check_nfce_duplicate(raw_url)
        if dup:
            return jsonify({
                'error': 'Esta NFCe já foi processada',
                'message': 'A URL já existe no banco de dados',
                'status': dup.get('status', 'unknown'),
                'market_name': dup.get('market_name', ''),
                'products_count': dup.get('products_count', 0),
            }), 409

        # Insert with status='queued' and return immediately.
        # URL resolution and extraction happen in the background worker.
        temp_url_data = {
            'nfce_url': raw_url,
            'original_url': raw_url,
            'market_id': 'QUEUED',
            'market_name': '',
            'products_count': 0,
            'status': 'queued',
            'processed_at': datetime.utcnow().isoformat()
        }
        try:
            url_insert = supabase.table('processed_urls').insert(temp_url_data).execute()
        except Exception:
            # Fallback: original_url column might not exist yet
            temp_url_data.pop('original_url', None)
            url_insert = supabase.table('processed_urls').insert(temp_url_data).execute()
        url_record_id = url_insert.data[0]['id']

        task_queue.enqueue_nfce(raw_url, url_record_id)

        return jsonify({
            'message': 'NFCe adicionada à fila de processamento',
            'status': 'queued',
            'record_id': url_record_id
        }), 202

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Falha ao iniciar processamento: {str(e)}'}), 500


def _format_status_record(record):
    """Format a processed_urls DB row into the API response shape."""
    return {
        'record_id': record['id'],
        'nfce_url': record.get('nfce_url', ''),
        'status': record['status'],
        'market_id': record.get('market_id'),
        'market_name': record.get('market_name', ''),
        'products_count': record.get('products_count', 0),
        'error_message': record.get('error_message'),
        'processed_at': record['processed_at']
    }


@app.route('/api/nfce/check', methods=['GET'])
def check_nfce_exists():
    """
    Check whether a raw QR code URL was already processed.
    Uses 3-step check: original_url → nfce_url → resolve then nfce_url.
    Always returns 200; never throws, to avoid blocking the scanner UI.
    """
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'exists': False}), 200

    try:
        row = _check_nfce_duplicate(url)
        if row:
            return jsonify({
                'exists': True,
                'status': row.get('status', 'unknown'),
                'market_name': row.get('market_name', ''),
                'products_count': row.get('products_count', 0),
            }), 200
        return jsonify({'exists': False}), 200
    except Exception as e:
        print(f"[CHECK] Unexpected error in check_nfce_exists: {e}")
        return jsonify({'exists': False, 'error': str(e)}), 200


@app.route('/api/nfce/status/<int:record_id>', methods=['GET'])
def get_nfce_status(record_id):
    """Get processing status by record ID"""
    try:
        result = supabase.table('processed_urls').select('*').eq('id', record_id).execute()

        if not result.data:
            return jsonify({'error': 'Registro não encontrado'}), 404

        return jsonify(_format_status_record(result.data[0]))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nfce/status/batch', methods=['POST'])
def get_nfce_status_batch():
    """Get processing status for multiple record IDs in a single query."""
    data = request.get_json()
    ids = data.get('ids', []) if data else []

    if not ids:
        return jsonify([])

    try:
        result = supabase.table('processed_urls').select('*').in_('id', ids).execute()
        return jsonify([_format_status_record(r) for r in result.data])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/nfce/processing', methods=['GET'])
def get_processing_nfces():
    """Get all currently processing NFCe URLs"""
    try:
        ten_minutes_ago = (datetime.utcnow() - timedelta(minutes=10)).isoformat()

        result = supabase.table('processed_urls')\
            .select('*')\
            .in_('status', ['queued', 'processing', 'extracting'])\
            .gt('processed_at', ten_minutes_ago)\
            .execute()

        return jsonify([_format_status_record(r) for r in result.data])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scan/save', methods=['POST'])
def save_barcode_scan():
    """Save a barcode scan from the worker app. Fast insert, no enrichment."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Corpo da requisição vazio'}), 400

    market_id = (data.get('market_id') or '').strip()
    ean = (data.get('ean') or '').strip()
    varejo_price = data.get('varejo_price')
    atacado_price = data.get('atacado_price')

    if not market_id:
        return jsonify({'error': 'market_id é obrigatório'}), 400
    if not ean:
        return jsonify({'error': 'ean é obrigatório'}), 400
    if varejo_price is None or float(varejo_price) <= 0:
        return jsonify({'error': 'varejo_price deve ser maior que zero'}), 400

    try:
        market_check = supabase.table('markets').select('market_id').eq('market_id', market_id).limit(1).execute()
        if not market_check.data:
            return jsonify({'error': 'Mercado não encontrado'}), 404

        row = {
            'market_id': market_id,
            'ean': ean,
            'varejo_price': float(varejo_price),
            'enriched': False,
            'enrichment_status': 'pending',
            'source': 'worker_scan',
        }
        if atacado_price is not None and float(atacado_price) > 0:
            row['atacado_price'] = float(atacado_price)

        result = supabase.table('scanned_prices').insert(row).execute()

        if not result.data:
            return jsonify({'error': 'Falha ao salvar escaneamento'}), 500

        return jsonify({'success': True, 'id': result.data[0]['id']}), 201

    except Exception as e:
        print(f"[ERROR] /api/scan/save: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/search', methods=['GET'])
def search_products():
    """
    Search products by name across all markets
    Query params: name (required), limit (optional, default 50)
    """
    name_query = request.args.get('name', '').strip()
    limit = min(int(request.args.get('limit', 50)), 100)
    
    if not name_query or len(name_query) < 2:
        return jsonify({'error': 'A busca deve ter pelo menos 2 caracteres'}), 400
    
    try:
        # Search unique_products by product_name (case-insensitive)
        result = supabase.table('unique_products').select(
            'id, product_name, ean, ncm, price, unidade_comercial, market_id, image_url'
        ).ilike('product_name', f'%{name_query}%').limit(limit).execute()
        
        # Group by product (ean or ncm+product_name if no ean)
        products_map = {}
        for p in result.data:
            # Use EAN as key if available, otherwise use NCM+name
            if p['ean'] and p['ean'] != 'SEM GTIN':
                key = f"ean:{p['ean']}"
            else:
                key = f"ncm:{p['ncm']}:{p['product_name']}"
            
            if key not in products_map:
                products_map[key] = {
                    'product_name': p['product_name'],
                    'ean': p['ean'],
                    'ncm': p['ncm'],
                    'unidade_comercial': p['unidade_comercial'],
                    'markets_count': 0,
                    'min_price': p['price'],
                    'max_price': p['price'],
                    'image_url': p.get('image_url')
                }
            
            products_map[key]['markets_count'] += 1
            products_map[key]['min_price'] = min(products_map[key]['min_price'], p['price'])
            products_map[key]['max_price'] = max(products_map[key]['max_price'], p['price'])
            
            # If the current entry has an image but the map entry doesn't, update it
            if not products_map[key]['image_url'] and p.get('image_url'):
                products_map[key]['image_url'] = p.get('image_url')
        
        return jsonify({
            'query': name_query,
            'results': list(products_map.values()),
            'total': len(products_map)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/enrich/trigger', methods=['POST'])
def manual_trigger_enrichment():
    """Manually trigger the product enrichment process"""
    try:
        # Note: We no longer do a manual lock check here because acquire_enrichment_lock()
        # inside the worker has built-in retry logic and handles stale locks correctly.
        # This ensures the 'Sync' button always attempts to start a worker that can 
        # break through ghost locks or wait for an active one.
        trigger_enrichment("manual-api")
        
        return jsonify({
            'message': 'Enriquecimento de produtos iniciado em segundo plano',
            'status': 'started'
        }), 202
    except Exception as e:
        print(f"[ERROR] Manual enrichment trigger failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/compare', methods=['POST'])
def compare_products():
    """
    Compare product prices across selected markets
    Request body: {
        "products": [{"ean": "...", "ncm": "...", "product_name": "..."}],
        "market_ids": ["MKT123", "MKT456"]
    }
    Returns price comparison table
    """
    data = request.get_json()
    
    products = data.get('products', [])
    market_ids = data.get('market_ids', [])
    
    if not products:
        return jsonify({'error': 'Pelo menos um produto é obrigatório'}), 400
    if not market_ids:
        return jsonify({'error': 'Pelo menos um mercado é obrigatório'}), 400
    
    try:
        # Get market info
        markets_result = supabase.table('markets').select('market_id, name').in_('market_id', market_ids).execute()
        markets_info = {m['market_id']: m['name'] for m in markets_result.data}
        
        comparison = []
        
        for product in products:
            product_row = {
                'product_name': product.get('product_name', ''),
                'ean': product.get('ean', ''),
                'ncm': product.get('ncm', ''),
                'image_url': None,
                'prices': {}
            }
            
            for market_id in market_ids:
                price = None
                
                # Try to find by EAN first (if available and not "SEM GTIN")
                if product.get('ean') and product['ean'] != 'SEM GTIN':
                    result = supabase.table('unique_products').select('price, image_url').match({
                        'market_id': market_id,
                        'ean': product['ean']
                    }).execute()
                    if result.data:
                        price = result.data[0]['price']
                        if not product_row['image_url']:
                            product_row['image_url'] = result.data[0].get('image_url')
                
                # Fallback to NCM if no EAN match
                if price is None and product.get('ncm'):
                    result = supabase.table('unique_products').select('price, product_name, image_url').match({
                        'market_id': market_id,
                        'ncm': product['ncm']
                    }).execute()
                    if result.data:
                        # If multiple products with same NCM, try to match by name
                        if len(result.data) > 1 and product.get('product_name'):
                            for r in result.data:
                                if product['product_name'].lower() in r['product_name'].lower():
                                    price = r['price']
                                    if not product_row['image_url']:
                                        product_row['image_url'] = r.get('image_url')
                                    break
                        if price is None:
                            price = result.data[0]['price']
                            if not product_row['image_url']:
                                product_row['image_url'] = result.data[0].get('image_url')
                
                product_row['prices'][market_id] = price
            
            # Calculate min/max for color coding
            valid_prices = [p for p in product_row['prices'].values() if p is not None]
            if valid_prices:
                product_row['min_price'] = min(valid_prices)
                product_row['max_price'] = max(valid_prices)
                product_row['all_equal'] = len(set(valid_prices)) == 1
            else:
                product_row['min_price'] = None
                product_row['max_price'] = None
                product_row['all_equal'] = False
            
            comparison.append(product_row)
        
        return jsonify({
            'markets': markets_info,
            'comparison': comparison
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/best-markets', methods=['POST'])
def get_best_markets_for_product():
    """
    Find the best (cheapest) markets for a single product
    Request body: {
        "product": {"ean": "...", "ncm": "...", "product_name": "..."},
        "limit": 3
    }
    Returns all markets with top 3 unique prices (handles ties)
    """
    data = request.get_json()
    
    product = data.get('product', {})
    limit = min(data.get('limit', 3), 10)  # Max 10 unique price points
    
    if not product:
        return jsonify({'error': 'Produto é obrigatório'}), 400
    
    try:
        market_prices = []
        
        # Try to find by EAN first (if available and not "SEM GTIN")
        if product.get('ean') and product['ean'] != 'SEM GTIN':
            result = supabase.table('unique_products').select(
                'market_id, price, product_name, image_url, unidade_comercial'
            ).eq('ean', product['ean']).execute()
            
            if result.data:
                for item in result.data:
                    # Get market details
                    market_result = supabase.table('markets').select('name, address').eq(
                        'market_id', item['market_id']
                    ).execute()
                    
                    if market_result.data:
                        market = market_result.data[0]
                        market_prices.append({
                            'market_id': item['market_id'],
                            'market_name': market['name'],
                            'market_address': market['address'],
                            'price': item['price'],
                            'product_name': item['product_name'],
                            'image_url': item.get('image_url'),
                            'unidade_comercial': item['unidade_comercial']
                        })
        
        # Fallback to NCM if no EAN matches found
        if not market_prices and product.get('ncm'):
            result = supabase.table('unique_products').select(
                'market_id, price, product_name, image_url, unidade_comercial'
            ).eq('ncm', product['ncm']).execute()
            
            if result.data:
                # If we have a product name, try to match it
                product_name = product.get('product_name', '').lower()
                filtered_data = result.data
                
                if product_name:
                    # Try exact match first
                    exact_matches = [
                        item for item in result.data 
                        if product_name in item['product_name'].lower()
                    ]
                    if exact_matches:
                        filtered_data = exact_matches
                
                for item in filtered_data:
                    # Get market details
                    market_result = supabase.table('markets').select('name, address').eq(
                        'market_id', item['market_id']
                    ).execute()
                    
                    if market_result.data:
                        market = market_result.data[0]
                        market_prices.append({
                            'market_id': item['market_id'],
                            'market_name': market['name'],
                            'market_address': market['address'],
                            'price': item['price'],
                            'product_name': item['product_name'],
                            'image_url': item.get('image_url'),
                            'unidade_comercial': item['unidade_comercial']
                        })
        
        if not market_prices:
            return jsonify({
                'product': product,
                'best_markets': [],
                'message': 'Produto não encontrado em nenhum mercado'
            }), 200
        
        # Sort by price (lowest first)
        market_prices.sort(key=lambda x: x['price'])
        
        # Find top N unique price points (to handle ties)
        unique_prices = sorted(set(m['price'] for m in market_prices))[:limit]
        
        # Return all markets that have any of the top N prices
        best_markets = [m for m in market_prices if m['price'] in unique_prices]
        
        return jsonify({
            'product': product,
            'best_markets': best_markets,
            'total_markets_found': len(market_prices),
            'unique_price_points': len(unique_prices)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import io
    
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    task_queue.recover_orphaned_tasks()

    print("\n" + "=" * 50)
    print(" AppPrecos Backend API")
    print("=" * 50)
    print("\n Server: http://localhost:5000")
    print(" Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
