# AppPrecos - Brazilian Price Comparison App

Price comparison application that extracts product data from NFCe receipts and helps consumers find the best prices across multiple markets.

---

## Overview

AppPrecos automatically extracts product information from Brazilian electronic receipts (NFC-e) by scanning QR codes. The app compares prices across different markets and tracks price history over time.

---

## Technology Stack

- **Frontend:** Android (Kotlin, Material Design 3)
- **Backend:** Flask (Python 3.13+)
- **Database:** Supabase PostgreSQL (Cloud)
- **Web Scraping:** Playwright (Chromium automation)

---

## Project Structure

```
AppPrecos/
├── android/                    # Android mobile app
│   └── app/src/main/          # Kotlin source code
│
└── backend/                    # Flask REST API
    ├── app.py                  # Main API server
    ├── nfce_extractor.py       # NFCe web scraper
    ├── supabase_config.py      # Database configuration
    ├── supabase_migrations.py  # Database setup SQL
    ├── requirements.txt        # Python dependencies
    └── .env                    # Environment variables
```

---

## How It Works

### 1. User Scans QR Code
- User scans QR code on NFCe receipt with Android app
- App extracts NFCe URL from QR code

### 2. Send to Backend
- App sends URL to backend API: `POST /api/nfce/extract`
- Request includes: `{"url": "...", "save": true}`

### 3. Duplicate Check (Instant)
- Backend checks if URL already processed
- If yes → Return 409 (already processed) in <100ms
- If no → Continue to extraction

### 4. Extract NFCe Data (15-20 seconds)
- Launch headless browser (Playwright + Chromium)
- Navigate to government NFCe website
- Click "Visualizar em Abas" button to expand details
- Extract from HTML:
  - **Market:** Name, address, CEP
  - **Products:** NCM code, quantity, unit, price
- Returns all extracted data

### 5. Market Matching
- Check if market exists (by exact name + address match)
- If exists → Use existing market ID
- If new → Create market with random ID (e.g., MKTABC12345)

### 6. Save to Database
- **Purchases table:** Save all 82 products (complete history)
- **Unique_products table:** Save/update latest price per NCM
- **Processed_urls table:** Mark URL as processed

### 7. Return Results
- Send success response to Android app with:
  - Market information
  - All products extracted
  - Statistics (how many saved/updated)

---

## Database Schema

### 4 Tables in Supabase PostgreSQL:

#### **1. markets**
Stores market metadata
- `id` - Auto-increment primary key
- `market_id` - Random unique ID (MKTABC12345)
- `name` - Market name
- `address` - Full address
- `created_at` - Timestamp

**Unique Constraint:** `(name, address)` - Same market = same ID

---

#### **2. purchases** (Complete Purchase History)
Stores every product from every receipt - unlimited entries
- `id` - Auto-increment
- `market_id` - Foreign key to markets
- `ncm` - 8-digit product code
- `quantity` - Amount purchased
- `unidade_comercial` - Unit (KG, UN, L, etc.)
- `price` - Product price
- `nfce_url` - Receipt URL
- `purchase_date` - When purchased
- `created_at` - Record timestamp

**No constraints:** Allows unlimited history tracking

---

#### **3. unique_products** (Latest Prices Only)
Stores the most recent price for each product per market
- `id` - Auto-increment
- `market_id` - Foreign key to markets
- `ncm` - Product code
- `unidade_comercial` - Unit
- `price` - Latest price
- `nfce_url` - Latest receipt URL
- `last_updated` - Auto-updated timestamp

**Unique Constraint:** `(market_id, ncm)` - One price per product per market

---

#### **4. processed_urls** (Duplicate Prevention)
Tracks processed NFCe URLs to prevent re-processing
- `id` - Auto-increment
- `nfce_url` - Receipt URL
- `market_id` - Associated market
- `products_count` - Number of products
- `processed_at` - Processing timestamp

**Unique Constraint:** `(nfce_url)` - Each URL processed only once

---

## Setup Instructions

### Backend Setup

1. **Install Python Dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Install Playwright Browser:**
```bash
playwright install chromium
```

3. **Configure Environment Variables:**

Edit `backend/.env` and add your Supabase credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key
DATABASE_URL=postgresql://postgres:your_password@host:5432/postgres
SECRET_KEY=your-secret-key
```

4. **Create Database Tables:**

Go to Supabase Dashboard → SQL Editor and run:
```bash
python backend/supabase_migrations.py
```
This will display the SQL commands to create all tables.

5. **Start Backend:**
```bash
cd backend
python app.py
```

Server runs at: `http://localhost:5000`

---

## API Endpoints

### **GET /**
API information and available endpoints

### **GET /api/markets**
List all markets in database

### **GET /api/markets/{market_id}**
Get specific market details

### **GET /api/markets/{market_id}/products**
Get all unique products for a market (latest prices)

### **POST /api/nfce/extract**
Extract and save NFCe data

**Request:**
```json
{
  "url": "https://www.nfce.fazenda.sp.gov.br/...",
  "save": true
}
```

**Response (201 Created):**
```json
{
  "message": "NFCe data extracted and saved successfully",
  "market": {
    "market_id": "MKTABC12345",
    "name": "Supermercado Example",
    "address": "Rua Example, 123",
    "action": "created"
  },
  "products": [82 items],
  "statistics": {
    "products_saved_to_purchases": 82,
    "unique_products_created": 79,
    "unique_products_updated": 0
  }
}
```

**Response (409 Conflict):**
```json
{
  "error": "This NFCe has already been processed",
  "market_id": "MKTABC12345",
  "products_count": 82,
  "processed_at": "2025-10-22T12:00:00"
}
```

### **GET /api/stats**
Get database statistics

**Response:**
```json
{
  "total_markets": 2,
  "total_purchases": 181,
  "total_unique_products": 79,
  "architecture": "Supabase PostgreSQL - 3-Table Design"
}
```

---

## Key Features

### ✅ Automatic Market Detection
- Extracts market name and address from NFCe
- Automatically matches existing markets
- Creates new market if not found
- Prevents duplicate markets

### ✅ Complete Price History
- Every purchase saved to `purchases` table
- Track price changes over time
- Unlimited entries per product

### ✅ Latest Price Tracking
- `unique_products` table maintains current prices
- One price per product per market
- Auto-updates on new purchases

### ✅ Duplicate Prevention
- NFCe URLs tracked in `processed_urls` table
- Instant duplicate detection (<100ms)
- Prevents duplicate data
- No wasted processing time

### ✅ Transaction Safety
- URL recorded before extraction
- Rollback on any failure
- Partial data cleaned up
- Safe retry on errors

---

## Architecture Highlights

### Efficient Processing
- **Duplicate Check:** <100ms (instant response)
- **NFCe Extraction:** 15-20 seconds (browser automation)
- **Data Save:** <1 second (82 products)
- **Total:** ~16-21 seconds for new receipts

### Smart Market Matching
Markets matched by exact `name + address`:
- Same market, different spelling → Different market
- Same chain, different location → Different market
- Exact match → Same market ID

### Data Flow
```
QR Code Scan
    ↓
Check processed_urls (instant)
    ↓
Extract NFCe (15-20s)
    ↓
Match/Create Market
    ↓
Save to purchases (history)
    ↓
Save to unique_products (latest)
    ↓
Return Success
```

---

## NCM Codes

**NCM** (Nomenclatura Comum do Mercosul) is an 8-digit product classification code used throughout South America.

**Examples:**
- `07099300` - Abóbora (pumpkin)
- `09012100` - Café (coffee)
- `04012010` - Leite (milk)

Used for accurate price comparison across markets.

---

## Error Handling

### **400 Bad Request**
- Missing URL parameter
- No products extracted from NFCe
- Missing market information

### **409 Conflict**
- URL already processed (duplicate)
- Returns previous processing details

### **500 Internal Server Error**
- Extraction failed
- Database save failed
- All errors trigger rollback

---

## Production Deployment

### Requirements
- Python 3.13+
- Supabase account (free tier works)
- Playwright Chromium browser

### Recommended Hosting
- **Backend:** Heroku, Railway, AWS, Google Cloud
- **Database:** Supabase (already configured)
- **Android:** Google Play Store

### Environment Variables
Set these in production:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `DATABASE_URL`
- `SECRET_KEY` (change from dev key)
- `FLASK_ENV=production`
- `DEBUG=False`

---

## Development

### Run Backend
```bash
cd backend
python app.py
```

### Test NFCe Extraction
Use any valid NFCe URL from a receipt QR code.

### View Database
Go to Supabase Dashboard → Table Editor to see all data.

---

## Troubleshooting

**Backend won't start:**
- Check `.env` file exists in `backend/` folder
- Verify all Supabase credentials are set
- Ensure Python 3.13+ is installed

**No products extracted:**
- Verify Playwright is installed: `playwright install chromium`
- Check NFCe URL is valid
- Try with `headless=False` for debugging

**Duplicate check not working:**
- Verify `processed_urls` table exists in Supabase
- Check backend logs for errors

**Tables don't exist:**
- Run SQL from `supabase_migrations.py` in Supabase SQL Editor
- Verify tables created in Supabase Table Editor

---

**Built with clean code, efficient processes, and well-organized functions.** ✨
