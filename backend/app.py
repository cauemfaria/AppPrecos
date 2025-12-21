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
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# Database-based lock for extraction (works across Gunicorn workers)
# We use the processed_urls table status='extracting' as the lock

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validate required environment variables
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")

if not OPENAI_API_KEY:
    print("[WARN] OPENAI_API_KEY not set - LLM product matching will be disabled")

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

# Initialize OpenAI client
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("[OK] OpenAI client initialized")
else:
    print("[WARN] OpenAI client NOT initialized (API key missing)")

print("[OK] Supabase client initialized")

# ============================================================================
# Open Food Facts API - Get product name from GTIN/EAN
# ============================================================================
OPEN_FOOD_FACTS_API = "https://world.openfoodfacts.org/api/v2/product"

def get_product_from_open_food_facts(gtin):
    """
    Query Open Food Facts API to get product name from GTIN/EAN barcode.
    
    Args:
        gtin: The barcode/EAN of the product
        
    Returns:
        tuple: (success, product_name, execution_time_ms)
        - success: True if product found, False otherwise
        - product_name: The product name from OFF, or None if not found
        - execution_time_ms: Time taken for the API call
    """
    if not gtin or gtin == 'SEM GTIN' or len(gtin) < 8:
        return False, None, 0
    
    start_time = time.time()
    
    try:
        url = f"{OPEN_FOOD_FACTS_API}/{gtin}?fields=product_name,product_name_pt,product_name_en,brands"
        
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'AppPrecos/1.0 (contact@appprecos.com)'
        })
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 1 and data.get('product'):
                product = data['product']
                
                # Try Portuguese name first, then generic, then English
                product_name = (
                    product.get('product_name_pt') or 
                    product.get('product_name') or 
                    product.get('product_name_en')
                )
                
                if product_name:
                    # Optionally append brand if available
                    brand = product.get('brands', '').split(',')[0].strip()
                    if brand and brand.lower() not in product_name.lower():
                        product_name = f"{product_name} {brand}"
                    
                    # Clean up the name
                    product_name = product_name.strip()
                    
                    print(f"  [OFF] Found: \"{product_name}\" for GTIN {gtin} ({execution_time_ms}ms)")
                    return True, product_name, execution_time_ms
        
        print(f"  [OFF] Not found: GTIN {gtin} ({execution_time_ms}ms)")
        return False, None, execution_time_ms
        
    except requests.Timeout:
        execution_time_ms = int((time.time() - start_time) * 1000)
        print(f"  [OFF] Timeout: GTIN {gtin} ({execution_time_ms}ms)")
        return False, None, execution_time_ms
            
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        print(f"  [OFF] Error: {e} for GTIN {gtin} ({execution_time_ms}ms)")
        return False, None, execution_time_ms


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
        tuple: (success, product_name, brand_name, execution_time_ms, error_msg)
    """
    global _current_cosmos_token_idx
    
    if not gtin or gtin == 'SEM GTIN' or len(gtin) < 8:
        return False, None, None, 0, "Invalid GTIN"
    
    if not COSMOS_TOKENS:
        return False, None, None, 0, "No Cosmos tokens available"

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
                print(f"  [COSMOS] Found: \"{product_name}\" [{brand_name}] for GTIN {gtin} ({execution_time_ms}ms)")
                return True, product_name, brand_name, execution_time_ms, None
                
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
            
    return False, None, None, 0, "All Cosmos tokens reached limit"


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


def log_llm_decision(market_id, ncm, new_product_name, canonical_name, existing_products, 
                     llm_prompt, llm_response, decision, matched_product_id,
                     success, error_message, execution_time_ms):
    """
    Log LLM decision to Supabase for debugging.
    """
    try:
        log_data = {
            'market_id': market_id,
            'ncm': ncm,
            'new_product_name': new_product_name[:200] if new_product_name else '',
            'canonical_name': canonical_name[:200] if canonical_name else '',  # Store formatted name
            'existing_products': existing_products,  # JSONB
            'llm_prompt': llm_prompt,
            'llm_response': llm_response,
            'decision': decision,
            'matched_product_id': matched_product_id,
            'success': success,
            'error_message': error_message,
            'execution_time_ms': execution_time_ms,
            'created_at': datetime.utcnow().isoformat()
        }
        supabase.table('llm_product_decisions').insert(log_data).execute()
        print(f"  [LOG] LLM decision logged: {decision} → \"{canonical_name}\"")
    except Exception as e:
        print(f"  [WARN] Failed to log LLM decision: {e}")


def log_product_lookup(nfce_url, market_id, gtin, ncm, original_name, final_name,
                       cosmos_result=None, off_result=None, llm_result=None,
                       source_used=None, success=False):
    """
    Log detailed product lookup to Supabase product_lookup_log table.
    
    Args:
        nfce_url: The NFCe URL being processed
        market_id: Market identifier
        gtin: Product GTIN/EAN
        ncm: Product NCM code
        original_name: Original name from NFCe
        final_name: Final name after lookup/formatting
        cosmos_result: Dict with Bluesoft Cosmos lookup details
        off_result: Dict with Open Food Facts lookup details  
        llm_result: Dict with LLM lookup details
        source_used: Which source provided the final name
        success: Whether lookup was successful
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
                'api_error': cosmos_result.get('error'),
                'api_from_cache': False,
                'api_time_ms': cosmos_result.get('time_ms'),
            })
        
        # Open Food Facts details
        if off_result:
            log_data.update({
                'off_attempted': True,
                'off_success': off_result.get('success', False),
                'off_product_name': off_result.get('product_name'),
                'off_error': off_result.get('error'),
                'off_time_ms': off_result.get('time_ms'),
            })
        
        # LLM details
        if llm_result:
            log_data.update({
                'llm_attempted': True,
                'llm_success': llm_result.get('success', False),
                'llm_decision': llm_result.get('decision'),
                'llm_matched_id': llm_result.get('matched_id'),
                'llm_error': llm_result.get('error'),
                'llm_time_ms': llm_result.get('time_ms'),
            })
        
        supabase.table('product_lookup_log').insert(log_data).execute()
        
    except Exception as e:
        # Don't fail the main process if logging fails
        print(f"  [WARN] Failed to log product lookup: {e}")


def call_llm_for_product_match(new_product_name, existing_products):
    """
    Call OpenAI to determine if new product matches any existing product.
    Also returns a canonical (formatted) product name.
    
    Args:
        new_product_name: Name of the new product being added (often ugly/abbreviated)
        existing_products: List of dicts with 'id' and 'product_name' keys (from ALL markets)
    
    Returns:
        tuple: (decision, matched_id, canonical_name, llm_prompt, llm_response, execution_time_ms, error_message)
        decision: "CREATE_NEW" or "UPDATE:{id}"
        matched_id: ID of matched product (or None)
        canonical_name: The standardized product name to use
    """
    if not openai_client:
        return None, None, None, None, None, 0, "OpenAI client not initialized"
    
    # Handle empty product name
    if not new_product_name or not new_product_name.strip():
        return None, None, None, None, None, 0, "New product name is empty"
    
    # If no existing products, we need to format the name
    if not existing_products:
        return call_llm_format_new_product(new_product_name)
    
    # Limit to 20 most recent products to avoid huge prompts
    MAX_PRODUCTS_TO_COMPARE = 20
    products_to_compare = existing_products[:MAX_PRODUCTS_TO_COMPARE]
    
    # Build the list of existing products for the prompt
    existing_list = "\n".join([
        f"{i+1}. ID: {p['id']} - \"{p['product_name']}\""
        for i, p in enumerate(products_to_compare)
    ])
    
    prompt = f"""Você é um especialista em identificação de produtos de supermercado brasileiro.

Dado um novo produto e uma lista de produtos existentes com o mesmo NCM,
determine se o novo produto é IGUAL a algum existente ou se é DIFERENTE.

Novo produto: "{new_product_name}"

Produtos existentes:
{existing_list}

=== ABREVIAÇÕES COMUNS (são equivalentes) ===
QJ/QJO=Queijo, MUSS=Mussarela, PARM=Parmesão, BOV=Bovino, RES=Resfriado
BISC=Biscoito, REFRIG=Refrigerante, AZ=Azeite, INT=Integral, AMER=Americana
BDJ=Bandeja, TRC=Trincado, COZ=Cozido, HIDROP=Hidropônico, UN=Unidade

=== REGRAS CRÍTICAS ===
1. MARCAS/FABRICANTES DIFERENTES = NOVO (ex: "AURORA" != "PARLAK", "SADIA" != "SEARA")
2. VARIEDADES/TIPOS DIFERENTES = NOVO (ex: "ITALIANO" != generico, "PINK LADY" != "GALA")
3. TAMANHOS DIFERENTES = NOVO (ex: "500G" != "1KG", "350ML" != "2L")
4. SABORES DIFERENTES = NOVO (ex: "ORIGINAL" != "ZERO", "LIMAO" != "BAUNILHA")
5. Apenas variacoes de ESCRITA/ABREVIACAO = IGUAL (ex: "QJ MUSS" = "Queijo Mussarela")

ATENCAO: Se um produto tem marca/fabricante e o outro nao tem, sao DIFERENTES!
Ex: "QJ.MUSS AURORA KG" != "Queijo Mussarela Parlak" (AURORA != PARLAK = marcas diferentes)
Ex: "TOMATE ITALIANO KG" != "Tomate Kg" (ITALIANO e uma variedade especifica)

Responda em JSON:
{{"decisao": "NOVO" ou "IGUAL", "id_match": null ou ID, "nome_canonico": "Nome formatado"}}

IMPORTANTE: Mesmo que a decisao seja "IGUAL", se o nome do produto existente estiver em caixa alta ou mal formatado, forneca um "nome_canonico" limpo e legivel.

Se IGUAL: melhore a formatacao se o nome existente for ruim.
Se NOVO: formate expandindo abreviacoes.

JSON:"""

    start_time = time.time()
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Voce e um especialista em identificacao de produtos. Responda apenas com JSON valido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1  # Low temperature for consistent decisions
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        llm_response = response.choices[0].message.content.strip()
        
        print(f"  [LLM] Response: {llm_response} ({execution_time_ms}ms)")
        
        # Parse JSON response
        import json
        try:
            # Clean up response - remove markdown code blocks if present
            clean_response = llm_response
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()
            
            result = json.loads(clean_response)
            decision_raw = result.get("decisao", "").upper()
            matched_id = result.get("id_match")
            canonical_name = result.get("nome_canonico", new_product_name)
            
            if decision_raw == "NOVO":
                return "CREATE_NEW", None, canonical_name, prompt, llm_response, execution_time_ms, None
            elif decision_raw == "IGUAL" and matched_id:
                matched_id = int(matched_id)
                # Verify the ID exists in our list
                valid_ids = [p['id'] for p in products_to_compare]
                if matched_id in valid_ids:
                    # PRIORIDADE: Se o LLM sugeriu um nome canônico melhor/limpo, usamos ele
                    # mesmo que tenha dado match com um ID existente.
                    return f"UPDATE:{matched_id}", matched_id, canonical_name, prompt, llm_response, execution_time_ms, None
                else:
                    return "CREATE_NEW", None, canonical_name, prompt, llm_response, execution_time_ms, f"LLM returned invalid ID: {matched_id}"
            else:
                # Unexpected response - default to creating new with formatted name
                return "CREATE_NEW", None, canonical_name, prompt, llm_response, execution_time_ms, f"Unexpected decision: {decision_raw}"
                
        except json.JSONDecodeError as je:
            # Fallback to simple parsing if JSON fails
            print(f"  [WARN] JSON parse failed, trying fallback: {je}")
            return "CREATE_NEW", None, new_product_name, prompt, llm_response, execution_time_ms, f"JSON parse error: {je}"
            
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_msg = f"OpenAI API error: {str(e)}"
        print(f"  [ERROR] LLM error: {error_msg}")
        return None, None, None, prompt, None, execution_time_ms, error_msg


def call_llm_format_new_product(product_name):
    """
    Call OpenAI to format a new product name when no existing products to compare.
    
    Returns:
        tuple: (decision, matched_id, canonical_name, llm_prompt, llm_response, execution_time_ms, error_message)
    """
    if not openai_client:
        return "CREATE_NEW", None, product_name, None, None, 0, "OpenAI client not initialized"
    
    prompt = f"""Formate este nome de produto de supermercado brasileiro.

Produto: "{product_name}"

=== ABREVIAÇÕES COMUNS ===
QJ/QJO=Queijo, MUSS=Mussarela, PARM=Parmesão, BOV=Bovino, RES=Resfriado
BISC=Biscoito, REFRIG=Refrigerante, AZ=Azeite, E.V=Extra Virgem, INT=Integral
BDJ=Bandeja, TRC=Trincado, COZ=Cozido, HIDROP=Hidropônico, UN=Unidade
AMER=Americana, CR=Creme, MACO=Maço, MORT=Mortadela, PROT=Protetor
DET=Detergente, SAB=Sabão, AMAC=Amaciante, LIMP=Limpador, DESIF=Desinfetante
MAC=Macarrão, AC=Açúcar, REF=Refinado, MIN=Mineral, PAP=Papel

=== REGRAS ===
1. Expanda abreviacoes conhecidas
2. NUNCA remova palavras - preserve tudo (especialmente marcas)
3. NUNCA reordene - mantenha a ordem original
4. Use Title Case e acentuacao correta (a, e, c, etc)
5. Remova pontos entre palavras (QJ.MUSS -> Queijo Mussarela)
6. MANTENHA "Kg" (nao expanda para Quilograma)
7. Se nao reconhecer uma palavra, mantenha em Title Case
8. Remova virgulas e caracteres estranhos no final

Responda APENAS com o nome formatado:"""

    start_time = time.time()
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Voce formata nomes de produtos. Responda apenas com o nome formatado."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        canonical_name = response.choices[0].message.content.strip()
        
        # Remove quotes if present
        if canonical_name.startswith('"') and canonical_name.endswith('"'):
            canonical_name = canonical_name[1:-1]
        
        print(f"  [LLM] Formatted: \"{product_name}\" → \"{canonical_name}\" ({execution_time_ms}ms)")
        
        return "CREATE_NEW", None, canonical_name, prompt, canonical_name, execution_time_ms, None
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_msg = f"OpenAI API error: {str(e)}"
        print(f"  [ERROR] LLM format error: {error_msg}")
        # Return original name on error
        return "CREATE_NEW", None, product_name, prompt, None, execution_time_ms, error_msg


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
            'off_hits': 0,
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


def enrich_and_upsert_unique_products(market_id, products, nfce_url):
    """
    DEPRECATED: This was the original enrichment logic.
    Now maintained here for future reference or for the enrichment worker to use.
    """
    updated_unique = 0
    created_unique = 0
    skipped_products = 0
    off_hits = 0
    llm_calls = 0
    
    inserted_unique_ids = []
    updated_unique_backup = {}
    
    try:
        # 2. Upsert to UNIQUE_PRODUCTS table
        # Priority: 1) Bluesoft Cosmos 2) Open Food Facts 3) LLM
        # NOTE: Each insert/update commits immediately - partial success is preserved
        print(f"[2/2] Upserting to UNIQUE_PRODUCTS table...")
        print(f"      Priority: Bluesoft Cosmos -> Open Food Facts -> LLM")
        
        for idx, product in enumerate(products, 1):
            original_product_name = product.get('product', '')
            ncm = product['ncm']
            ean = product.get('ean', 'SEM GTIN')
            
            # Variables for this product
            canonical_name = None
            decision = None
            matched_id = None
            source_used = None
            
            # Detailed lookup results for logging
            cosmos_result = None
            off_result = None
            llm_result = None
            
            try:
                print(f"\n  [{idx}/{len(products)}] Processing: {original_product_name[:50]}... (GTIN: {ean})")
                
                # ============================================================
                # STEP 1: Try Bluesoft Cosmos FIRST (if valid GTIN)
                # ============================================================
                if ean and ean != 'SEM GTIN' and len(ean) >= 8:
                    cosmos_success, cosmos_product_name, cosmos_brand, cosmos_time, cosmos_error = get_product_from_cosmos(ean)
                    
                    # Store Cosmos result for logging
                    cosmos_result = {
                        'success': cosmos_success,
                        'product_name': cosmos_product_name,
                        'brand': cosmos_brand,
                        'time_ms': cosmos_time,
                        'error': cosmos_error
                    }
                    
                    if cosmos_success and cosmos_product_name:
                        # Cosmos found the product!
                        canonical_name = cosmos_product_name
                        decision = "CREATE_NEW"
                        source_used = "COSMOS_BLUE"
                        print(f"    [COSMOS] SUCCESS: \"{cosmos_product_name}\" [{cosmos_brand}]")
                    else:
                        print(f"    [COSMOS] FAILED: {cosmos_error or 'Not found'}")
                        
                        # ============================================================
                        # STEP 2: Cosmos failed - Try Open Food Facts as FALLBACK
                        # ============================================================
                        off_success, off_product_name, off_time = get_product_from_open_food_facts(ean)
                        
                        # Store OFF result for logging
                        off_result = {
                            'success': off_success,
                            'product_name': off_product_name,
                            'time_ms': off_time,
                            'error': None if off_success else 'Not found'
                        }
                        
                        if off_success and off_product_name:
                            # Open Food Facts found the product!
                            canonical_name = off_product_name
                            decision = "CREATE_NEW"
                            source_used = "OPEN_FOOD_FACTS"
                            off_hits += 1
                            print(f"    [OFF] SUCCESS (fallback): \"{off_product_name}\"")
                        else:
                            print(f"    [OFF] FAILED: Not found")
                else:
                    print(f"    [SKIP] No valid GTIN, going to LLM...")
                
                # ============================================================
                # STEP 3: Both Cosmos and OFF failed - Use LLM as FINAL FALLBACK
                # ============================================================
                if canonical_name is None:
                    llm_calls += 1
                    
                    # Query existing products with same NCM from ALL markets
                    response = supabase.table('unique_products').select('*').eq('ncm', ncm).execute()
                    existing_products = response.data if response.data else []
                    
                    if existing_products:
                        markets_with_product = set(p.get('market_id', 'unknown') for p in existing_products)
                        print(f"    [LLM] Found {len(existing_products)} similar products in {len(markets_with_product)} markets")
                    
                    # Call LLM to match/format product
                    llm_decision, llm_matched_id, llm_canonical, llm_prompt, llm_response, llm_time, llm_error = call_llm_for_product_match(
                        new_product_name=original_product_name,
                        existing_products=existing_products
                    )
                    
                    # Store LLM result for logging
                    llm_result = {
                        'success': llm_canonical is not None,
                        'decision': llm_decision,
                        'matched_id': llm_matched_id,
                        'time_ms': llm_time,
                        'error': llm_error
                    }
                    
                    if llm_canonical:
                        canonical_name = llm_canonical
                        decision = llm_decision
                        matched_id = llm_matched_id
                        source_used = "LLM"
                        print(f"    [LLM] SUCCESS: \"{canonical_name}\" (decision: {decision})")
                    else:
                        print(f"    [LLM] FAILED: {llm_error or 'Unknown error'}")
                    
                    # Log to llm_product_decisions table (for backward compatibility)
                    log_llm_decision(
                        market_id=market_id,
                        ncm=ncm,
                        new_product_name=original_product_name,
                        canonical_name=canonical_name,
                        existing_products=[{'id': p['id'], 'name': p['product_name'], 'market': p.get('market_id')} for p in existing_products] if existing_products else None,
                        llm_prompt=llm_prompt,
                        llm_response=llm_response,
                        decision=llm_decision if llm_decision else "SKIPPED",
                        matched_product_id=llm_matched_id,
                        success=llm_decision is not None,
                        error_message=llm_error,
                        execution_time_ms=llm_time
                    )
                
                # Log detailed product lookup to new table
                log_product_lookup(
                    nfce_url=nfce_url,
                    market_id=market_id,
                    gtin=ean,
                    ncm=ncm,
                    original_name=original_product_name,
                    final_name=canonical_name,
                    cosmos_result=cosmos_result,
                    off_result=off_result,
                    llm_result=llm_result,
                    source_used=source_used,
                    success=canonical_name is not None
                )
                
                # Handle complete failure -> skip product but continue with others
                if canonical_name is None:
                    print(f"    [FINAL] SKIPPED - All sources failed")
                    skipped_products += 1
                    continue
                
                # Use canonical name for storage (or original if both failed)
                product_name = canonical_name if canonical_name else original_product_name
                
                unique_data = {
                    'market_id': market_id,
                    'ncm': ncm,
                    'ean': ean,
                    'product_name': product_name,  # Use canonical name!
                    'unidade_comercial': product.get('unidade_comercial', 'UN'),
                    'price': product.get('unit_price', 0),
                    'nfce_url': nfce_url,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                # Check if this market already has this product (to update instead of insert)
                existing_in_this_market = supabase.table('unique_products').select('id').match({
                    'market_id': market_id,
                    'ncm': ncm,
                    'product_name': product_name
                }).execute()
                
                if existing_in_this_market.data:
                    # Update existing row for this market
                    update_id = existing_in_this_market.data[0]['id']
                    
                    # Backup old data for potential rollback
                    old_data_response = supabase.table('unique_products').select('*').eq('id', update_id).execute()
                    if old_data_response.data:
                        updated_unique_backup[update_id] = old_data_response.data[0]
                    
                    update_response = supabase.table('unique_products').update(unique_data).eq('id', update_id).execute()
                    updated_unique += 1
                    print(f"  [~] [{idx}/{len(products)}] Updated price in market: \"{product_name[:40]}\"")
                else:
                    # Create new row for this market
                    insert_response = supabase.table('unique_products').insert(unique_data).execute()
                    
                    if not insert_response.data or len(insert_response.data) == 0:
                        raise Exception(f"Failed to insert product {idx}")
                    
                    inserted_unique_ids.append(insert_response.data[0]['id'])
                    created_unique += 1
                    
                    if matched_id:
                        print(f"  [+] [{idx}/{len(products)}] Added to market (matched ID {matched_id}): \"{product_name[:40]}\"")
                    else:
                        print(f"  [+] [{idx}/{len(products)}] Created (new product): \"{product_name[:40]}\"")
                    
            except Exception as e:
                print(f"[ERROR] Processing product {idx}: {str(e)}")
                raise Exception(f"Failed at product {idx}: {str(e)}")
        
        return {
            'updated_unique': updated_unique,
            'created_unique': created_unique,
            'skipped_products': skipped_products,
            'off_hits': off_hits,
            'llm_calls': llm_calls
        }
    except Exception as e:
        # Rollback logic for unique products
        if inserted_unique_ids:
            try:
                for unique_id in inserted_unique_ids:
                    supabase.table('unique_products').delete().eq('id', unique_id).execute()
                print(f"[OK] Rolled back unique products")
            except Exception as rb_error:
                print(f"[FAIL] Rollback unique_products failed: {rb_error}")
        
        if updated_unique_backup:
            try:
                for unique_id, old_data in updated_unique_backup.items():
                    restore_data = {k: v for k, v in old_data.items() if k not in ['id', 'created_at']}
                    supabase.table('unique_products').update(restore_data).eq('id', unique_id).execute()
                print(f"[OK] Restored updated products")
            except Exception as rb_error:
                print(f"[FAIL] Restore failed: {rb_error}")
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
    
    use_async = data.get('async', False)
    
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
    
    # ========== SYNC MODE ==========
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
                        'unique_products_created': save_result['created_unique'],
                        'unique_products_updated': save_result['updated_unique'],
                        'unique_products_skipped': save_result.get('skipped_products', 0),
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
            'id, product_name, ean, ncm, price, unidade_comercial, market_id'
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
                    'max_price': p['price']
                }
            
            products_map[key]['markets_count'] += 1
            products_map[key]['min_price'] = min(products_map[key]['min_price'], p['price'])
            products_map[key]['max_price'] = max(products_map[key]['max_price'], p['price'])
        
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
                'prices': {}
            }
            
            for market_id in market_ids:
                price = None
                
                # Try to find by EAN first (if available and not "SEM GTIN")
                if product.get('ean') and product['ean'] != 'SEM GTIN':
                    result = supabase.table('unique_products').select('price').match({
                        'market_id': market_id,
                        'ean': product['ean']
                    }).execute()
                    if result.data:
                        price = result.data[0]['price']
                
                # Fallback to NCM if no EAN match
                if price is None and product.get('ncm'):
                    result = supabase.table('unique_products').select('price, product_name').match({
                        'market_id': market_id,
                        'ncm': product['ncm']
                    }).execute()
                    if result.data:
                        # If multiple products with same NCM, try to match by name
                        if len(result.data) > 1 and product.get('product_name'):
                            for r in result.data:
                                if product['product_name'].lower() in r['product_name'].lower():
                                    price = r['price']
                                    break
                        if price is None:
                            price = result.data[0]['price']
                
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
