# AppPrecos Backend API

Flask REST API with NFCe crawler integration and SQLAlchemy ORM.

## Features

- REST API for market and product management
- Automatic NFCe receipt data extraction
- SQLite (dev) / PostgreSQL (prod) support
- Price comparison across markets
- Automatic product deduplication

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
├── app.py                    # Main Flask app (models + routes)
├── nfce_extractor.py         # NFCe crawler module
├── nfce_crawler_ultimate.py  # Standalone crawler (with Excel export)
├── config.py                 # Configuration
├── requirements.txt          # Python dependencies
├── appprecos.db             # SQLite database (generated)
└── .gitignore
```

## API Documentation

See `../docs/API_REFERENCE.md` for complete API documentation.

## Database

See `../docs/DATABASE_SCHEMA.md` for database schema details.

**Tables:**
- `markets` - Store information
- `purchases` - Complete purchase history
- `unique_products` - Latest price per product per market

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
