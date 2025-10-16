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


# ==================== MAIN DATABASE MODEL (Market Metadata) ====================

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
    """Create a new database for a market with proper schema"""
    db_path = get_market_db_path(market_id)
    
    # Create engine for new database
    engine = create_engine(f'sqlite:///{db_path}')
    
    # Create schema
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
    
    return db_path


def get_market_db_connection(market_id):
    """Get database connection for a specific market"""
    db_path = get_market_db_path(market_id)
    
    if not os.path.exists(db_path):
        create_market_database(market_id)
    
    return create_engine(f'sqlite:///{db_path}')


def save_products_to_market_db(market_id, products, nfce_url, purchase_date=None):
    """Save products to market-specific database"""
    engine = get_market_db_connection(market_id)
    
    if purchase_date is None:
        purchase_date = datetime.utcnow()
    
    saved_count = 0
    
    with engine.connect() as conn:
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
    
    return saved_count


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
    """Get all products for a specific market from its database"""
    # Verify market exists
    market = Market.query.filter_by(market_id=market_id).first_or_404()
    
    # Get products from market-specific database
    engine = get_market_db_connection(market_id)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM products ORDER BY created_at DESC"))
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
            
            # Save products to market-specific database
            products_saved = save_products_to_market_db(
                market.market_id,
                products,
                data['url']
            )
            
            return jsonify({
                'message': 'NFCe data extracted and saved successfully',
                'market': {
                    'id': market.id,
                    'market_id': market.market_id,
                    'name': market.name,
                    'address': market.address,
                    'action': market_action,
                    'database_file': f"{market.market_id}.db"
                },
                'products': products,
                'statistics': {
                    'products_saved': products_saved,
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

