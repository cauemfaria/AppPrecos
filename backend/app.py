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

def generate_market_id():
    """Generate a random unique market ID (format: MKT + 8 random chars)"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"MKT{random_part}"


def save_products_to_supabase(market_id, products, nfce_url, purchase_date=None):
    """
    Save products to Supabase PostgreSQL database
    Maintains both full history (purchases) and latest prices (unique_products)
    All-or-nothing approach: if any insert fails, rollback all changes
    """
    if purchase_date is None:
        purchase_date = datetime.utcnow()
    
    # Track inserted IDs for rollback capability
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
        
        # 1. Insert to PURCHASES table (full history)
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
                    raise Exception(f"Failed to insert product {idx} to purchases table")
                
                inserted_purchase_ids.append(response.data[0]['id'])
                saved_to_purchases += 1
                print(f"  ✓ [{idx}/{len(products)}] {product.get('product', 'Unknown')[:50]}")
                
            except Exception as e:
                print(f"❌ ERROR inserting product {idx}: {str(e)}")
                raise Exception(f"Failed at product {idx}: {str(e)}")
        
        print(f"✓ Inserted {saved_to_purchases} products to PURCHASES\n")
        
        # 2. Upsert to UNIQUE_PRODUCTS table (latest prices)
        print(f"[2/2] Upserting to UNIQUE_PRODUCTS table...")
        
        for idx, product in enumerate(products, 1):
            try:
                unique_data = {
                    'market_id': market_id,
                    'ncm': product['ncm'],
                    'ean': product.get('ean', 'SEM GTIN'),
                    'product_name': product.get('product', ''),
                    'unidade_comercial': product.get('unidade_comercial', 'UN'),
                    'price': product.get('unit_price', 0),
                    'nfce_url': nfce_url,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                # Check if exists
                response = supabase.table('unique_products').select('*').match({
                    'market_id': market_id,
                    'ncm': product['ncm']
                }).execute()
                
                if response.data:
                    old_id = response.data[0]['id']
                    updated_unique_backup[old_id] = response.data[0]
                    
                    update_response = supabase.table('unique_products').update(unique_data).eq('id', old_id).execute()
                    
                    if not update_response.data or len(update_response.data) == 0:
                        raise Exception(f"Failed to update product {idx}")
                    
                    updated_unique += 1
                    print(f"  ↻ [{idx}/{len(products)}] Updated {product.get('product', 'Unknown')[:50]}")
                else:
                    insert_response = supabase.table('unique_products').insert(unique_data).execute()
                    
                    if not insert_response.data or len(insert_response.data) == 0:
                        raise Exception(f"Failed to insert product {idx}")
                    
                    inserted_unique_ids.append(insert_response.data[0]['id'])
                    created_unique += 1
                    print(f"  ✓ [{idx}/{len(products)}] Created {product.get('product', 'Unknown')[:50]}")
                    
            except Exception as e:
                print(f"❌ ERROR upserting product {idx}: {str(e)}")
                raise Exception(f"Failed at product {idx}: {str(e)}")
        
        print(f"\n{'='*60}")
        print(f"✓ COMPLETED: {saved_to_purchases} purchases, {created_unique} new, {updated_unique} updated")
        print(f"{'='*60}\n")
        
        return {
            'saved_to_purchases': saved_to_purchases,
            'updated_unique': updated_unique,
            'created_unique': created_unique
        }
    
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ TRANSACTION FAILED - ROLLING BACK")
        print(f"{'='*60}")
        
        # Rollback purchases
        if inserted_purchase_ids:
            print(f"Rolling back {len(inserted_purchase_ids)} purchases...")
            try:
                for purchase_id in inserted_purchase_ids:
                    supabase.table('purchases').delete().eq('id', purchase_id).execute()
                print(f"✓ Rolled back purchases")
            except Exception as rb_error:
                print(f"✗ Rollback purchases failed: {rb_error}")
        
        # Rollback new unique_products
        if inserted_unique_ids:
            print(f"Rolling back {len(inserted_unique_ids)} unique products...")
            try:
                for unique_id in inserted_unique_ids:
                    supabase.table('unique_products').delete().eq('id', unique_id).execute()
                print(f"✓ Rolled back unique products")
            except Exception as rb_error:
                print(f"✗ Rollback unique_products failed: {rb_error}")
        
        # Restore updated unique_products
        if updated_unique_backup:
            print(f"Restoring {len(updated_unique_backup)} updated products...")
            try:
                for unique_id, old_data in updated_unique_backup.items():
                    restore_data = {k: v for k, v in old_data.items() if k not in ['id', 'created_at']}
                    supabase.table('unique_products').update(restore_data).eq('id', unique_id).execute()
                print(f"✓ Restored updated products")
            except Exception as rb_error:
                print(f"✗ Restore failed: {rb_error}")
        
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
    """Get unique products for a specific market (latest prices only)"""
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
    Request body: { "url": "...", "save": true/false }
    """
    data = request.get_json()
    
    if not data.get('url'):
        return jsonify({'error': 'NFCe URL is required'}), 400
    
    url_record_id = None
    try:
        # Check if save mode requested
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
        
        # Import and run extractor
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from nfce_extractor import extract_full_nfce_data
        
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


if __name__ == '__main__':
    import io
    
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "=" * 50)
    print(" AppPrecos Backend API")
    print("=" * 50)
    print("\n Server: http://localhost:5000")
    print(" Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
