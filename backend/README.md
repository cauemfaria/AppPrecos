# AppPrecos Backend API

Flask REST API with NFCe crawler integration and multi-database architecture.

## Features

- REST API for market and product management
- Automatic NFCe receipt data extraction
- **Multi-database architecture** (one database per market)
- Automatic market matching by name + address
- Random market ID generation
- Product data isolation per market

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Run server
python app.py
```

Server runs at: `http://localhost:5000`

## Project Structure

```
backend/
├── app.py                    # Main Flask app (multi-database architecture)
├── nfce_extractor.py         # NFCe crawler module with market extraction
├── nfce_crawler_ultimate.py  # Standalone crawler (with Excel export)
├── config.py                 # Configuration
├── requirements.txt          # Python dependencies
├── markets_main.db          # Main database (market metadata)
├── market_databases/        # Market-specific databases
│   ├── MKT*******.db        # One database per market
│   └── ...
└── .gitignore
```

## API Documentation

See `../docs/API_REFERENCE.md` for complete API documentation.

## Database Architecture

**Multi-Database Design:**
- **Main Database** (`markets_main.db`) - Stores market metadata
  - Table: `markets` (id, market_id, name, address, created_at)
  
- **Market Databases** (`market_databases/{MARKET_ID}.db`) - One per market
  - Table: `products` (id, ncm, quantity, unidade_comercial, price, nfce_url, purchase_date, created_at)

**Benefits:**
- Data isolation per market
- Scalability (distributed storage)
- Easy to backup individual markets
- No cross-market data pollution

See `../docs/DATABASE_SCHEMA.md` for complete schema details.

## NFCe Extraction

The crawler uses Playwright to:
1. Navigate to NFCe URL
2. Click "Visualizar em Abas" button
3. Extract all NCM codes from HTML
4. Parse product names, quantities, prices

**Time:** ~10-15 seconds per receipt
**Success Rate:** ~100% (when page loads correctly)

## Configuration

Copy `config.py` and modify as needed:
- Database URL
- Secret key
- Debug mode

## Deployment

See `../docs/DEPLOYMENT.md` for production deployment guide.

## Testing

Test the crawler:
```bash
python nfce_crawler_ultimate.py
```

Results saved to `ncm_codes.xlsx`
