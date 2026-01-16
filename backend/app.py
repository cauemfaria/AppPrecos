"""
AppPrecos Backend API
3-Table Architecture: markets, purchases, unique_products
Using Supabase REST API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import string
import random
import sys
import threading
import time
import requests
import difflib
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
# Bluesoft Cosmos API - Get product name from GTIN/EAN
# ============================================================================
COSMOS_TOKENS = os.getenv('COSMOS_TOKENS', '').split(',') if os.getenv('COSMOS_TOKENS') else []
COSMOS_USER_AGENT = os.getenv('COSMOS_USER_AGENT', 'Cosmos-API-Request')
_current_cosmos_token_idx = 0

def get_product_from_cosmos(gtin):
    """
    Query Bluesoft Cosmos API to get product name from GTIN/EAN barcode.
    Handles multiple tokens and 429 rate limits.
    
    Returns:
        tuple: (success, product_name, brand_name, image_url, execution_time_ms, error_msg)
    """
    global _current_cosmos_token_idx
    
    if not gtin or gtin == 'SEM GTIN' or len(gtin) < 8:
        return False, None, None, None, 0, "Invalid GTIN"
    
    if not COSMOS_TOKENS:
        return False, None, None, None, 0, "No Cosmos tokens available"

    start_time = time.time()
    
    # Try each available token if we hit 429
    tokens_to_try = len(COSMOS_TOKENS)
    
    for _ in range(tokens_to_try):
        token = COSMOS_TOKENS[_current_cosmos_token_idx].strip()
        url = f"https://api.cosmos.bluesoft.com.br/gtins/{gtin}.json"
        headers = {
            "X-Cosmos-Token": token,
            "User-Agent": COSMOS_USER_AGENT,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                product_name = data.get('description')
                brand_name = data.get('brand', {}).get('name')
                image_url = data.get('thumbnail')
                print(f"  [COSMOS] Found: \"{product_name}\" [{brand_name}] for GTIN {gtin} ({execution_time_ms}ms)")
                return True, product_name, brand_name, image_url, execution_time_ms, None
                
            elif response.status_code == 429:
                print(f"  [COSMOS] Limit exceeded for token index {_current_cosmos_token_idx}. Rotating...")
                _current_cosmos_token_idx = (_current_cosmos_token_idx + 1) % len(COSMOS_TOKENS)
                # After rotating, the next loop iteration will try the next token
                continue
                
            elif response.status_code == 404:
                print(f"  [COSMOS] Product {gtin} not found (404)")
                return False, None, None, execution_time_ms, "Product not found"
                
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"  [COSMOS] Error: {error_msg} for GTIN {gtin}")
                return False, None, None, execution_time_ms, error_msg
                
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            print(f"  [COSMOS] Request Error: {e}")
            return False, None, None, execution_time_ms, str(e)
            
    return False, None, None, 0, "TOKENS_EXHAUSTED"


def search_product_on_cosmos(query, ncm_filter=None):
    """
    Search for a product on Cosmos API by its description.
    Prioritizes results that match the provided NCM.
    
    Returns:
        tuple: (success, product_name, gtin, brand_name, image_url, execution_time_ms, error_msg)
    """
    global _current_cosmos_token_idx
    
    if not query or len(query.strip()) < 3:
        return False, None, None, None, None, 0, "Query too short"
        
    if not COSMOS_TOKENS:
        return False, None, None, None, None, 0, "No Cosmos tokens available"

    start_time = time.time()
    tokens_to_try = len(COSMOS_TOKENS)
    
    for _ in range(tokens_to_try):
        token = COSMOS_TOKENS[_current_cosmos_token_idx].strip()
        url = "https://api.cosmos.bluesoft.com.br/products"
        params = {"query": query}
        headers = {
            "X-Cosmos-Token": token,
            "User-Agent": COSMOS_USER_AGENT,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                if not products:
                    return False, None, None, None, execution_time_ms, "No products found"
                
                # NCM-Aware Matching Logic with Fuzzy String Similarity
                selected_product = None
                
                # Candidates for matching
                candidates = []
                if ncm_filter:
                    # Filter by exact NCM match
                    candidates = [p for p in products if p.get('ncm', {}).get('code') == ncm_filter]
                    if not candidates:
                        print(f"  [COSMOS-SEARCH] No NCM match for '{query}'. Moving to backlog for accuracy.")
                        return False, None, None, None, execution_time_ms, "No NCM match found"
                else:
                    candidates = products

                # Find the best match among candidates using string similarity
                best_score = -1
                
                for candidate in candidates:
                    candidate_name = candidate.get('description', '')
                    # Calculate similarity ratio (0.0 to 1.0)
                    score = difflib.SequenceMatcher(None, query.upper(), candidate_name.upper()).ratio()
                    
                    if score > best_score:
                        best_score = score
                        selected_product = candidate
                
                # Minimum threshold to avoid weak matches (e.g. 0.8 or 80%)
                SIMILARITY_THRESHOLD = 0.8
                
                if selected_product and best_score >= SIMILARITY_THRESHOLD:
                    print(f"  [COSMOS-SEARCH] Best match for '{query}' (score: {best_score:.2f}): {selected_product.get('description')}")
                    return (
                        True, 
                        selected_product.get('description'), 
                        selected_product.get('gtin'),
                        selected_product.get('brand', {}).get('name'),
                        selected_product.get('thumbnail'),
                        execution_time_ms, 
                        None
                    )
                else:
                    print(f"  [COSMOS-SEARCH] No confident match for '{query}' (best score: {best_score:.2f}).")
                    return False, None, None, None, None, execution_time_ms, "No confident similarity match"
                
            elif response.status_code == 429:
                print(f"  [COSMOS-SEARCH] Limit exceeded for token index {_current_cosmos_token_idx}. Rotating...")
                _current_cosmos_token_idx = (_current_cosmos_token_idx + 1) % len(COSMOS_TOKENS)
                continue
                
            else:
                error_msg = f"HTTP {response.status_code}"
                return False, None, None, None, execution_time_ms, error_msg
                
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            print(f"  [COSMOS-SEARCH] Request Error: {e}")
            return False, None, None, None, execution_time_ms, str(e)
            
    return False, None, None, None, 0, "TOKENS_EXHAUSTED"


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
            from datetime import datetime, timezone
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


# ==================== UTILITY FUNCTIONS ====================

def generate_market_id():
    """Generate a random unique market ID (format: MKT + 8 random chars)"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"MKT{random_part}"


def log_product_lookup(nfce_url, market_id, gtin, ncm, original_name, final_name,
                       cosmos_result=None, source_used=None, success=False):
    """
    Log detailed product lookup to Supabase product_lookup_log table.
    """
    try:
        log_data = {
            'nfce_url': nfce_url,
            'market_id': market_id,
            'gtin': gtin if gtin != 'SEM GTIN' else None,
            'ncm': ncm,
            'original_name': original_name[:500] if original_name else None,
            'final_name': final_name[:500] if final_name else None,
            'source_used': source_used,
            'success': success,
        }
        
        # Bluesoft Cosmos details (generic api columns)
        if cosmos_result:
            log_data.update({
                'api_attempted': True,
                'api_success': cosmos_result.get('success', False),
                'api_product_name': cosmos_result.get('product_name'),
                'api_brand': cosmos_result.get('brand'),
                'api_image_url': cosmos_result.get('image_url'), # New field
                'api_error': cosmos_result.get('error'),
                'api_from_cache': False,
                'api_time_ms': cosmos_result.get('time_ms'),
            })
        
        # We use a try-except here because the column might not exist yet
        try:
            supabase.table('product_lookup_log').insert(log_data).execute()
        except Exception as insert_error:
            # If it failed, maybe it's the new column. Try without it.
            if 'api_image_url' in log_data:
                del log_data['api_image_url']
                supabase.table('product_lookup_log').insert(log_data).execute()
            else:
                raise insert_error
        
    except Exception as e:
        # Don't fail the main process if logging fails
        print(f"  [WARN] Failed to log product lookup: {e}")


def process_nfce_in_background(url, url_record_id):
    """Background task to process NFCe extraction and save to database"""
    start_time = time.time()
    
    print(f"\n[BACKGROUND #{url_record_id}] Queued for processing...")
    print(f"[BACKGROUND #{url_record_id}] Waiting for extraction slot (database lock)...")
    
    # Acquire database-based lock (works across Gunicorn workers)
    if not acquire_extraction_lock(url_record_id, max_wait_seconds=600):
        # Timeout - mark as error
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
        result = extract_full_nfce_data(url, headless=True)
        extraction_time = time.time() - extraction_start
        print(f"[BACKGROUND #{url_record_id}] Playwright extraction completed in {extraction_time:.1f}s")
        
        market_info = result.get('market_info', {})
        products = result.get('products', [])
        
        if not products or not market_info.get('name') or not market_info.get('address'):
            release_extraction_lock(url_record_id, 'error',
                error_message='No products or market info extracted'
            )
            print(f"[FAIL] [BACKGROUND #{url_record_id}] No products or market info extracted")
            return
        
        print(f"[BACKGROUND #{url_record_id}] Extracted {len(products)} products from {market_info.get('name')}")
        
        # Check/create market
        print(f"[BACKGROUND #{url_record_id}] Checking/creating market...")
        market_result = supabase.table('markets').select('*').match({
            'name': market_info['name'],
            'address': market_info['address']
        }).execute()
        
        if market_result.data:
            market = market_result.data[0]
            print(f"[BACKGROUND #{url_record_id}] Found existing market: {market['market_id']}")
        else:
            new_market_id = generate_market_id()
            while True:
                check = supabase.table('markets').select('id').eq('market_id', new_market_id).execute()
                if not check.data:
                    break
                new_market_id = generate_market_id()
            
            market_data = {
                'market_id': new_market_id,
                'name': market_info['name'],
                'address': market_info['address']
            }
            market_insert = supabase.table('markets').insert(market_data).execute()
            market = market_insert.data[0]
            print(f"[BACKGROUND #{url_record_id}] Created new market: {market['market_id']}")
        
        # Save products
        print(f"[BACKGROUND #{url_record_id}] Saving {len(products)} products...")
        save_result = save_products_to_supabase(market['market_id'], products, url)
        
        # Update URL record with success (this also releases the lock)
        release_extraction_lock(url_record_id, 'success',
            market_id=market['market_id'],
            market_name=market['name'],
            products_count=len(products)
        )
        
        total_time = time.time() - start_time
        print(f"[OK] [BACKGROUND #{url_record_id}] Complete in {total_time:.1f}s: {save_result['saved_to_purchases']} products saved")
        
    except Exception as e:
        # Release lock with error status
        release_extraction_lock(url_record_id, 'error',
            error_message=str(e)[:200]
        )
        total_time = time.time() - start_time
        print(f"[FAIL] [BACKGROUND #{url_record_id}] Error after {total_time:.1f}s: {e}")
        import traceback
        traceback.print_exc()


def save_products_to_supabase(market_id, products, nfce_url, purchase_date=None):
    """
    Save products to Supabase PostgreSQL database (PURCHASES table only)
    Enrichment and unique_products upsert is now handled by a separate worker.
    """
    if purchase_date is None:
        purchase_date = datetime.utcnow()
    
    inserted_purchase_ids = []
    
    try:
        saved_to_purchases = 0
        
        print(f"\n{'='*60}")
        print(f"SAVING PRODUCTS TO PURCHASES")
        print(f"{'='*60}")
        print(f"Market ID: {market_id}")
        print(f"Products count: {len(products)}")
        print(f"{'='*60}\n")
        
        # 1. Insert to PURCHASES table
        print(f"Inserting {len(products)} products to PURCHASES table...")
        
        for idx, product in enumerate(products, 1):
            try:
                purchase_data = {
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
                }
                
                response = supabase.table('purchases').insert(purchase_data).execute()
                
                if not response.data or len(response.data) == 0:
                    raise Exception(f"Failed to insert product {idx}")
                
                inserted_purchase_ids.append(response.data[0]['id'])
                saved_to_purchases += 1
                print(f"  [+] [{idx}/{len(products)}] {product.get('product', 'Unknown')[:50]}")
                
            except Exception as e:
                print(f"[ERROR] Inserting product {idx}: {str(e)}")
                raise Exception(f"Failed at product {idx}: {str(e)}")
        
        print(f"[OK] Inserted {saved_to_purchases} products to PURCHASES\n")
        
        return {
            'saved_to_purchases': saved_to_purchases,
            'updated_unique': 0,
            'created_unique': 0,
            'skipped_products': 0,
            'llm_calls': 0
        }
    
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[ERROR] TRANSACTION FAILED - ROLLING BACK")
        print(f"{'='*60}")
        
        if inserted_purchase_ids:
            try:
                for purchase_id in inserted_purchase_ids:
                    supabase.table('purchases').delete().eq('id', purchase_id).execute()
                print(f"[OK] Rolled back purchases")
            except Exception as rb_error:
                print(f"[FAIL] Rollback purchases failed: {rb_error}")
        
        print(f"{'='*60}\n")
        raise


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
            return jsonify({'error': 'Market not found'}), 404
        
        products_result = supabase.table('unique_products').select('*').eq('market_id', market_id).execute()
        
        return jsonify({
            'market': market_result.data[0],
            'products': products_result.data,
            'total': len(products_result.data)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch products: {e}'}), 500


@app.route('/api/nfce/extract', methods=['POST'])
def extract_nfce():
    """
    Extract data from NFCe URL and save to database
    Request body: { "url": "...", "save": true/false, "async": true/false }
    """
    data = request.get_json()
    
    if not data.get('url'):
        return jsonify({'error': 'NFCe URL is required'}), 400
    
    # Force use_async to True for better stability, or respect data if provided
    use_async = data.get('async', True)
    
    # ========== ASYNC MODE ==========
    if data.get('save') and use_async:
        try:
            # Check if URL already processed
            existing_url = supabase.table('processed_urls').select('*').eq('nfce_url', data['url']).execute()
            if existing_url.data:
                url_data = existing_url.data[0]
                return jsonify({
                    'error': 'This NFCe has already been processed',
                    'message': 'URL already exists in database',
                    'status': url_data.get('status', 'unknown'),
                    'processed_at': url_data['processed_at'],
                    'market_id': url_data['market_id'],
                    'products_count': url_data['products_count']
                }), 409
            
            # Record URL with status='processing'
            temp_url_data = {
                'nfce_url': data['url'],
                'market_id': 'PROCESSING',
                'market_name': '',
                'products_count': 0,
                'status': 'processing',
                'processed_at': datetime.utcnow().isoformat()
            }
            url_insert = supabase.table('processed_urls').insert(temp_url_data).execute()
            url_record_id = url_insert.data[0]['id']
            
            # Start background processing
            thread = threading.Thread(
                target=process_nfce_in_background,
                args=(data['url'], url_record_id),
                daemon=True
            )
            thread.start()
            
            return jsonify({
                'message': 'NFCe processing started',
                'status': 'processing',
                'record_id': url_record_id
            }), 202
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to start processing: {str(e)}'}), 500
    
    # ========== SYNC MODE (Legacy/Fallback) ==========
        url_record_id = None
        try:
            if data.get('save'):
                existing_url = supabase.table('processed_urls').select('*').eq('nfce_url', data['url']).execute()
                if existing_url.data:
                    url_data = existing_url.data[0]
                    return jsonify({
                        'error': 'This NFCe has already been processed',
                        'message': 'URL already exists in database',
                        'status': url_data.get('status', 'unknown'),
                        'processed_at': url_data['processed_at'],
                        'market_id': url_data['market_id'],
                        'products_count': url_data['products_count']
                    }), 409
                
                temp_url_data = {
                    'nfce_url': data['url'],
                    'market_id': 'PROCESSING',
                'market_name': '',
                    'products_count': 0,
                    'status': 'processing',
                    'processed_at': datetime.utcnow().isoformat()
                }
                url_insert = supabase.table('processed_urls').insert(temp_url_data).execute()
                url_record_id = url_insert.data[0]['id']
            
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from nfce_extractor import extract_full_nfce_data
            
            result = extract_full_nfce_data(data['url'], headless=True)
            
            market_info = result.get('market_info', {})
            products = result.get('products', [])
            
            if not products:
                if url_record_id:
                    supabase.table('processed_urls').update({'status': 'error'}).eq('id', url_record_id).execute()
                return jsonify({'error': 'No products extracted from NFCe'}), 400
            
            if data.get('save'):
                if not market_info.get('name') or not market_info.get('address'):
                    if url_record_id:
                        supabase.table('processed_urls').update({'status': 'error'}).eq('id', url_record_id).execute()
                    return jsonify({'error': 'Could not extract market information'}), 400
                
                market_result = supabase.table('markets').select('*').match({
                    'name': market_info['name'],
                    'address': market_info['address']
                }).execute()
                
                if market_result.data:
                    market = market_result.data[0]
                    market_action = 'matched'
                else:
                    new_market_id = generate_market_id()
                    while True:
                        check = supabase.table('markets').select('id').eq('market_id', new_market_id).execute()
                        if not check.data:
                            break
                        new_market_id = generate_market_id()
                    
                    market_data = {'market_id': new_market_id, 'name': market_info['name'], 'address': market_info['address']}
                    market_insert = supabase.table('markets').insert(market_data).execute()
                    market = market_insert.data[0]
                    market_action = 'created'
                
                save_result = save_products_to_supabase(market['market_id'], products, data['url'])
                
                if url_record_id:
                    supabase.table('processed_urls').update({
                        'market_id': market['market_id'],
                        'market_name': market['name'],
                        'products_count': len(products),
                        'status': 'success'
                    }).eq('id', url_record_id).execute()
                
                return jsonify({
                    'message': 'NFCe data extracted and saved successfully',
                    'record_id': url_record_id,
                    'market': {
                        'id': market['id'],
                        'market_id': market['market_id'],
                        'name': market['name'],
                        'address': market['address'],
                        'action': market_action
                    },
                    'products': products,
                    'statistics': {
                        'products_saved_to_main': save_result['saved_to_purchases'],
                        'market_action': market_action
                    }
                }), 201
            else:
                return jsonify({
                    'message': 'NFCe data extracted successfully (not saved)',
                    'market_info': market_info,
                    'products': products
                }), 200
            
        except Exception as e:
            if url_record_id:
                supabase.table('processed_urls').update({'status': 'error'}).eq('id', url_record_id).execute()
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500


@app.route('/api/nfce/status/<int:record_id>', methods=['GET'])
def get_nfce_status(record_id):
    """Get processing status by record ID"""
    try:
        result = supabase.table('processed_urls').select('*').eq('id', record_id).execute()
        
        if not result.data:
            return jsonify({'error': 'Record not found'}), 404
        
        record = result.data[0]
        return jsonify({
            'record_id': record['id'],
            'status': record['status'],
            'market_id': record.get('market_id'),
            'market_name': record.get('market_name', ''),
            'products_count': record.get('products_count', 0),
            'error_message': record.get('error_message'),
            'processed_at': record['processed_at']
        })
    except Exception as e:
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
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
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
        return jsonify({'error': 'At least one product is required'}), 400
    if not market_ids:
        return jsonify({'error': 'At least one market is required'}), 400
    
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


if __name__ == '__main__':
    import io
    
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "=" * 50)
    print(" AppPrecos Backend API")
    print("=" * 50)
    print("\n Server: http://localhost:5000")
    print(" Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
