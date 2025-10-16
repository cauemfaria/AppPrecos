# Database Population Guide

Complete guide on how to populate all database columns from NFCe URL data.

---

## 📋 TABLE 1: MARKETS

### Columns & Population Logic

| Column | Type | Nullable | Auto-Populated | Source | Current Logic |
|--------|------|----------|----------------|--------|---------------|
| **id** | INTEGER | NO | ✅ AUTO INCREMENT | Database | ✅ Automatic |
| **name** | VARCHAR(200) | NO | ❌ MANUAL | NFCe HTML | ⚠️ **NEEDS EXTRACTION** |
| **address** | VARCHAR(500) | NO | ❌ MANUAL | NFCe HTML | ⚠️ **NEEDS EXTRACTION** |
| **created_at** | DATETIME | NO | ✅ AUTO | Database | ✅ Automatic (datetime.utcnow) |

### 🔍 Available from NFCe URL:

From your sample NFCe page, I can extract:

```html
<!-- Store name -->
<div>Supermercado Shibata Ltda</div>

<!-- CNPJ -->
CNPJ: 48.093.892/0010-30

<!-- Address -->
Av Getulio vargas , 1430 , , Jd.Primavera , Jacarei , SP
```

### ✅ What We CAN Extract:
- ✅ **name** - Store name (e.g., "Supermercado Shibata Ltda")
- ✅ **address** - Full address
- ✅ **cnpj** - Store CNPJ (NOT in current schema)

### ⚠️ Current Status:
**NOT IMPLEMENTED** - Currently you must create markets manually via API

### 💡 Recommendation:
**ADD to `extract_full_nfce_data()` function:**
- Extract store name from HTML
- Extract store address from HTML
- Optionally extract CNPJ (could add to schema)

---

## 📋 TABLE 2: PURCHASES

### Columns & Population Logic

| Column | Type | Nullable | Auto-Populated | Source | Current Logic |
|--------|------|----------|----------------|--------|---------------|
| **id** | INTEGER | NO | ✅ AUTO INCREMENT | Database | ✅ Automatic |
| **market_id** | INTEGER | NO | ❌ MANUAL | User input | ⚠️ **User must select market** |
| **ncm** | VARCHAR(8) | NO | ✅ EXTRACTED | NFCe HTML | ✅ **Working!** |
| **quantity** | FLOAT | NO | ✅ EXTRACTED | NFCe HTML | ✅ **Working!** |
| **unidade_comercial** | VARCHAR(10) | NO | ✅ EXTRACTED | NFCe HTML | ✅ **Working!** |
| **price** | FLOAT | NO | ✅ EXTRACTED | NFCe HTML | ✅ **Working!** |
| **nfce_url** | VARCHAR(1000) | YES | ✅ PROVIDED | QR code scan | ✅ **Working!** |
| **purchase_date** | DATETIME | NO | ✅ EXTRACTED | NFCe HTML | ⚠️ **NEEDS EXTRACTION** |
| **created_at** | DATETIME | NO | ✅ AUTO | Database | ✅ Automatic (datetime.utcnow) |

### 🔍 Available from NFCe URL:

```html
<!-- From your sample NFCe: -->

<!-- Product 1 -->
<span>ABOBORA PESCOCO KG</span>          ← Product name (not in DB)
<span>07099300</span>                    ← NCM code ✅
<span>0,4310</span>                      ← Quantity ✅
<span>KG</span>                          ← Unidade comercial ✅
<span>2,15</span>                        ← Price ✅

<!-- Receipt date -->
Emissão: 20/09/2025 19:44:53             ← Purchase date ⚠️ NEEDS EXTRACTION
```

### ✅ What We CAN Extract (Currently Working):
- ✅ **ncm** - 8-digit NCM code
- ✅ **quantity** - Product quantity
- ✅ **unidade_comercial** - Unit (KG, UN, L, etc.)
- ✅ **price** - Product price
- ✅ **nfce_url** - URL from QR code

### ⚠️ What NEEDS to be Added:
- ⚠️ **purchase_date** - Currently uses `datetime.utcnow()` (wrong!)
  - Should extract from NFCe "Emissão" field
  - Format: `20/09/2025 19:44:53`

### ❌ What's NOT in Database (but available):
- Product name (we extract it but don't save it)
- Store CNPJ
- Receipt number
- Receipt series

---

## 📋 TABLE 3: UNIQUE_PRODUCTS

### Columns & Population Logic

| Column | Type | Nullable | Auto-Populated | Source | Current Logic |
|--------|------|----------|----------------|--------|---------------|
| **id** | INTEGER | NO | ✅ AUTO INCREMENT | Database | ✅ Automatic |
| **market_id** | INTEGER | NO | ❌ MANUAL | User input | ⚠️ **User must select market** |
| **ncm** | VARCHAR(8) | NO | ✅ EXTRACTED | NFCe HTML | ✅ **Working!** |
| **unidade_comercial** | VARCHAR(10) | NO | ✅ EXTRACTED | NFCe HTML | ✅ **Working!** |
| **price** | FLOAT | NO | ✅ EXTRACTED | NFCe HTML | ✅ **Working!** |
| **nfce_url** | VARCHAR(1000) | YES | ✅ PROVIDED | QR code scan | ✅ **Working!** |
| **last_updated** | DATETIME | NO | ✅ AUTO | Database | ✅ Automatic (auto-update) |

### ✅ Auto-Update Logic:

When a new purchase is added:
```python
1. Check if NCM exists for this market
2. If YES:
   - UPDATE unidade_comercial (if different)
   - UPDATE price (latest price)
   - UPDATE nfce_url (latest receipt)
   - UPDATE last_updated (automatic)
3. If NO:
   - INSERT new row
```

**Status:** ✅ **Fully implemented and working!**

---

## 🎯 COMPLETE DATA MAPPING

### What NFCe URL Provides:

From the sample URL you shared, the NFCe page contains:

```
STORE INFORMATION:
├── Store Name:     "Supermercado Shibata Ltda"      ✅ Can extract
├── CNPJ:          "48.093.892/0010-30"              ✅ Can extract
├── Address:       "Av Getulio vargas, 1430..."     ✅ Can extract
└── State:         "SP"                              ✅ Can extract

RECEIPT INFORMATION:
├── Receipt Number: "31010"                          ✅ Can extract
├── Series:        "308"                             ✅ Can extract
├── Issue Date:    "20/09/2025 19:44:53"            ✅ Can extract
└── Total Value:   "96,88"                          ✅ Can extract

PRODUCTS (17 items):
├── Product 1:
│   ├── Name:      "ABOBORA PESCOCO KG"             ✅ Extracted (not saved)
│   ├── NCM:       "07099300"                       ✅ Extracted & saved ✅
│   ├── Quantity:  "0,4310"                         ✅ Extracted & saved ✅
│   ├── Unit:      "KG"                             ✅ Extracted & saved ✅
│   └── Price:     "2,15"                           ✅ Extracted & saved ✅
│
├── Product 2...
└── Product 17...
```

---

## 📊 CURRENT EXTRACTION STATUS

### ✅ WORKING (Currently Extracted & Saved):

1. **NCM codes** - ✅ Extracted with regex, saved to DB
2. **Quantities** - ✅ Extracted, converted from BR format (0,431 → 0.431)
3. **Units** - ✅ Extracted (KG, UN, L, etc.)
4. **Prices** - ✅ Extracted, converted from BR format (2,15 → 2.15)
5. **NFCe URL** - ✅ Provided by user/app

### ⚠️ PARTIALLY WORKING (Extracted but NOT saved):

6. **Product names** - Extracted but **NOT in database**
7. **Store name** - Visible on page but **NOT extracted**
8. **Store address** - Visible on page but **NOT extracted**

### ❌ NOT WORKING (Needs Implementation):

9. **Purchase date** - Currently uses `datetime.utcnow()` (**WRONG!**)
   - Should extract "Emissão: 20/09/2025 19:44:53"
10. **Store CNPJ** - Not extracted, **NOT in schema**
11. **Receipt number** - Not extracted, **NOT in schema**

---

## 🔧 REQUIRED FIXES

### Priority 1: Extract Purchase Date from NFCe

**Current Problem:**
```python
purchase_date = db.Column(db.DateTime, default=datetime.utcnow)  # ❌ Wrong!
```
Uses current time instead of actual purchase time

**Solution:**
Extract from NFCe HTML:
```html
<strong>Emissão:</strong> 20/09/2025 19:44:53
```

**Implementation needed in `nfce_extractor.py`:**
```python
# Add to extract_full_nfce_data()
date_pattern = r'Emissão:</strong>\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})'
purchase_dates = re.findall(date_pattern, html)

# Convert to datetime
from datetime import datetime
purchase_date = datetime.strptime(purchase_dates[0], '%d/%m/%Y %H:%M:%S')
```

---

### Priority 2: Extract Store Information

**Current Problem:**
```python
# User must manually create market via API
POST /api/markets
{
  "name": "...",      # ❌ Manual entry
  "address": "..."   # ❌ Manual entry
}
```

**Solution:**
Extract from NFCe HTML:
```html
<div>Supermercado Shibata Ltda</div>
CNPJ: 48.093.892/0010-30
<div>Av Getulio vargas , 1430 , , Jd.Primavera , Jacarei , SP</div>
```

**Implementation needed in `nfce_extractor.py`:**
```python
# Add to extract_full_nfce_data()
name_pattern = r'class="[^"]*emitente[^"]*">\s*<[^>]*>([^<]+)</[^>]*>'
address_pattern = r'Av [^<]+'  # Need exact selector from HTML

market_info = {
    'name': extracted_name,
    'address': extracted_address,
    'cnpj': extracted_cnpj  # Optional
}
```

---

### Priority 3: Add Product Names to Database

**Current Problem:**
- Product names are extracted but **NOT saved**
- Only NCM codes stored
- Users can't search by product name

**Solution:**
Add `product_name` column to `purchases` and `unique_products` tables

**Schema Change Needed:**
```python
class Purchase(db.Model):
    # ... existing columns ...
    product_name = db.Column(db.String(200), nullable=True)  # NEW
    ncm = db.Column(db.String(8), nullable=False, index=True)
    # ...

class UniqueProduct(db.Model):
    # ... existing columns ...
    product_name = db.Column(db.String(200), nullable=True)  # NEW
    ncm = db.Column(db.String(8), nullable=False, index=True)
    # ...
```

---

## 🎯 COMPLETE POPULATION FLOW

### Current Flow (Partial Automation):

```
1. User scans QR code → Gets NFCe URL
2. User MANUALLY selects market (market_id)  ← Manual step!
3. App sends: { "url": "...", "market_id": 1, "save": true }
4. Backend extracts:
   ✅ NCM codes
   ✅ Quantities
   ✅ Units
   ✅ Prices
   ⚠️ Purchase date (uses current time - WRONG!)
5. Backend saves to database
```

### Recommended Flow (Full Automation):

```
1. User scans QR code → Gets NFCe URL
2. App sends: { "url": "...", "save": true }  ← No market_id needed!
3. Backend extracts:
   ✅ Store name + address
   ✅ Store CNPJ (optional)
   ✅ Product names
   ✅ NCM codes
   ✅ Quantities
   ✅ Units
   ✅ Prices
   ✅ Purchase date (from receipt)
4. Backend logic:
   a. Check if market exists (by CNPJ or name)
   b. If NO: Create new market automatically
   c. If YES: Use existing market_id
   d. Save all products
5. Return complete data to app
```

---

## 📝 DETAILED COLUMN ANALYSIS

### MARKETS Table

```sql
CREATE TABLE markets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(200) NOT NULL,
    address         VARCHAR(500) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Population:**
| Column | Source | Extraction Method | Status |
|--------|--------|-------------------|---------|
| id | Auto | Auto-increment | ✅ Done |
| name | NFCe HTML | Regex: Store name near CNPJ | ❌ TODO |
| address | NFCe HTML | Regex: Address line | ❌ TODO |
| created_at | Auto | Database default | ✅ Done |

**Example Extraction from NFCe:**
```python
# In nfce_extractor.py - ADD THIS:
def extract_market_info(html):
    """Extract market information from NFCe HTML"""
    market_info = {}
    
    # Extract store name (after CNPJ section)
    name_match = re.search(r'Nome / Razão Social[^<]*<[^>]*>([^<]+)', html)
    if name_match:
        market_info['name'] = name_match.group(1).strip()
    
    # Extract CNPJ
    cnpj_match = re.search(r'CNPJ[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', html)
    if cnpj_match:
        market_info['cnpj'] = cnpj_match.group(1)
    
    # Extract address
    address_match = re.search(r'(Av|Rua|R\.)[^<]+(?:Jacarei|SP)', html)
    if address_match:
        market_info['address'] = address_match.group(0).strip()
    
    return market_info
```

---

### PURCHASES Table

```sql
CREATE TABLE purchases (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id           INTEGER NOT NULL,
    ncm                 VARCHAR(8) NOT NULL,
    quantity            FLOAT NOT NULL,
    unidade_comercial   VARCHAR(10) NOT NULL,
    price               FLOAT NOT NULL,
    nfce_url            VARCHAR(1000),
    purchase_date       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (market_id) REFERENCES markets(id)
);
```

**Population:**
| Column | Source | Extraction Method | Status |
|--------|--------|-------------------|---------|
| id | Auto | Auto-increment | ✅ Done |
| market_id | User/Auto | Match by CNPJ or create new | ⚠️ Manual now |
| ncm | NFCe HTML | `Código NCM</label><span>(\d{8})` | ✅ Done |
| quantity | NFCe HTML | `fixo-prod-serv-qtd.*?(\d+,\d+)` | ✅ Done |
| unidade_comercial | NFCe HTML | `fixo-prod-serv-uc.*?>(KG\|UN\|L)` | ✅ Done |
| price | NFCe HTML | `fixo-prod-serv-vb.*?(\d+,\d+)` | ✅ Done |
| nfce_url | QR Code | Scanned URL | ✅ Done |
| purchase_date | NFCe HTML | `Emissão:\s*(\d{2}/\d{2}/\d{4}...)` | ❌ TODO |
| created_at | Auto | Database default | ✅ Done |

**Example: Extract Purchase Date**
```python
# ADD THIS to extract_full_nfce_data():

# Extract receipt issue date
date_pattern = r'Emissão:</strong>\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})'
date_match = re.search(date_pattern, html)

if date_match:
    date_str = date_match.group(1)  # "20/09/2025 19:44:53"
    purchase_date = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')
else:
    purchase_date = datetime.utcnow()  # Fallback

# Then in products dict:
products.append({
    # ... existing fields ...
    'purchase_date': purchase_date  # NEW
})
```

---

### UNIQUE_PRODUCTS Table

```sql
CREATE TABLE unique_products (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id           INTEGER NOT NULL,
    ncm                 VARCHAR(8) NOT NULL,
    unidade_comercial   VARCHAR(10) NOT NULL,
    price               FLOAT NOT NULL,
    nfce_url            VARCHAR(1000),
    last_updated        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (market_id) REFERENCES markets(id),
    UNIQUE (market_id, ncm)
);
```

**Population:**
| Column | Source | Logic | Status |
|--------|--------|-------|---------|
| id | Auto | Auto-increment | ✅ Done |
| market_id | Purchases | Same as purchase | ✅ Done |
| ncm | Purchases | Same as purchase | ✅ Done |
| unidade_comercial | Purchases | Latest from purchase | ✅ Done |
| price | Purchases | Latest from purchase | ✅ Done |
| nfce_url | Purchases | Latest from purchase | ✅ Done |
| last_updated | Auto | Auto-update on change | ✅ Done |

**Auto-Update Logic (WORKING):**
```python
# In app.py - already implemented!
unique_product = UniqueProduct.query.filter_by(
    market_id=market_id,
    ncm=ncm
).first()

if unique_product:
    # UPDATE existing
    unique_product.price = new_price
    unique_product.unidade_comercial = new_unit
    unique_product.nfce_url = new_url
    unique_product.last_updated = datetime.utcnow()  # Auto
else:
    # INSERT new
    unique_product = UniqueProduct(...)
```

---

## 🚨 MISSING DATA THAT SHOULD BE ADDED

### Recommended Schema Additions:

#### 1. Add to MARKETS table:
```python
cnpj = db.Column(db.String(18), unique=True, index=True)  # NEW
# Allows auto-matching markets by CNPJ
```

#### 2. Add to PURCHASES and UNIQUE_PRODUCTS tables:
```python
product_name = db.Column(db.String(200), nullable=True, index=True)  # NEW
# Enables search by product name
```

#### 3. Optional - Add RECEIPTS table:
```python
class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.Integer, db.ForeignKey('markets.id'))
    nfce_url = db.Column(db.String(1000), unique=True)
    receipt_number = db.Column(db.String(20))
    receipt_series = db.Column(db.String(10))
    total_value = db.Column(db.Float)
    issue_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 🎯 ACTION ITEMS

### To Fully Populate Database from NFCe URL:

#### ✅ Already Working:
1. NCM codes extraction
2. Quantities extraction  
3. Units extraction
4. Prices extraction
5. Unique product auto-update

#### ⚠️ Needs Implementation:

**1. Extract Store Information:**
```python
# Add to nfce_extractor.py
def extract_market_info(html):
    # Extract: name, address, cnpj
    return market_info
```

**2. Extract Purchase Date:**
```python
# Update extract_full_nfce_data()
# Extract "Emissão" date from HTML
# Convert to datetime object
# Include in returned product dict
```

**3. Auto-Create Markets:**
```python
# Update API endpoint /api/nfce/extract
# Extract market info
# Check if market exists (by CNPJ)
# If not: create automatically
# Use market_id for products
```

**4. Add Product Names to Schema:**
```python
# Add column to both tables
# Update extraction to include product name
# Save to database
```

---

## 📋 QUICK REFERENCE

### What's Currently Auto-Populated:

| Table | Auto Columns |
|-------|--------------|
| **markets** | id, created_at |
| **purchases** | id, created_at *(purchase_date uses wrong date!)* |
| **unique_products** | id, last_updated |

### What Requires User Input:

| Field | Why | Can Be Automated? |
|-------|-----|-------------------|
| market_id | Must select market | ✅ YES - extract CNPJ, auto-match |
| (None other) | - | - |

### What's Extracted from NFCe:

| Data | Saved to DB? | Table/Column |
|------|--------------|--------------|
| NCM codes | ✅ YES | purchases.ncm, unique_products.ncm |
| Quantities | ✅ YES | purchases.quantity |
| Units | ✅ YES | purchases.unidade_comercial |
| Prices | ✅ YES | purchases.price, unique_products.price |
| Product names | ❌ NO | (not in schema) |
| Store name | ❌ NO | (not extracted) |
| Store address | ❌ NO | (not extracted) |
| Purchase date | ⚠️ WRONG | purchases.purchase_date (uses current time) |

---

## ✅ SUMMARY

**CURRENTLY WORKING:** 60% of needed data  
**NEEDS FIXES:** Purchase date extraction  
**NEEDS ENHANCEMENTS:** Store info auto-extraction, product names  

**All data IS available in NFCe URL** - just needs extraction logic added!

