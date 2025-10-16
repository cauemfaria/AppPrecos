# AppPrecos Architecture

## System Overview

AppPrecos is a price comparison application for Brazilian markets, using NFCe receipt data.

```
┌─────────────────┐
│  Android App    │
│  (Kotlin)       │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│  Flask Backend  │
│  (Python)       │
├─────────────────┤
│  - REST API     │
│  - NFCe Crawler │
│  - SQLAlchemy   │
└────────┬────────┘
         │
         │ SQL
         │
┌────────▼────────┐
│  Database       │
│  SQLite/Postgres│
└─────────────────┘
```

## Components

### 1. Android App (`android/`)

**Technology:** Kotlin, AndroidX, Material Design 3

**Responsibilities:**
- User interface
- QR code scanning
- API communication
- Local data caching (optional)
- Price comparison display

**Key Features:**
- Scan NFCe QR codes
- Send URL to backend
- Display product prices
- Compare prices across markets
- Save favorite products

---

### 2. Backend API (`backend/`)

**Technology:** Flask, SQLAlchemy, Playwright

**Responsibilities:**
- REST API endpoints
- NFCe data extraction
- Database management
- Business logic

**Components:**

#### `app.py`
- Flask application setup
- All API routes
- Database models (Market, Purchase, UniqueProduct)

#### `nfce_extractor.py`
- Playwright-based web crawler
- Extracts NCM codes from NFCe URLs
- Returns structured product data

#### `nfce_crawler_ultimate.py`
- Standalone crawler with Excel export
- Can be run independently for testing

---

### 3. Database

**Development:** SQLite (`appprecos.db`)
**Production:** PostgreSQL (recommended)

**Design:**
- Normalized schema
- Foreign key constraints
- Cascade deletes
- Automatic timestamp management

---

## Data Flow

### NFCe Receipt Processing

```
1. User scans QR code with Android app
   ↓
2. App extracts NFCe URL from QR code
   ↓
3. App sends URL to backend:
   POST /api/nfce/extract
   {
     "url": "https://nfce.fazenda.sp.gov.br/...",
     "market_id": 1,
     "save": true
   }
   ↓
4. Backend:
   a. Launches headless browser (Playwright)
   b. Navigates to NFCe URL
   c. Clicks "Visualizar em Abas" button
   d. Extracts all NCM codes from HTML
   e. Parses product names, quantities, prices
   ↓
5. Backend saves to database:
   a. Inserts into purchases table (history)
   b. Updates/inserts into unique_products table (latest)
   ↓
6. Backend returns JSON to Android
   {
     "products": [ {...}, {...} ],
     "saved_to_market": 1
   }
   ↓
7. Android displays products to user
```

### Price Comparison

```
1. User searches for product (by NCM or name)
   ↓
2. App requests: GET /api/price-comparison/{ncm}
   ↓
3. Backend queries unique_products table
   ↓
4. Joins with markets table
   ↓
5. Sorts by price (ascending)
   ↓
6. Returns list of markets with prices
   ↓
7. Android displays comparison:
   "Market A: R$ 1.99"
   "Market B: R$ 2.50"
   "Market C: R$ 2.75"
```

---

## Security Considerations

### Current (POC):
- No authentication
- Local network only
- SQLite database

### Production Recommendations:
- Add API authentication (JWT tokens)
- Use HTTPS
- Rate limiting on NFCe extraction
- PostgreSQL with proper credentials
- Input validation and sanitization

---

## Performance

### NFCe Extraction:
- **Time:** ~10-15 seconds per receipt
- **Bottleneck:** Browser automation (unavoidable)
- **Optimization:** Run headless, cache results

### API Response Times:
- **Market queries:** <50ms
- **Purchase queries:** <100ms
- **Price comparison:** <200ms

### Scalability:
- **Current:** Single-threaded Flask (dev server)
- **Production:** Use Gunicorn with multiple workers
- **Database:** Add indexes on frequently queried columns

---

## Future Enhancements

1. **Product Name Matching**
   - Map NCM codes to product names
   - Search by product name instead of just NCM

2. **Price History Charts**
   - Track price trends over time
   - Show price fluctuations

3. **User Accounts**
   - Save favorite markets
   - Personalized price alerts

4. **Caching Layer**
   - Redis for frequently accessed data
   - Cache NFCe extractions

5. **Async Processing**
   - Queue NFCe extractions (Celery)
   - Process receipts in background

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Android | Kotlin | 1.9.20 |
| Android UI | Material Design 3 | 1.11.0 |
| Backend | Flask | 3.0.0 |
| ORM | SQLAlchemy | 3.1.1 |
| Web Automation | Playwright | 1.55.0 |
| Database (Dev) | SQLite | 3 |
| Database (Prod) | PostgreSQL | 14+ |

