"""
AppPrecos Backend API - Version 2
Multi-database architecture: Using Supabase PostgreSQL
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, text
from datetime import datetime
import os
import uuid
import string
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Supabase configuration
from supabase_config import get_supabase_admin_client, get_database_url

# Initialize Flask app
app = Flask(__name__)

# Supabase PostgreSQL configuration
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# Initialize database
db = SQLAlchemy(app)

# Get Supabase admin client
supabase = get_supabase_admin_client()


# ==================== MAIN DATABASE MODELS ====================

class ProcessedURL(db.Model):
    """Tracks processed NFCe URLs to prevent duplicates"""
    __tablename__ = 'processed_urls'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nfce_url = db.Column(db.String(1000), unique=True, nullable=False, index=True)
    market_id = db.Column(db.String(20), nullable=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    products_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nfce_url': self.nfce_url,
            'market_id': self.market_id,
            'processed_at': self.processed_at.isoformat(),
            'products_count': self.products_count
        }


class Market(db.Model):
    """Stores market metadata in main database"""
    __tablename__ = 'markets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    market_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Random ID
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: combination of name + address must be unique
    __table_args__ = (
        db.UniqueConstraint('name', 'address', name='unique_market_name_address'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'market_id': self.market_id,
            'name': self.name,
            'address': self.address,
            'created_at': self.created_at.isoformat()
        }


# ==================== UTILITY FUNCTIONS ====================

def generate_market_id():
    """Generate a random unique market ID (format: MKT + 8 random chars)"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"MKT{random_part}"


def create_market_tables():
    """Create necessary tables in Supabase PostgreSQL"""
    with app.app_context():
        db.create_all()
        print("[OK] Market tables created in Supabase PostgreSQL")


def save_products_to_supabase(market_id, products, nfce_url, purchase_date=None):
    """
    Save products to Supabase PostgreSQL database
    Maintains both full history and unique product tracking
    """
    if purchase_date is None:
        purchase_date = datetime.utcnow()
    
    try:
        # Insert to main products table (full history)
        for product in products:
            data = {
                'market_id': market_id,
                'ncm': product['ncm'],
                'quantity': product.get('quantity', 0),
                'unidade_comercial': product.get('unidade_comercial', 'UN'),
                'price': product.get('price', 0),
                'nfce_url': nfce_url,
                'purchase_date': purchase_date.isoformat(),
                'product_type': 'full_history'
            }
            supabase.table('products').insert(data).execute()
        
        # Upsert to unique products table (latest data only)
        saved_count = len(products)
        updated_unique_count = 0
        created_unique_count = 0
        
        for product in products:
            unique_data = {
                'market_id': market_id,
                'ncm': product['ncm'],
                'quantity': product.get('quantity', 0),
                'unidade_comercial': product.get('unidade_comercial', 'UN'),
                'price': product.get('price', 0),
                'nfce_url': nfce_url,
                'purchase_date': purchase_date.isoformat(),
                'product_type': 'unique'
            }
            
            # Check if exists
            response = supabase.table('products').select('id').match({
                'market_id': market_id,
                'ncm': product['ncm'],
                'product_type': 'unique'
            }).execute()
            
            if response.data:
                # Update existing
                supabase.table('products').update(unique_data).eq('id', response.data[0]['id']).execute()
                updated_unique_count += 1
            else:
                # Create new
                supabase.table('products').insert(unique_data).execute()
                created_unique_count += 1
        
        return {
            'saved_to_main': saved_count,
            'updated_unique': updated_unique_count,
            'created_unique': created_unique_count
        }
    
    except Exception as e:
        print(f"Error saving products to Supabase: {e}")
        raise


# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """API information endpoint"""
    return jsonify({
        'name': 'AppPrecos API v2',
        'version': '2.0',
        'architecture': 'Multi-database (one DB per market)',
        'endpoints': {
            'markets': '/api/markets',
            'nfce_extract': '/api/nfce/extract',
            'market_products': '/api/markets/{market_id}/products'
        }
    })


# ========== MARKET ENDPOINTS ==========

@app.route('/api/markets', methods=['GET'])
def get_markets():
    """Get all markets"""
    markets = Market.query.all()
    return jsonify([market.to_dict() for market in markets])


@app.route('/api/markets/<string:market_id>', methods=['GET'])
def get_market(market_id):
    """Get specific market by market_id"""
    market = Market.query.filter_by(market_id=market_id).first_or_404()
    return jsonify(market.to_dict())


@app.route('/api/markets/<string:market_id>/products', methods=['GET'])
def get_market_products(market_id):
    """Get unique products for a specific market from its UNIQUE database"""
    # Verify market exists
    market = Market.query.filter_by(market_id=market_id).first_or_404()
    
    # Get products from market-specific UNIQUE database (not main)
    # This endpoint will now fetch from Supabase directly
    try:
        response = supabase.table('products').select('*').match({
            'market_id': market_id,
            'product_type': 'unique'
        }).execute()
        
        products = response.data
        return jsonify({
            'market': market.to_dict(),
            'products': products,
            'total': len(products)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch products from Supabase: {e}'}), 500


# ========== NFCe INTEGRATION ENDPOINT ==========

@app.route('/api/nfce/extract', methods=['POST'])
def extract_nfce():
    """
    Extract data from NFCe URL and save to databases
    Request body: { "url": "...", "save": true/false }
    
    Process:
    1. Extract market info and products from NFCe
    2. Check if market exists (by name + address)
    3. If NOT exists: Create market with random market_id + create new database
    4. If exists: Use existing market_id and database
    5. Save products to market-specific database
    """
    data = request.get_json()
    
    if not data.get('url'):
        return jsonify({'error': 'NFCe URL is required'}), 400
    
    # CHECK: Has this URL been processed before?
    if data.get('save'):
        existing_url = ProcessedURL.query.filter_by(nfce_url=data['url']).first()
        if existing_url:
            return jsonify({
                'error': 'This NFCe has already been processed',
                'message': 'URL already exists in database',
                'processed_at': existing_url.processed_at.isoformat(),
                'market_id': existing_url.market_id,
                'products_count': existing_url.products_count
            }), 409
    
    try:
        # Import crawler
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from nfce_extractor import extract_full_nfce_data
        
        # Extract complete NFCe data
        result = extract_full_nfce_data(data['url'], headless=True)
        
        market_info = result.get('market_info', {})
        products = result.get('products', [])
        
        if not products:
            return jsonify({'error': 'No products extracted from NFCe'}), 400
        
        market = None
        market_action = None
        
        # If save=true, save to databases
        if data.get('save'):
            if not market_info.get('name') or not market_info.get('address'):
                return jsonify({'error': 'Could not extract market information from NFCe'}), 400
            
            # Check if market exists by name + address
            market = Market.query.filter_by(
                name=market_info['name'],
                address=market_info['address']
            ).first()
            
            if market:
                # Market exists - use existing market_id
                market_action = 'matched'
            else:
                # Create new market with random market_id
                new_market_id = generate_market_id()
                
                # Ensure market_id is unique (very unlikely to collide, but check)
                while Market.query.filter_by(market_id=new_market_id).first():
                    new_market_id = generate_market_id()
                
                market = Market(
                    market_id=new_market_id,
                    name=market_info['name'],
                    address=market_info['address']
                )
                db.session.add(market)
                db.session.flush()
                
                # Create new database for this market
                # This part is now handled by Supabase, so we just commit the market
                db.session.commit()
                
                # Save products to Supabase
                save_result = save_products_to_supabase(
                    market.market_id,
                    products,
                    data['url']
                )
                
                # Record this URL as processed
                processed_url = ProcessedURL(
                    nfce_url=data['url'],
                    market_id=market.market_id,
                    products_count=len(products)
                )
                db.session.add(processed_url)
                db.session.commit()
                
                return jsonify({
                    'message': 'NFCe data extracted and saved successfully',
                    'market': {
                        'id': market.id,
                        'market_id': market.market_id,
                        'name': market.name,
                        'address': market.address,
                        'action': market_action,
                        'database_files': {
                            'main': f"{market.market_id}.db", # This will be removed as per new_code
                            'unique': f"{market.market_id}_unique.db" # This will be removed as per new_code
                        }
                    },
                    'products': products,
                    'statistics': {
                        'products_saved_to_main': save_result['saved_to_main'],
                        'unique_products_updated': save_result['updated_unique'],
                        'unique_products_created': save_result['created_unique'],
                        'market_action': market_action,
                        'database_location': 'Supabase' # This will be removed as per new_code
                    }
                }), 201
        
        # Just return extracted data without saving
        return jsonify({
            'message': 'NFCe data extracted successfully (not saved)',
            'market_info': market_info,
            'products': products
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ========== UTILITY ENDPOINTS ==========

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    total_markets = Market.query.count()
    
    # Count products across all market databases
    total_products = 0
    markets = Market.query.all()
    for market in markets:
        try:
            # This part will now fetch from Supabase directly
            response = supabase.table('products').select('*').match({
                'market_id': market.market_id,
                'product_type': 'unique'
            }).execute()
            count = len(response.data)
            total_products += count
        except:
            pass
    
    return jsonify({
        'total_markets': total_markets,
        'total_products_across_all_markets': total_products,
        'architecture': 'Multi-database (one DB per market)'
    })


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize main database"""
    with app.app_context():
        db.create_all()
        print("[OK] Main database created (markets_main.db)")
        print("[OK] Market tables created in Supabase PostgreSQL")


if __name__ == '__main__':
    import sys
    import io
    
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Create main database
    init_db()
    
    # Run Flask app
    print("\n" + "=" * 77)
    print(" AppPrecos Backend API V2 - Supabase PostgreSQL Architecture")
    print("=" * 77)
    print("\n Architecture: Supabase PostgreSQL Database")
    print(" Main DB: Supabase PostgreSQL (markets_main, products)")
    print(" Markets: Stored in Supabase with unique product tracking")
    print("\n Server: http://localhost:5000")
    print(" Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

