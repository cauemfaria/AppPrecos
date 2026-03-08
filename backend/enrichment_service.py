import os
import time
import requests
import difflib
from datetime import datetime, timezone
from supabase import create_client

# Load environment variables (just in case, though they should be loaded by the caller)
from dotenv import load_dotenv
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Bluesoft Cosmos API configuration
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
        return False, None, None, None, 0, "GTIN inválido"
    
    if not COSMOS_TOKENS:
        return False, None, None, None, 0, "Nenhum token do Cosmos disponível"

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
                print(f"  [COSMOS] Encontrado: \"{product_name}\" [{brand_name}] para GTIN {gtin} ({execution_time_ms}ms)")
                return True, product_name, brand_name, image_url, execution_time_ms, None
                
            elif response.status_code == 429:
                print(f"  [COSMOS] Limite excedido para o token de índice {_current_cosmos_token_idx}. Rotacionando...")
                _current_cosmos_token_idx = (_current_cosmos_token_idx + 1) % len(COSMOS_TOKENS)
                # After rotating, the next loop iteration will try the next token
                continue
                
            elif response.status_code == 404:
                print(f"  [COSMOS] Produto {gtin} não encontrado (404)")
                return False, None, None, None, execution_time_ms, "Produto não encontrado"
                
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"  [COSMOS] Erro: {error_msg} para GTIN {gtin}")
                return False, None, None, None, execution_time_ms, error_msg
                
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            print(f"  [COSMOS] Erro na Requisição: {e}")
            return False, None, None, None, execution_time_ms, str(e)
            
    return False, None, None, None, 0, "TOKENS_EXHAUSTED"


def search_product_on_cosmos(query, ncm_filter=None):
    """
    Search for a product on Cosmos API by its description.
    Prioritizes results that match the provided NCM.
    
    Returns:
        tuple: (success, product_name, gtin, brand_name, image_url, execution_time_ms, error_msg)
    """
    global _current_cosmos_token_idx
    
    if not query or len(query.strip()) < 3:
        return False, None, None, None, None, 0, "Busca muito curta"
        
    if not COSMOS_TOKENS:
        return False, None, None, None, None, 0, "Nenhum token do Cosmos disponível"

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
                    return False, None, None, None, None, execution_time_ms, "Nenhum produto encontrado"
                
                # NCM-Aware Matching Logic with Fuzzy String Similarity
                selected_product = None
                
                # Candidates for matching
                candidates = []
                if ncm_filter:
                    # Filter by exact NCM match
                    candidates = [p for p in products if p.get('ncm', {}).get('code') == ncm_filter]
                    if not candidates:
                        print(f"  [COSMOS-SEARCH] Nenhum match de NCM para '{query}'.")
                        return False, None, None, None, None, execution_time_ms, "Nenhum match de NCM encontrado"
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
                return False, None, None, None, None, execution_time_ms, error_msg
                
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            print(f"  [COSMOS-SEARCH] Request Error: {e}")
            return False, None, None, None, None, execution_time_ms, str(e)
            
    return False, None, None, None, None, 0, "TOKENS_EXHAUSTED"


# Enrichment Lock Configuration (uses dedicated system_locks table)
ENRICHMENT_LOCK_NAME = 'enrichment_worker'
STALE_ENRICHMENT_LOCK_SECONDS = 600  # 10 minutes

def acquire_enrichment_lock(worker_id="default", max_retries=15):
    """
    Try to acquire enrichment lock using the system_locks table.
    Retries with jitter to handle high-frequency submissions.
    """
    import random
    
    for attempt in range(max_retries):
        try:
            lock_record = supabase.table('system_locks').select('*').eq('lock_name', ENRICHMENT_LOCK_NAME).execute()
            
            now = datetime.utcnow().isoformat()
            
            if not lock_record.data:
                try:
                    supabase.table('system_locks').insert({
                        'lock_name': ENRICHMENT_LOCK_NAME,
                        'status': 'locked',
                        'locked_by': worker_id,
                        'locked_at': now,
                        'updated_at': now
                    }).execute()
                    return True
                except:
                    pass
            else:
                record = lock_record.data[0]
                
                if record['status'] == 'locked':
                    locked_at_str = record.get('locked_at') or record.get('updated_at', now)
                    if isinstance(locked_at_str, str):
                        if locked_at_str.endswith('Z'):
                            locked_at_str = locked_at_str[:-1] + '+00:00'
                        elif '+' not in locked_at_str and '-' not in locked_at_str[-6:]:
                            locked_at_str = locked_at_str + '+00:00'
                    
                        locked_at = datetime.fromisoformat(locked_at_str)
                        if locked_at.tzinfo is None:
                            locked_at = locked_at.replace(tzinfo=timezone.utc)
                        
                        age_seconds = (datetime.now(timezone.utc) - locked_at).total_seconds()
                    else:
                        age_seconds = STALE_ENRICHMENT_LOCK_SECONDS + 1
                    
                    if age_seconds < STALE_ENRICHMENT_LOCK_SECONDS:
                        if attempt < max_retries - 1:
                            wait_time = 2 + (random.random() * 8)
                            print(f"[LOCK] Enrichment locked by {record.get('locked_by', 'unknown')}. Attempt {attempt+1}/{max_retries}. Retrying in {wait_time:.1f}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            return False
                    
                    print(f"[LOCK] Enrichment lock is stale ({age_seconds:.0f}s), breaking it.")
                
                result = supabase.table('system_locks').update({
                    'status': 'locked',
                    'locked_by': worker_id,
                    'locked_at': now,
                    'updated_at': now
                }).eq('lock_name', ENRICHMENT_LOCK_NAME).execute()
                
                if len(result.data) > 0:
                    return True

        except Exception as e:
            print(f"[LOCK] Error in acquire_enrichment_lock (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return False
                
    return False

def release_enrichment_lock():
    """Release the enrichment lock"""
    try:
        supabase.table('system_locks').update({
            'status': 'idle',
            'locked_by': None,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('lock_name', ENRICHMENT_LOCK_NAME).execute()
        print("[LOCK] Enrichment lock released.")
    except Exception as e:
        print(f"[LOCK] Error releasing enrichment lock: {e}")

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
