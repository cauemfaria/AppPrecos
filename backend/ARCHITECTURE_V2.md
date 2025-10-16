# Multi-Database Architecture V2

## Overview

AppPrecos uses a **multi-database architecture** where each market gets its own isolated database.

## Design

### Main Database: `markets_main.db`

Stores market metadata only:

```sql
CREATE TABLE markets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,      -- Sequential ID (1, 2, 3...)
    market_id VARCHAR(20) UNIQUE NOT NULL,     -- Random ID (MKT********)
    name VARCHAR(200) NOT NULL,                 -- Store name
    address VARCHAR(500) NOT NULL,              -- Full address with CEP
    created_at DATETIME NOT NULL,
    UNIQUE(name, address)                       -- Prevents duplicates
);
```

**Example Data:**
```
id | market_id    | name                      | address
1  | MKTOHMTI00S  | Supermercado Shibata Ltda | Av Getulio vargas, 1430, CEP: 12305-010
2  | MKTJOGAXOH2  | Supermercado XYZ Ltda     | Rua Teste, 123, CEP: 12345-678
```

---

### Market Databases: `market_databases/{MARKET_ID}.db`

Each market gets its own database file:

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ncm VARCHAR(8) NOT NULL,
    quantity FLOAT NOT NULL,
    unidade_comercial VARCHAR(10) NOT NULL,
    price FLOAT NOT NULL,
    nfce_url VARCHAR(1000),
    purchase_date DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Example:**
- `MKTOHMTI00S.db` contains all products for Supermercado Shibata
- `MKTJOGAXOH2.db` contains all products for Supermercado XYZ

---

## Workflow

### 1. QR Code Scanned
```
User scans NFCe QR code → Gets URL
```

### 2. Extract Data
```
POST /api/nfce/extract
{ "url": "https://...", "save": true }

Backend extracts:
- Market name: "Supermercado Shibata Ltda"
- Market address: "Av Getulio vargas, 1430, CEP: 12305-010"
- 17 products with NCM, qty, unit, price
```

### 3. Market Matching/Creation
```
Query: SELECT * FROM markets 
       WHERE name=? AND address=?

IF FOUND:
  - Use existing market_id
  - Use existing database file
  - Action: "matched"

IF NOT FOUND:
  - Generate random market_id (e.g., "MKTOHMTI00S")
  - INSERT INTO markets_main.db
  - CREATE market_databases/MKTOHMTI00S.db
  - CREATE TABLE products in new database
  - Action: "created"
```

### 4. Save Products
```
For each of 17 products:
  INSERT INTO market_databases/MKTOHMTI00S.db
  VALUES (ncm, quantity, unit, price, url, date)
```

### 5. Response
```json
{
  "market": {
    "market_id": "MKTOHMTI00S",
    "name": "Supermercado Shibata Ltda",
    "action": "created",
    "database_file": "MKTOHMTI00S.db"
  },
  "statistics": {
    "products_saved": 17
  }
}
```

---

## Benefits

### Data Isolation
- Each market's data is completely separate
- No cross-contamination
- Easy to delete a market (just delete its .db file)

### Scalability
- Distributed storage (one file per market)
- No single large database
- Better for backups (can backup per market)

### Performance
- Smaller databases = faster queries
- No need to filter by market_id in queries
- Reduced index overhead

### Security
- Data separation by design
- Easy to implement per-market access controls
- Can encrypt individual market databases

---

## File Structure

```
backend/
├── markets_main.db              # Metadata only
│
└── market_databases/            # Market-specific data
    ├── MKTOHMTI00S.db          # Market 1 products
    ├── MKTJOGAXOH2.db          # Market 2 products
    ├── MKT3X9K2L5P.db          # Market 3 products
    └── ...                     # One per market
```

---

## Market ID Format

```
Format: MKT + 8 random characters
Characters: A-Z, 0-9
Examples: MKTOHMTI00S, MKTJOGAXOH2, MKT3X9K2L5P

Uniqueness: Checked before creation
Collision handling: Regenerate if duplicate found
```

---

## API Changes

### Old API (V1):
```
POST /api/nfce/extract
{
  "url": "...",
  "market_id": 1,    ← User had to select
  "save": true
}
```

### New API (V2):
```
POST /api/nfce/extract
{
  "url": "...",      ← Just the URL!
  "save": true
}

Backend auto-matches/creates market
```

---

## Migration from V1

If migrating from single-database architecture:

1. Export data from old database
2. Group products by market_id
3. For each market:
   - Generate random market_id
   - Create market database
   - Import products
4. Update application to use V2

---

## Advantages Over Single Database

| Aspect | Single DB | Multi-DB |
|--------|-----------|----------|
| **Isolation** | ❌ All mixed | ✅ Separated |
| **Scalability** | ⚠️ One large file | ✅ Distributed |
| **Backup** | ❌ All or nothing | ✅ Per market |
| **Performance** | ⚠️ Large indices | ✅ Small DBs |
| **Deletion** | ⚠️ CASCADE needed | ✅ Delete file |
| **Security** | ❌ One access point | ✅ Per-market access |

---

**Status:** ✅ Implemented and tested
**Version:** 2.0
**Architecture:** Multi-database (one DB per market)

