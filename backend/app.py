"""
AppPrecos Backend API - Version 2
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
from dotenv import load_dotenv
from supabase import create_client

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

print("✓ Supabase client initialized")
print(f"✓ API URL: {SUPABASE_URL}")


# ==================== UTILITY FUNCTIONS ====================

def validate_database_schema():
    """
    Validate that required tables and columns exist in Supabase
    Returns: dict with validation results
    """
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    try:
        # Check if purchases table has product_name column
        test_purchase = {
            'market_id': 'TEST_VALIDATION',
            'ncm': '00000000',
            'ean': 'TEST',
            'product_name': 'Test Product',
            'quantity': 1.0,
            'unidade_comercial': 'UN',
            'total_price': 1.0,
            'unit_price': 1.0,
            'nfce_url': 'test',
            'purchase_date': datetime.utcnow().isoformat()
        }
        
        # Try to insert test data (will rollback by deleting it)
        response = supabase.table('purchases').insert(test_purchase).execute()
        
        if response.data:
            # Clean up test data
            test_id = response.data[0]['id']
            supabase.table('purchases').delete().eq('id', test_id).execute()
            print("✓ purchases table schema validated (product_name column exists)")
        else:
            validation_results['valid'] = False
            validation_results['errors'].append("purchases table test insert failed")
            
    except Exception as e:
        validation_results['valid'] = False
        validation_results['errors'].append(f"purchases table validation failed: {str(e)}")
        print(f"✗ purchases table validation failed: {e}")
    
    try:
        # Check unique_products table
        test_unique = {
            'market_id': 'TEST_VALIDATION',
            'ncm': '00000000',
            'ean': 'TEST',
            'product_name': 'Test Product',
            'unidade_comercial': 'UN',
            'price': 1.0,
            'nfce_url': 'test',
            'last_updated': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('unique_products').insert(test_unique).execute()
        
        if response.data:
            # Clean up test data
            test_id = response.data[0]['id']
            supabase.table('unique_products').delete().eq('id', test_id).execute()
            print("✓ unique_products table schema validated (product_name column exists)")
        else:
            validation_results['valid'] = False
            validation_results['errors'].append("unique_products table test insert failed")
            
    except Exception as e:
        validation_results['valid'] = False
        validation_results['errors'].append(f"unique_products table validation failed: {str(e)}")
        print(f"✗ unique_products table validation failed: {e}")
    
    return validation_results


def generate_market_id():
    """Generate a random unique market ID (format: MKT + 8 random chars)"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"MKT{random_part}"


def process_nfce_in_background(url, url_record_id):
    """
    Background task to process NFCe extraction and save to database
    FIXED v2.1: Uses improved save_products_to_supabase with rollback capability
    """
    try:
        print(f"\n[BACKGROUND TASK] Processing NFCe URL (Record ID: {url_record_id})")
        
        # Import crawler
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from nfce_extractor import extract_full_nfce_data
        
        # Extract data
        print(f"[BACKGROUND TASK] Extracting NFCe data...")
        result = extract_full_nfce_data(url, headless=True)
        market_info = result.get('market_info', {})
        products = result.get('products', [])
        
        if not products or not market_info.get('name') or not market_info.get('address'):
            # Update status to error
            supabase.table('processed_urls').update({'status': 'error'}).eq('id', url_record_id).execute()
            print(f"✗ Background processing failed: No products or market info")
            return
        
        print(f"[BACKGROUND TASK] Extracted {len(products)} products from {market_info.get('name')}")
        
        # Check/create market
        print(f"[BACKGROUND TASK] Checking/creating market...")
        market_result = supabase.table('markets').select('*').match({
            'name': market_info['name'],
            'address': market_info['address']
        }).execute()
        
        if market_result.data:
            market = market_result.data[0]
            print(f"[BACKGROUND TASK] Market found: {market['market_id']}")
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
            print(f"[BACKGROUND TASK] Market created: {new_market_id}")
        
        # Save products (uses improved function with rollback)
        print(f"[BACKGROUND TASK] Saving products to database...")
        save_result = save_products_to_supabase(market['market_id'], products, url)
        
        # Update URL record with success
        update_data = {
            'market_id': market['market_id'],
            'products_count': len(products),
            'status': 'success'
        }
        supabase.table('processed_urls').update(update_data).eq('id', url_record_id).execute()
        print(f"✓ [BACKGROUND TASK] Processing complete: {save_result['saved_to_purchases']} purchases, "
              f"{save_result['created_unique']} new unique products, {save_result['updated_unique']} updated")
        
    except Exception as e:
        # Update status to error
        supabase.table('processed_urls').update({'status': 'error'}).eq('id', url_record_id).execute()
        print(f"✗ [BACKGROUND TASK] Processing error: {e}")
        import traceback
        traceback.print_exc()


def save_products_to_supabase(market_id, products, nfce_url, purchase_date=None):
    """
    Save products to Supabase PostgreSQL database
    Maintains both full history (purchases) and latest prices (unique_products)
    
    FIXED v2.1:
    - Added explicit error checking to prevent silent failures
    - Added detailed logging for debugging
    - Added rollback capability for transaction safety
    - All-or-nothing approach: if any insert fails, rollback all changes
    """
    if purchase_date is None:
        purchase_date = datetime.utcnow()
    
    # Track inserted IDs for rollback capability
    inserted_purchase_ids = []
    inserted_unique_ids = []
    updated_unique_backup = {}  # Store old values for updates
    
    try:
        saved_to_purchases = 0
        updated_unique = 0
        created_unique = 0
        
        print(f"\n{'='*80}")
        print(f"SAVING PRODUCTS TO SUPABASE (Transaction-safe)")
        print(f"{'='*80}")
        print(f"Market ID: {market_id}")
        print(f"Products count: {len(products)}")
        print(f"NFCe URL: {nfce_url[:80]}...")
        print(f"{'='*80}\n")
        
        # 1. Insert to PURCHASES table (full history - unlimited entries)
        # Stores RAW data: quantity, total_price paid, unit_price per KG/UN
        print(f"[1/2] Inserting {len(products)} products to PURCHASES table...")
        
        for idx, product in enumerate(products, 1):
            try:
                purchase_data = {
                    'market_id': market_id,
                    'ncm': product['ncm'],
                    'ean': product.get('ean', 'SEM GTIN'),
                    'product_name': product.get('product', ''),        # Product description
                    'quantity': product.get('quantity', 0),
                    'unidade_comercial': product.get('unidade_comercial', 'UN'),
                    'total_price': product.get('total_price', 0),      # Total paid for this quantity
                    'unit_price': product.get('unit_price', 0),        # Price per KG or UN
                    'nfce_url': nfce_url,
                    'purchase_date': purchase_date.isoformat()
                }
                
                # FIXED: Add explicit error checking
                response = supabase.table('purchases').insert(purchase_data).execute()
                
                # Check if insert was successful
                if not response.data or len(response.data) == 0:
                    error_msg = f"Failed to insert product {idx} (NCM: {product['ncm']}) to purchases table. No data returned."
                    print(f"❌ ERROR: {error_msg}")
                    raise Exception(error_msg)
                
                # Track inserted ID for potential rollback
                inserted_purchase_ids.append(response.data[0]['id'])
                saved_to_purchases += 1
                print(f"  ✓ [{idx}/{len(products)}] {product.get('product', 'Unknown')[:50]} - NCM: {product['ncm']} (ID: {response.data[0]['id']})")
                
            except Exception as e:
                print(f"❌ CRITICAL ERROR inserting product {idx} to PURCHASES:")
                print(f"   Product: {product.get('product', 'Unknown')}")
                print(f"   NCM: {product.get('ncm', 'Unknown')}")
                print(f"   Error: {str(e)}")
                import traceback
                traceback.print_exc()
                # Rollback will happen in outer exception handler
                raise Exception(f"Failed to insert to purchases table at product {idx}: {str(e)}")
        
        print(f"✓ Successfully inserted {saved_to_purchases} products to PURCHASES table\n")
        
        # 2. Upsert to UNIQUE_PRODUCTS table (one per NCM per market)
        # Stores UNIT PRICE only (price per KG or per UN) - no quantity needed
        print(f"[2/2] Upserting {len(products)} products to UNIQUE_PRODUCTS table...")
        
        for idx, product in enumerate(products, 1):
            try:
                unique_data = {
                    'market_id': market_id,
                    'ncm': product['ncm'],
                    'ean': product.get('ean', 'SEM GTIN'),
                    'product_name': product.get('product', ''),        # Product description
                    'unidade_comercial': product.get('unidade_comercial', 'UN'),
                    'price': product.get('unit_price', 0),  # Unit price (per KG or per UN)
                    'nfce_url': nfce_url,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                # Check if exists
                response = supabase.table('unique_products').select('*').match({
                    'market_id': market_id,
                    'ncm': product['ncm']
                }).execute()
                
                if response.data:
                    # Store backup for rollback
                    old_id = response.data[0]['id']
                    updated_unique_backup[old_id] = response.data[0]
                    
                    # Update existing
                    update_response = supabase.table('unique_products').update(unique_data).eq('id', old_id).execute()
                    
                    # FIXED: Check update success
                    if not update_response.data or len(update_response.data) == 0:
                        error_msg = f"Failed to update product {idx} (NCM: {product['ncm']}) in unique_products table"
                        print(f"❌ ERROR: {error_msg}")
                        raise Exception(error_msg)
                    
                    updated_unique += 1
                    print(f"  ↻ [{idx}/{len(products)}] Updated {product.get('product', 'Unknown')[:50]} (ID: {old_id})")
                else:
                    # Create new
                    insert_response = supabase.table('unique_products').insert(unique_data).execute()
                    
                    # FIXED: Check insert success
                    if not insert_response.data or len(insert_response.data) == 0:
                        error_msg = f"Failed to insert product {idx} (NCM: {product['ncm']}) to unique_products table"
                        print(f"❌ ERROR: {error_msg}")
                        raise Exception(error_msg)
                    
                    # Track inserted ID for potential rollback
                    inserted_unique_ids.append(insert_response.data[0]['id'])
                    created_unique += 1
                    print(f"  ✓ [{idx}/{len(products)}] Created {product.get('product', 'Unknown')[:50]} (ID: {insert_response.data[0]['id']})")
                    
            except Exception as e:
                print(f"❌ CRITICAL ERROR upserting product {idx} to UNIQUE_PRODUCTS:")
                print(f"   Product: {product.get('product', 'Unknown')}")
                print(f"   NCM: {product.get('ncm', 'Unknown')}")
                print(f"   Error: {str(e)}")
                import traceback
                traceback.print_exc()
                # Rollback will happen in outer exception handler
                raise Exception(f"Failed to upsert to unique_products table at product {idx}: {str(e)}")
        
        print(f"✓ Successfully processed {updated_unique + created_unique} products in UNIQUE_PRODUCTS table")
        print(f"  - Created: {created_unique}")
        print(f"  - Updated: {updated_unique}\n")
        
        print(f"{'='*80}")
        print(f"TRANSACTION COMPLETED SUCCESSFULLY")
        print(f"  ✓ Purchases saved: {saved_to_purchases}")
        print(f"  ✓ Unique products created: {created_unique}")
        print(f"  ✓ Unique products updated: {updated_unique}")
        print(f"{'='*80}\n")
        
        return {
            'saved_to_purchases': saved_to_purchases,
            'updated_unique': updated_unique,
            'created_unique': created_unique
        }
    
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ TRANSACTION FAILED - INITIATING ROLLBACK")
        print(f"{'='*80}")
        print(f"   Market ID: {market_id}")
        print(f"   NFCe URL: {nfce_url}")
        print(f"   Error: {str(e)}")
        print(f"{'='*80}\n")
        
        # ROLLBACK: Delete all inserted records
        rollback_errors = []
        
        # Rollback purchases
        if inserted_purchase_ids:
            print(f"Rolling back {len(inserted_purchase_ids)} purchases...")
            try:
                for purchase_id in inserted_purchase_ids:
                    supabase.table('purchases').delete().eq('id', purchase_id).execute()
                print(f"✓ Rolled back {len(inserted_purchase_ids)} purchases")
            except Exception as rb_error:
                rollback_errors.append(f"Failed to rollback purchases: {rb_error}")
                print(f"✗ Rollback purchases failed: {rb_error}")
        
        # Rollback newly created unique_products
        if inserted_unique_ids:
            print(f"Rolling back {len(inserted_unique_ids)} unique products (new)...")
            try:
                for unique_id in inserted_unique_ids:
                    supabase.table('unique_products').delete().eq('id', unique_id).execute()
                print(f"✓ Rolled back {len(inserted_unique_ids)} unique products")
            except Exception as rb_error:
                rollback_errors.append(f"Failed to rollback unique_products: {rb_error}")
                print(f"✗ Rollback unique_products failed: {rb_error}")
        
        # Rollback updated unique_products (restore old values)
        if updated_unique_backup:
            print(f"Rolling back {len(updated_unique_backup)} unique products (updates)...")
            try:
                for unique_id, old_data in updated_unique_backup.items():
                    # Remove system fields
                    restore_data = {k: v for k, v in old_data.items() if k not in ['id', 'created_at']}
                    supabase.table('unique_products').update(restore_data).eq('id', unique_id).execute()
                print(f"✓ Restored {len(updated_unique_backup)} unique products to previous state")
            except Exception as rb_error:
                rollback_errors.append(f"Failed to restore unique_products: {rb_error}")
                print(f"✗ Restore unique_products failed: {rb_error}")
        
        if rollback_errors:
            print(f"\n⚠ ROLLBACK COMPLETED WITH ERRORS:")
            for rb_err in rollback_errors:
                print(f"  - {rb_err}")
        else:
            print(f"\n✓ ROLLBACK COMPLETED SUCCESSFULLY - Database state restored")
        
        print(f"{'='*80}\n")
        
        import traceback
        traceback.print_exc()
        raise


# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """API information endpoint"""
    return jsonify({
        'name': 'AppPrecos API v2',
        'version': '2.1',
        'architecture': 'Supabase PostgreSQL - 3-Table Design',
        'status': 'running',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'tables': ['markets', 'purchases', 'unique_products', 'processed_urls'],
        'endpoints': {
            'markets': '/api/markets',
            'market': '/api/markets/{market_id}',
            'market_products': '/api/markets/{market_id}/products',
            'nfce_extract': '/api/nfce/extract',
            'nfce_status': '/api/nfce/status/{url}',
            'stats': '/api/stats',
            'health': '/health',
            'schema_check': '/api/schema/validate'
        },
        'fixes': [
            'v2.1: Fixed silent failures in purchases table inserts',
            'v2.1: Added explicit error checking for all database operations',
            'v2.1: Added detailed logging for debugging',
            'v2.1: Added schema validation endpoint'
        ]
    })


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test Supabase connection
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


# ========== MARKET ENDPOINTS ==========

@app.route('/api/markets', methods=['GET'])
def get_markets():
    """Get all markets"""
    try:
        result = supabase.table('markets').select('*').execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/markets/<string:market_id>', methods=['GET'])
def get_market(market_id):
    """Get specific market by market_id"""
    try:
        result = supabase.table('markets').select('*').eq('market_id', market_id).execute()
        if not result.data:
            return jsonify({'error': 'Market not found'}), 404
        return jsonify(result.data[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/markets/<string:market_id>/products', methods=['GET'])
def get_market_products(market_id):
    """Get unique products for a specific market (latest prices only)"""
    try:
        # Verify market exists
        market_result = supabase.table('markets').select('*').eq('market_id', market_id).execute()
        if not market_result.data:
            return jsonify({'error': 'Market not found'}), 404
        
        # Get unique products
        products_result = supabase.table('unique_products').select('*').eq('market_id', market_id).execute()
        
        return jsonify({
            'market': market_result.data[0],
            'products': products_result.data,
            'total': len(products_result.data)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch products: {e}'}), 500


# ========== NFCe INTEGRATION ENDPOINT ==========

@app.route('/api/nfce/extract', methods=['POST'])
def extract_nfce():
    """
    Extract data from NFCe URL and save to databases
    Request body: { "url": "...", "save": true/false, "async": true/false }
    
    If async=true: Returns immediately (202), processes in background
    If async=false or not set: Synchronous processing (backward compatible)
    """
    data = request.get_json()
    
    if not data.get('url'):
        return jsonify({'error': 'NFCe URL is required'}), 400
    
    # Check if async mode requested (new behavior)
    use_async = data.get('async', False)
    
    # ========== PATH 1: ASYNC MODE (New - Returns Immediately) ==========
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
                'products_count': 0,
                'status': 'processing',
                'processed_at': datetime.utcnow().isoformat()
            }
            url_insert = supabase.table('processed_urls').insert(temp_url_data).execute()
            url_record_id = url_insert.data[0]['id']
            print(f"✓ URL marked as processing (ID: {url_record_id})")
            
            # Start background processing
            thread = threading.Thread(
                target=process_nfce_in_background,
                args=(data['url'], url_record_id),
                daemon=True
            )
            thread.start()
            print(f"✓ Background thread started")
            
            # Return immediately (don't wait)
            return jsonify({
                'message': 'NFCe URL accepted successfully! Processing started.',
                'status': 'processing',
                'url_record_id': url_record_id,
                'check_status_at': f'/api/nfce/status/{data["url"]}',
                'estimated_time': '15-20 seconds'
            }), 202
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to start processing: {str(e)}'}), 500
    
    # ========== PATH 2: SYNC MODE (Backward Compatible - Android App) ==========
    else:
        url_record_id = None
        try:
            # For save=true, check duplicate and record URL
            if data.get('save'):
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
                    'products_count': 0,
                    'status': 'processing',
                    'processed_at': datetime.utcnow().isoformat()
                }
                url_insert = supabase.table('processed_urls').insert(temp_url_data).execute()
                url_record_id = url_insert.data[0]['id']
            
            # Import crawler
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from nfce_extractor import extract_full_nfce_data
            
            # Extract NFCe data synchronously
            result = extract_full_nfce_data(data['url'], headless=True)
            
            market_info = result.get('market_info', {})
            products = result.get('products', [])
            
            if not products:
                if url_record_id:
                    supabase.table('processed_urls').update({'status': 'error'}).eq('id', url_record_id).execute()
                return jsonify({'error': 'No products extracted from NFCe'}), 400
            
            # If save=true, save to database
            if data.get('save'):
                if not market_info.get('name') or not market_info.get('address'):
                    if url_record_id:
                        supabase.table('processed_urls').update({'status': 'error'}).eq('id', url_record_id).execute()
                    return jsonify({'error': 'Could not extract market information'}), 400
                
                # Check/create market
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
                
                # Save products
                save_result = save_products_to_supabase(market['market_id'], products, data['url'])
                
                # Update URL record
                if url_record_id:
                    update_data = {
                        'market_id': market['market_id'],
                        'products_count': len(products),
                        'status': 'success'
                    }
                    supabase.table('processed_urls').update(update_data).eq('id', url_record_id).execute()
                
                # Return full response (backward compatible with Android)
                return jsonify({
                    'message': 'NFCe data extracted and saved successfully',
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
                        'market_action': market_action
                    }
                }), 201
            else:
                # Return extracted data without saving
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


# ========== UTILITY ENDPOINTS ==========

@app.route('/api/nfce/status/<path:nfce_url>', methods=['GET'])
def check_nfce_status(nfce_url):
    """Check processing status of an NFCe URL"""
    try:
        result = supabase.table('processed_urls').select('*').eq('nfce_url', nfce_url).execute()
        
        if not result.data:
            return jsonify({'status': 'not_found', 'message': 'URL not processed yet'}), 404
        
        url_data = result.data[0]
        return jsonify({
            'status': url_data['status'],
            'market_id': url_data['market_id'],
            'products_count': url_data['products_count'],
            'processed_at': url_data['processed_at']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        markets_result = supabase.table('markets').select('id').execute()
        purchases_result = supabase.table('purchases').select('id').execute()
        unique_result = supabase.table('unique_products').select('id').execute()
        
        return jsonify({
            'total_markets': len(markets_result.data),
            'total_purchases': len(purchases_result.data),
            'total_unique_products': len(unique_result.data),
            'architecture': 'Supabase PostgreSQL - 3-Table Design',
            'status': 'connected'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'hint': 'Tables may not exist yet. Run SQL migrations in Supabase.',
            'total_markets': 0,
            'total_purchases': 0,
            'total_unique_products': 0
        }), 500


@app.route('/api/schema/validate', methods=['GET'])
def validate_schema():
    """
    Validate database schema - checks if all required columns exist
    Useful for debugging silent insert failures
    """
    try:
        validation = validate_database_schema()
        
        if validation['valid']:
            return jsonify({
                'status': 'valid',
                'message': 'Database schema is correctly configured',
                'details': validation
            }), 200
        else:
            return jsonify({
                'status': 'invalid',
                'message': 'Database schema has issues',
                'details': validation,
                'action_required': 'Run add_product_name_migration.sql in Supabase SQL Editor'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Schema validation failed: {str(e)}',
            'action_required': 'Check database connectivity and table existence'
        }), 500


if __name__ == '__main__':
    import io
    
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Run Flask app
    print("\n" + "=" * 77)
    print(" AppPrecos Backend API V2 - 3-Table Architecture")
    print("=" * 77)
    print("\n Architecture: markets, purchases, unique_products, processed_urls")
    print(" Storage: Supabase PostgreSQL Cloud Database")
    print("\n Server: http://localhost:5000")
    print(" Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
