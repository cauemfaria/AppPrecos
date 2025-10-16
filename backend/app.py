"""
AppPrecos Backend API - Version 2
Multi-database architecture: Each market gets its own database
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, text
from datetime import datetime
import os
import uuid
import string
import random

# Initialize Flask app
app = Flask(__name__)

# Main database configuration (stores market metadata only)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "markets_main.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

# Initialize main database
db = SQLAlchemy(app)


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


def get_market_db_path(market_id):
    """Get the database file path for a specific market"""
    db_dir = os.path.join(basedir, "market_databases")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, f"{market_id}.db")


def create_market_database(market_id):
    """Create TWO databases for a market: main and unique"""
    db_path = get_market_db_path(market_id)
    
    # Create main database (all purchases - history)
    engine = create_engine(f'sqlite:///{db_path}')
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ncm VARCHAR(8) NOT NULL,
                quantity FLOAT NOT NULL,
                unidade_comercial VARCHAR(10) NOT NULL,
                price FLOAT NOT NULL,
                nfce_url VARCHAR(1000),
                purchase_date DATETIME NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    
    # Create unique database (unique NCM codes - latest data only)
    unique_db_path = db_path.replace('.db', '_unique.db')
    engine_unique = create_engine(f'sqlite:///{unique_db_path}')
    with engine_unique.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ncm VARCHAR(8) NOT NULL UNIQUE,
                quantity FLOAT NOT NULL,
                unidade_comercial VARCHAR(10) NOT NULL,
                price FLOAT NOT NULL,
                nfce_url VARCHAR(1000),
                purchase_date DATETIME NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    
    return db_path


def get_market_db_connection(market_id):
    """Get database connection for a specific market"""
    db_path = get_market_db_path(market_id)
    
    if not os.path.exists(db_path):
        create_market_database(market_id)
    
    return create_engine(f'sqlite:///{db_path}')


def save_products_to_market_db(market_id, products, nfce_url, purchase_date=None):
    """
    Save products to TWO market-specific databases:
    1. {MARKET_ID}.db - All purchases (history)
    2. {MARKET_ID}_unique.db - Unique NCM codes (latest data only)
    """
    if purchase_date is None:
        purchase_date = datetime.utcnow()
    
    # Get both database connections
    db_path = get_market_db_path(market_id)
    unique_db_path = db_path.replace('.db', '_unique.db')
    
    engine_main = create_engine(f'sqlite:///{db_path}')
    engine_unique = create_engine(f'sqlite:///{unique_db_path}')
    
    saved_count = 0
    updated_unique_count = 0
    created_unique_count = 0
    
    # Save to MAIN database (all purchases - always INSERT)
    with engine_main.connect() as conn:
        for product in products:
            conn.execute(text("""
                INSERT INTO products (ncm, quantity, unidade_comercial, price, nfce_url, purchase_date)
                VALUES (:ncm, :quantity, :unit, :price, :url, :date)
            """), {
                'ncm': product['ncm'],
                'quantity': product.get('quantity', 0),
                'unit': product.get('unidade_comercial', 'UN'),
                'price': product.get('price', 0),
                'url': nfce_url,
                'date': purchase_date
            })
            saved_count += 1
        conn.commit()
    
    # Save/Update to UNIQUE database (unique NCM codes - UPSERT)
    with engine_unique.connect() as conn:
        for product in products:
            ncm = product['ncm']
            
            # Check if NCM already exists
            result = conn.execute(text("""
                SELECT id FROM products WHERE ncm = :ncm
            """), {'ncm': ncm})
            
            existing = result.fetchone()
            
            if existing:
                # UPDATE existing row
                conn.execute(text("""
                    UPDATE products 
                    SET quantity = :quantity,
                        unidade_comercial = :unit,
                        price = :price,
                        nfce_url = :url,
                        purchase_date = :date
                    WHERE ncm = :ncm
                """), {
                    'ncm': ncm,
                    'quantity': product.get('quantity', 0),
                    'unit': product.get('unidade_comercial', 'UN'),
                    'price': product.get('price', 0),
                    'url': nfce_url,
                    'date': purchase_date
                })
                updated_unique_count += 1
            else:
                # INSERT new row
                conn.execute(text("""
                    INSERT INTO products (ncm, quantity, unidade_comercial, price, nfce_url, purchase_date)
                    VALUES (:ncm, :quantity, :unit, :price, :url, :date)
                """), {
                    'ncm': ncm,
                    'quantity': product.get('quantity', 0),
                    'unit': product.get('unidade_comercial', 'UN'),
                    'price': product.get('price', 0),
                    'url': nfce_url,
                    'date': purchase_date
                })
                created_unique_count += 1
        
        conn.commit()
    
    return {
        'saved_to_main': saved_count,
        'updated_unique': updated_unique_count,
        'created_unique': created_unique_count
    }


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
    db_path = get_market_db_path(market_id)
    unique_db_path = db_path.replace('.db', '_unique.db')
    engine_unique = create_engine(f'sqlite:///{unique_db_path}')
    
    with engine_unique.connect() as conn:
        result = conn.execute(text("SELECT * FROM products ORDER BY ncm"))
        products = []
        for row in result:
            products.append({
                'id': row[0],
                'ncm': row[1],
                'quantity': row[2],
                'unidade_comercial': row[3],
                'price': row[4],
                'nfce_url': row[5],
                'purchase_date': row[6],
                'created_at': row[7]
            })
    
    return jsonify({
        'market': market.to_dict(),
        'products': products,
        'total': len(products)
    })


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
                db_path = create_market_database(new_market_id)
                market_action = 'created'
            
            # Save to main database
            db.session.commit()
            
            # Save products to market-specific databases
            save_result = save_products_to_market_db(
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
                        'main': f"{market.market_id}.db",
                        'unique': f"{market.market_id}_unique.db"
                    }
                },
                'products': products,
                'statistics': {
                    'products_saved_to_main': save_result['saved_to_main'],
                    'unique_products_updated': save_result['updated_unique'],
                    'unique_products_created': save_result['created_unique'],
                    'market_action': market_action,
                    'database_location': get_market_db_path(market.market_id)
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
            engine = get_market_db_connection(market.market_id)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM products"))
                count = result.fetchone()[0]
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
        print("[OK] Market-specific databases will be created as needed")


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
    print(" AppPrecos Backend API V2 - Multi-Database Architecture")
    print("=" * 77)
    print("\n Architecture: Each market = Separate database")
    print(" Main DB: markets_main.db (market metadata)")
    print(" Market DBs: market_databases/{MARKET_ID}.db")
    print("\n Server: http://localhost:5000")
    print(" Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

