"""
AppPrecos Backend API
Flask application with SQLAlchemy for managing markets and product prices
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "appprecos.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False  # Support Portuguese characters

# Initialize database
db = SQLAlchemy(app)


# ==================== DATABASE MODELS ====================

class Market(db.Model):
    """Stores market information"""
    __tablename__ = 'markets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    purchases = db.relationship('Purchase', backref='market', lazy=True, cascade='all, delete-orphan')
    unique_products = db.relationship('UniqueProduct', backref='market', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'created_at': self.created_at.isoformat()
        }


class Purchase(db.Model):
    """Stores all purchase records for each market"""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    market_id = db.Column(db.Integer, db.ForeignKey('markets.id'), nullable=False)
    ncm = db.Column(db.String(8), nullable=False, index=True)
    quantity = db.Column(db.Float, nullable=False)
    unidade_comercial = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Float, nullable=False)
    nfce_url = db.Column(db.String(1000), nullable=True)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'market_id': self.market_id,
            'ncm': self.ncm,
            'quantity': self.quantity,
            'unidade_comercial': self.unidade_comercial,
            'price': self.price,
            'nfce_url': self.nfce_url,
            'purchase_date': self.purchase_date.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class UniqueProduct(db.Model):
    """Stores unique products (latest price) for each market"""
    __tablename__ = 'unique_products'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    market_id = db.Column(db.Integer, db.ForeignKey('markets.id'), nullable=False)
    ncm = db.Column(db.String(8), nullable=False, index=True)
    unidade_comercial = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Float, nullable=False)
    nfce_url = db.Column(db.String(1000), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure one NCM per market
    __table_args__ = (
        db.UniqueConstraint('market_id', 'ncm', name='unique_market_ncm'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'market_id': self.market_id,
            'ncm': self.ncm,
            'unidade_comercial': self.unidade_comercial,
            'price': self.price,
            'nfce_url': self.nfce_url,
            'last_updated': self.last_updated.isoformat()
        }


# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """API information endpoint"""
    return jsonify({
        'name': 'AppPrecos API',
        'version': '1.0',
        'endpoints': {
            'markets': '/api/markets',
            'purchases': '/api/purchases',
            'unique_products': '/api/unique-products'
        }
    })


# ========== MARKET ENDPOINTS ==========

@app.route('/api/markets', methods=['GET'])
def get_markets():
    """Get all markets"""
    markets = Market.query.all()
    return jsonify([market.to_dict() for market in markets])


@app.route('/api/markets', methods=['POST'])
def create_market():
    """Create a new market"""
    data = request.get_json()
    
    if not data.get('name') or not data.get('address'):
        return jsonify({'error': 'Name and address are required'}), 400
    
    market = Market(
        name=data['name'],
        address=data['address']
    )
    
    db.session.add(market)
    db.session.commit()
    
    return jsonify(market.to_dict()), 201


@app.route('/api/markets/<int:market_id>', methods=['GET'])
def get_market(market_id):
    """Get specific market"""
    market = Market.query.get_or_404(market_id)
    return jsonify(market.to_dict())


@app.route('/api/markets/<int:market_id>', methods=['DELETE'])
def delete_market(market_id):
    """Delete a market (cascades to purchases and unique_products)"""
    market = Market.query.get_or_404(market_id)
    db.session.delete(market)
    db.session.commit()
    return jsonify({'message': 'Market deleted successfully'})


# ========== PURCHASE ENDPOINTS ==========

@app.route('/api/purchases', methods=['GET'])
def get_purchases():
    """Get all purchases (optionally filter by market_id)"""
    market_id = request.args.get('market_id', type=int)
    
    if market_id:
        purchases = Purchase.query.filter_by(market_id=market_id).all()
    else:
        purchases = Purchase.query.all()
    
    return jsonify([purchase.to_dict() for purchase in purchases])


@app.route('/api/purchases', methods=['POST'])
def add_purchase():
    """
    Add a new purchase and update unique_products table
    Automatically handles unique product updates
    """
    data = request.get_json()
    
    # Validate required fields
    required = ['market_id', 'ncm', 'quantity', 'unidade_comercial', 'price']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if market exists
    market = Market.query.get(data['market_id'])
    if not market:
        return jsonify({'error': 'Market not found'}), 404
    
    # Create purchase record
    purchase = Purchase(
        market_id=data['market_id'],
        ncm=data['ncm'],
        quantity=data['quantity'],
        unidade_comercial=data['unidade_comercial'],
        price=data['price'],
        nfce_url=data.get('nfce_url'),
        purchase_date=datetime.fromisoformat(data['purchase_date']) if data.get('purchase_date') else datetime.utcnow()
    )
    
    db.session.add(purchase)
    
    # Update or create unique product
    unique_product = UniqueProduct.query.filter_by(
        market_id=data['market_id'],
        ncm=data['ncm']
    ).first()
    
    if unique_product:
        # Update existing product
        unique_product.unidade_comercial = data['unidade_comercial']
        unique_product.price = data['price']
        unique_product.nfce_url = data.get('nfce_url')
        unique_product.last_updated = datetime.utcnow()
    else:
        # Create new unique product
        unique_product = UniqueProduct(
            market_id=data['market_id'],
            ncm=data['ncm'],
            unidade_comercial=data['unidade_comercial'],
            price=data['price'],
            nfce_url=data.get('nfce_url')
        )
        db.session.add(unique_product)
    
    db.session.commit()
    
    return jsonify({
        'purchase': purchase.to_dict(),
        'unique_product': unique_product.to_dict()
    }), 201


@app.route('/api/purchases/bulk', methods=['POST'])
def add_bulk_purchases():
    """Add multiple purchases at once (for NFCe import)"""
    data = request.get_json()
    
    if not data.get('market_id') or not data.get('products'):
        return jsonify({'error': 'market_id and products array required'}), 400
    
    market_id = data['market_id']
    products = data['products']
    nfce_url = data.get('nfce_url')
    
    # Check if market exists
    market = Market.query.get(market_id)
    if not market:
        return jsonify({'error': 'Market not found'}), 404
    
    added_purchases = []
    updated_unique = []
    
    for product in products:
        try:
            # Create purchase
            purchase = Purchase(
                market_id=market_id,
                ncm=product['ncm'],
                quantity=product.get('quantity', 0),
                unidade_comercial=product.get('unidade_comercial', 'UN'),
                price=product.get('price', 0),
                nfce_url=nfce_url
            )
            db.session.add(purchase)
            added_purchases.append(purchase)
            
            # Update unique product
            unique_product = UniqueProduct.query.filter_by(
                market_id=market_id,
                ncm=product['ncm']
            ).first()
            
            if unique_product:
                unique_product.unidade_comercial = product.get('unidade_comercial', unique_product.unidade_comercial)
                unique_product.price = product.get('price', unique_product.price)
                unique_product.nfce_url = nfce_url
                unique_product.last_updated = datetime.utcnow()
            else:
                unique_product = UniqueProduct(
                    market_id=market_id,
                    ncm=product['ncm'],
                    unidade_comercial=product.get('unidade_comercial', 'UN'),
                    price=product.get('price', 0),
                    nfce_url=nfce_url
                )
                db.session.add(unique_product)
            
            updated_unique.append(unique_product)
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Error processing product: {str(e)}'}), 500
    
    db.session.commit()
    
    return jsonify({
        'message': f'Successfully added {len(added_purchases)} purchases',
        'purchases_added': len(added_purchases),
        'unique_products_updated': len(updated_unique)
    }), 201


# ========== UNIQUE PRODUCTS ENDPOINTS ==========

@app.route('/api/unique-products', methods=['GET'])
def get_unique_products():
    """Get unique products (optionally filter by market_id)"""
    market_id = request.args.get('market_id', type=int)
    
    if market_id:
        products = UniqueProduct.query.filter_by(market_id=market_id).all()
    else:
        products = UniqueProduct.query.all()
    
    return jsonify([product.to_dict() for product in products])


@app.route('/api/unique-products/<string:ncm>', methods=['GET'])
def get_product_by_ncm(ncm):
    """Get all markets selling a specific NCM product"""
    market_id = request.args.get('market_id', type=int)
    
    if market_id:
        products = UniqueProduct.query.filter_by(ncm=ncm, market_id=market_id).all()
    else:
        products = UniqueProduct.query.filter_by(ncm=ncm).all()
    
    return jsonify([product.to_dict() for product in products])


# ========== NFCe INTEGRATION ENDPOINT ==========

@app.route('/api/nfce/extract', methods=['POST'])
def extract_nfce():
    """
    Extract NCM codes from NFCe URL and optionally save to database
    Request body: { "url": "...", "market_id": 123, "save": true/false }
    """
    data = request.get_json()
    
    if not data.get('url'):
        return jsonify({'error': 'NFCe URL is required'}), 400
    
    try:
        # Import crawler
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from nfce_extractor import extract_ncm_from_url
        
        # Extract NCM codes
        ncm_products = extract_ncm_from_url(data['url'])
        
        if not ncm_products:
            return jsonify({'error': 'No products extracted from NFCe'}), 400
        
        # If save=true and market_id provided, save to database
        if data.get('save') and data.get('market_id'):
            market_id = data['market_id']
            
            # Check if market exists
            market = Market.query.get(market_id)
            if not market:
                return jsonify({'error': 'Market not found'}), 404
            
            # Save products
            for product in ncm_products:
                # Create purchase
                purchase = Purchase(
                    market_id=market_id,
                    ncm=product['ncm'],
                    quantity=product.get('quantity', 0),
                    unidade_comercial=product.get('unidade_comercial', 'UN'),
                    price=product.get('price', 0),
                    nfce_url=data['url']
                )
                db.session.add(purchase)
                
                # Update unique product
                unique_product = UniqueProduct.query.filter_by(
                    market_id=market_id,
                    ncm=product['ncm']
                ).first()
                
                if unique_product:
                    unique_product.unidade_comercial = product.get('unidade_comercial', unique_product.unidade_comercial)
                    unique_product.price = product.get('price', unique_product.price)
                    unique_product.nfce_url = data['url']
                    unique_product.last_updated = datetime.utcnow()
                else:
                    unique_product = UniqueProduct(
                        market_id=market_id,
                        ncm=product['ncm'],
                        unidade_comercial=product.get('unidade_comercial', 'UN'),
                        price=product.get('price', 0),
                        nfce_url=data['url']
                    )
                    db.session.add(unique_product)
            
            db.session.commit()
            
            return jsonify({
                'message': 'NCM codes extracted and saved successfully',
                'products': ncm_products,
                'saved_to_market': market_id
            }), 201
        
        # Just return extracted data without saving
        return jsonify({
            'message': 'NCM codes extracted successfully',
            'products': ncm_products
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ========== UTILITY ENDPOINTS ==========

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    return jsonify({
        'total_markets': Market.query.count(),
        'total_purchases': Purchase.query.count(),
        'total_unique_products': UniqueProduct.query.count()
    })


@app.route('/api/price-comparison/<string:ncm>', methods=['GET'])
def compare_prices(ncm):
    """Compare prices for a specific NCM across all markets"""
    products = UniqueProduct.query.filter_by(ncm=ncm).all()
    
    if not products:
        return jsonify({'error': 'Product not found in any market'}), 404
    
    # Get market info for each product
    results = []
    for product in products:
        market = Market.query.get(product.market_id)
        results.append({
            'market_id': market.id,
            'market_name': market.name,
            'market_address': market.address,
            'ncm': product.ncm,
            'price': product.price,
            'unidade_comercial': product.unidade_comercial,
            'last_updated': product.last_updated.isoformat()
        })
    
    # Sort by price (cheapest first)
    results.sort(key=lambda x: x['price'])
    
    return jsonify({
        'ncm': ncm,
        'markets_count': len(results),
        'cheapest_price': results[0]['price'] if results else None,
        'results': results
    })


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize database tables"""
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully")


if __name__ == '__main__':
    # Create database tables
    init_db()
    
    # Run Flask app
    print("\n" + "=" * 77)
    print(" AppPrecos Backend API - Starting...")
    print("=" * 77)
    print("\n Server running at: http://localhost:5000")
    print(" Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

