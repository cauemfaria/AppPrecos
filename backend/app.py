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
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# Semaphore to limit concurrent Playwright extractions (browser is resource-heavy)
extraction_semaphore = threading.Semaphore(1)  # Only 1 extraction at a time

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
print(f"[OK] API URL: {SUPABASE_URL}")


# ==================== UTILITY FUNCTIONS ====================

def generate_market_id():
    """Generate a random unique market ID (format: MKT + 8 random chars)"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"MKT{random_part}"


def log_llm_decision(market_id, ncm, new_product_name, existing_products, 
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
        print(f"  [LOG] LLM decision logged: {decision}")
    except Exception as e:
        print(f"  [WARN] Failed to log LLM decision: {e}")


def call_llm_for_product_match(new_product_name, existing_products):
    """
    Call OpenAI to determine if new product matches any existing product.
    
    Args:
        new_product_name: Name of the new product being added
        existing_products: List of dicts with 'id' and 'product_name' keys
    
    Returns:
        tuple: (decision, matched_id, llm_prompt, llm_response, execution_time_ms, error_message)
        decision: "CREATE_NEW" or "UPDATE:{id}"
        matched_id: ID of matched product (or None)
    """
    if not openai_client:
        return None, None, None, None, 0, "OpenAI client not initialized"
    
    if not existing_products:
        return "CREATE_NEW", None, None, None, 0, None
    
    # Handle empty product name
    if not new_product_name or not new_product_name.strip():
        return None, None, None, None, 0, "New product name is empty"
    
    # Limit to 20 most recent products to avoid huge prompts
    MAX_PRODUCTS_TO_COMPARE = 20
    products_to_compare = existing_products[:MAX_PRODUCTS_TO_COMPARE]
    
    # Build the list of existing products for the prompt
    existing_list = "\n".join([
        f"{i+1}. ID: {p['id']} - \"{p['product_name']}\""
        for i, p in enumerate(products_to_compare)
    ])
    
    prompt = f"""Você é um especialista em identificação de produtos de supermercado.

Dado um novo produto e uma lista de produtos existentes com o mesmo código NCM (categoria fiscal),
determine se o novo produto é IGUAL a algum dos existentes ou se é um produto DIFERENTE.

Novo produto: "{new_product_name}"

Produtos existentes:
{existing_list}

REGRAS IMPORTANTES:
- Variações de escrita, abreviações e formatação = MESMO produto (ex: "COCA COLA 350ML" = "COCA-COLA LATA 350ML")
- Marcas diferentes = produtos DIFERENTES (ex: "COCA COLA" ≠ "PEPSI")
- Tamanhos/quantidades diferentes = produtos DIFERENTES (ex: "350ML" ≠ "2L")
- Sabores diferentes = produtos DIFERENTES (ex: "ORIGINAL" ≠ "ZERO")

Responda APENAS com:
- "NOVO" se é um produto diferente de todos os existentes
- "IGUAL:ID" se é igual ao produto com esse ID (substitua ID pelo número do ID)

Sua resposta (apenas uma palavra):"""

    start_time = time.time()
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você responde apenas com 'NOVO' ou 'IGUAL:ID'. Nada mais."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0.1  # Low temperature for consistent decisions
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        llm_response = response.choices[0].message.content.strip()
        
        print(f"  [LLM] Response: {llm_response} ({execution_time_ms}ms)")
        
        # Parse response - normalize by removing spaces and converting to uppercase
        normalized_response = llm_response.upper().replace(" ", "")
        
        if normalized_response == "NOVO":
            return "CREATE_NEW", None, prompt, llm_response, execution_time_ms, None
        elif normalized_response.startswith("IGUAL:"):
            try:
                # Extract ID after "IGUAL:" - handle variations like "IGUAL:123", "IGUAL: 123", "igual:123"
                id_part = normalized_response.split(":")[1].strip()
                matched_id = int(id_part)
                # Verify the ID exists in our list
                valid_ids = [p['id'] for p in products_to_compare]
                if matched_id in valid_ids:
                    return f"UPDATE:{matched_id}", matched_id, prompt, llm_response, execution_time_ms, None
                else:
                    return "CREATE_NEW", None, prompt, llm_response, execution_time_ms, f"LLM returned invalid ID: {matched_id}"
            except (ValueError, IndexError):
                return "CREATE_NEW", None, prompt, llm_response, execution_time_ms, f"Failed to parse ID from: {llm_response}"
        else:
            # Unexpected response - default to creating new
            return "CREATE_NEW", None, prompt, llm_response, execution_time_ms, f"Unexpected LLM response: {llm_response}"
            
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_msg = f"OpenAI API error: {str(e)}"
        print(f"  [ERROR] LLM error: {error_msg}")
        return None, None, prompt, None, execution_time_ms, error_msg


def process_nfce_in_background(url, url_record_id):
    """Background task to process NFCe extraction and save to database"""
    start_time = time.time()
    
    try:
        print(f"\n[BACKGROUND #{url_record_id}] Queued for processing...")
        print(f"[BACKGROUND #{url_record_id}] Waiting for extraction slot (semaphore)...")
        
        # Acquire semaphore to limit concurrent extractions
        # This prevents multiple Playwright browsers from running simultaneously
        extraction_semaphore.acquire()
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
                supabase.table('processed_urls').update({
                    'status': 'error',
                    'error_message': 'No products or market info extracted'
                }).eq('id', url_record_id).execute()
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
            
            # Update URL record with success
            supabase.table('processed_urls').update({
                'market_id': market['market_id'],
                'market_name': market['name'],
                'products_count': len(products),
                'status': 'success'
            }).eq('id', url_record_id).execute()
            
            total_time = time.time() - start_time
            print(f"[OK] [BACKGROUND #{url_record_id}] Complete in {total_time:.1f}s: {save_result['saved_to_purchases']} products saved")
            
        finally:
            # Always release the semaphore
            extraction_semaphore.release()
            print(f"[BACKGROUND #{url_record_id}] Released extraction slot")
        
    except Exception as e:
        supabase.table('processed_urls').update({
            'status': 'error',
            'error_message': str(e)[:200]  # Limit error message length
        }).eq('id', url_record_id).execute()
        total_time = time.time() - start_time
        print(f"[FAIL] [BACKGROUND #{url_record_id}] Error after {total_time:.1f}s: {e}")
        import traceback
        traceback.print_exc()


def save_products_to_supabase(market_id, products, nfce_url, purchase_date=None):
    """
    Save products to Supabase PostgreSQL database
    Maintains both full history (purchases) and latest prices (unique_products)
    """
    if purchase_date is None:
        purchase_date = datetime.utcnow()
    
    inserted_purchase_ids = []
    inserted_unique_ids = []
    updated_unique_backup = {}
    
    try:
        saved_to_purchases = 0
        updated_unique = 0
        created_unique = 0
        
        print(f"\n{'='*60}")
        print(f"SAVING PRODUCTS TO SUPABASE")
        print(f"{'='*60}")
        print(f"Market ID: {market_id}")
        print(f"Products count: {len(products)}")
        print(f"{'='*60}\n")
        
        # 1. Insert to PURCHASES table
        print(f"[1/2] Inserting {len(products)} products to PURCHASES table...")
        
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
                    'purchase_date': purchase_date.isoformat()
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
        
        # 2. Upsert to UNIQUE_PRODUCTS table using LLM-based matching
        print(f"[2/2] Upserting to UNIQUE_PRODUCTS table (LLM-based matching)...")
        skipped_products = 0
        
        for idx, product in enumerate(products, 1):
            product_name = product.get('product', '')
            ncm = product['ncm']
            
            try:
                unique_data = {
                    'market_id': market_id,
                    'ncm': ncm,
                    'ean': product.get('ean', 'SEM GTIN'),
                    'product_name': product_name,
                    'unidade_comercial': product.get('unidade_comercial', 'UN'),
                    'price': product.get('unit_price', 0),
                    'nfce_url': nfce_url,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                # Query existing products with same NCM in this market
                # Get all fields for potential rollback
                response = supabase.table('unique_products').select('*').match({
                    'market_id': market_id,
                    'ncm': ncm
                }).execute()
                
                existing_products = response.data if response.data else []
                
                # CASE 1: No existing products with this NCM -> create new directly
                if not existing_products:
                    insert_response = supabase.table('unique_products').insert(unique_data).execute()
                    
                    if not insert_response.data or len(insert_response.data) == 0:
                        raise Exception(f"Failed to insert product {idx}")
                    
                    inserted_unique_ids.append(insert_response.data[0]['id'])
                    created_unique += 1
                    print(f"  [+] [{idx}/{len(products)}] Created (new NCM): {product_name[:50]}")
                    
                    # Log decision (no LLM needed)
                    log_llm_decision(
                        market_id=market_id,
                        ncm=ncm,
                        new_product_name=product_name,
                        existing_products=None,
                        llm_prompt=None,
                        llm_response=None,
                        decision="CREATE_NEW",
                        matched_product_id=None,
                        success=True,
                        error_message=None,
                        execution_time_ms=0
                    )
                    continue
                
                # CASE 2: Existing products found -> call LLM to decide
                print(f"  [SEARCH] [{idx}/{len(products)}] Found {len(existing_products)} existing products with NCM {ncm}")
                
                decision, matched_id, llm_prompt, llm_response, exec_time, error_msg = call_llm_for_product_match(
                    new_product_name=product_name,
                    existing_products=existing_products
                )
                
                # Log the LLM decision
                log_llm_decision(
                    market_id=market_id,
                    ncm=ncm,
                    new_product_name=product_name,
                    existing_products=[{'id': p['id'], 'name': p['product_name']} for p in existing_products],
                    llm_prompt=llm_prompt,
                    llm_response=llm_response,
                    decision=decision if decision else "SKIPPED",
                    matched_product_id=matched_id,
                    success=decision is not None,
                    error_message=error_msg,
                    execution_time_ms=exec_time
                )
                
                # Handle LLM failure -> skip product
                if decision is None:
                    print(f"  [SKIP] [{idx}/{len(products)}] SKIPPED (LLM error): {product_name[:50]}")
                    skipped_products += 1
                    continue
                
                # Handle LLM decision
                if decision == "CREATE_NEW":
                    insert_response = supabase.table('unique_products').insert(unique_data).execute()
                    
                    if not insert_response.data or len(insert_response.data) == 0:
                        raise Exception(f"Failed to insert product {idx}")
                    
                    inserted_unique_ids.append(insert_response.data[0]['id'])
                    created_unique += 1
                    print(f"  [+] [{idx}/{len(products)}] Created (LLM: new product): {product_name[:50]}")
                    
                elif decision.startswith("UPDATE:"):
                    # Update existing product
                    old_data = next((p for p in existing_products if p['id'] == matched_id), None)
                    if old_data:
                        updated_unique_backup[matched_id] = old_data
                    
                    update_response = supabase.table('unique_products').update(unique_data).eq('id', matched_id).execute()
                    
                    if not update_response.data or len(update_response.data) == 0:
                        raise Exception(f"Failed to update product {idx}")
                    
                    updated_unique += 1
                    print(f"  [~] [{idx}/{len(products)}] Updated (LLM: same as ID {matched_id}): {product_name[:50]}")
                    
            except Exception as e:
                print(f"[ERROR] Processing product {idx}: {str(e)}")
                raise Exception(f"Failed at product {idx}: {str(e)}")
        
        print(f"\n{'='*60}")
        print(f"[OK] COMPLETED: {saved_to_purchases} purchases, {created_unique} new, {updated_unique} updated, {skipped_products} skipped")
        print(f"{'='*60}\n")
        
        return {
            'saved_to_purchases': saved_to_purchases,
            'updated_unique': updated_unique,
            'created_unique': created_unique,
            'skipped_products': skipped_products
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
