# NFCe Data → Database Mapping

Visual guide showing what data is available and how it maps to database tables.

---

## 🗺️ DATA FLOW VISUALIZATION

```
┌────────────────────────────────────────────────────────────┐
│  NFCe URL (QR Code Scan)                                   │
│  https://www.nfce.fazenda.sp.gov.br/...?p=xxxxx            │
└───────────────────────┬────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────┐
│  NFCe Government Website (After "Visualizar em Abas")      │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  STORE INFORMATION:                                         │
│  ├─ Name: "Supermercado Shibata Ltda"       ⚠️ Not saved   │
│  ├─ CNPJ: "48.093.892/0010-30"              ⚠️ Not saved   │
│  └─ Address: "Av Getulio vargas, 1430..."   ⚠️ Not saved   │
│                                                             │
│  RECEIPT INFO:                                              │
│  ├─ Date: "20/09/2025 19:44:53"             ⚠️ Not saved   │
│  ├─ Number: "31010"                         ⚠️ Not saved   │
│  └─ Total: "R$ 96,88"                       ⚠️ Not saved   │
│                                                             │
│  PRODUCTS (17 items):                                       │
│  Product 1:                                                 │
│  ├─ Name: "ABOBORA PESCOCO KG"              ⚠️ Not saved   │
│  ├─ NCM: "07099300"                         ✅ SAVED       │
│  ├─ Qty: "0,4310"                           ✅ SAVED       │
│  ├─ Unit: "KG"                              ✅ SAVED       │
│  └─ Price: "2,15"                           ✅ SAVED       │
│                                                             │
│  Product 2...                                               │
│  Product 3...                                               │
│  [15 more products]                                         │
│                                                             │
└────────────────────────────────────────────────────────────┘
                        │
                        ▼
         ┌──────────────┴───────────────┐
         │                              │
         ▼                              ▼
┌─────────────────┐           ┌──────────────────┐
│  WHAT'S SAVED   │           │  WHAT'S MISSING  │
├─────────────────┤           ├──────────────────┤
│ ✅ NCM codes    │           │ ⚠️ Store name    │
│ ✅ Quantities   │           │ ⚠️ Store address │
│ ✅ Units        │           │ ⚠️ Product names │
│ ✅ Prices       │           │ ⚠️ Purchase date │
│ ✅ NFCe URL     │           │ ⚠️ Store CNPJ    │
└─────────────────┘           └──────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│  DATABASE TABLES                                            │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  MARKETS                                                    │
│  ├─ id              ✅ Auto-generated                       │
│  ├─ name            ⚠️ MANUAL (should be auto)             │
│  ├─ address         ⚠️ MANUAL (should be auto)             │
│  └─ created_at      ✅ Auto-generated                       │
│                                                             │
│  PURCHASES                                                  │
│  ├─ id              ✅ Auto-generated                       │
│  ├─ market_id       ⚠️ MANUAL (should be auto-matched)     │
│  ├─ ncm             ✅ From NFCe                            │
│  ├─ quantity        ✅ From NFCe                            │
│  ├─ unidade_com.    ✅ From NFCe                            │
│  ├─ price           ✅ From NFCe                            │
│  ├─ nfce_url        ✅ From QR code                         │
│  ├─ purchase_date   ⚠️ WRONG (uses current time)           │
│  └─ created_at      ✅ Auto-generated                       │
│                                                             │
│  UNIQUE_PRODUCTS                                            │
│  ├─ id              ✅ Auto-generated                       │
│  ├─ market_id       ⚠️ From purchases (manual source)      │
│  ├─ ncm             ✅ From purchases (auto-updated)        │
│  ├─ unidade_com.    ✅ From purchases (auto-updated)        │
│  ├─ price           ✅ From purchases (auto-updated)        │
│  ├─ nfce_url        ✅ From purchases (auto-updated)        │
│  └─ last_updated    ✅ Auto-generated on update             │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 📊 EXTRACTION COVERAGE

### Current Coverage: 5/9 Fields (56%)

| Data Available in NFCe | Currently Extracted? | Currently Saved? |
|------------------------|----------------------|------------------|
| Store name | ❌ NO | ❌ NO |
| Store CNPJ | ❌ NO | ❌ NO |
| Store address | ❌ NO | ❌ NO |
| Receipt date | ❌ NO | ⚠️ Uses wrong date |
| Product names | ✅ YES | ❌ NO (not in schema) |
| NCM codes | ✅ YES | ✅ YES |
| Quantities | ✅ YES | ✅ YES |
| Units | ✅ YES | ✅ YES |
| Prices | ✅ YES | ✅ YES |

---

## 🔧 RECOMMENDED IMPROVEMENTS

### Improvement 1: Auto-Extract Market Info

**Add to `backend/nfce_extractor.py`:**

```python
def extract_market_info(html):
    """Extract market information from NFCe HTML"""
    
    market = {}
    
    # Store name
    name_match = re.search(
        r'Nome / Razão Social[^<]*<[^>]*>([^<]+)', 
        html
    )
    if name_match:
        market['name'] = name_match.group(1).strip()
    
    # CNPJ
    cnpj_match = re.search(
        r'CNPJ[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', 
        html
    )
    if cnpj_match:
        market['cnpj'] = cnpj_match.group(1)
    
    # Address
    address_match = re.search(
        r'((?:Av|Rua|R\.)[^<,]+(?:,\s*\d+)?[^<]*(?:Jacarei|SP)[^<]*)', 
        html
    )
    if address_match:
        market['address'] = address_match.group(1).strip()
    
    return market
```

**Then update `extract_full_nfce_data()` to also return market info:**
```python
return {
    'market_info': extract_market_info(html),
    'products': products,
    'purchase_date': purchase_date
}
```

---

### Improvement 2: Auto-Match or Create Market

**Update API endpoint `/api/nfce/extract`:**

```python
@app.route('/api/nfce/extract', methods=['POST'])
def extract_nfce():
    data = request.get_json()
    
    # Extract NFCe data
    result = extract_full_nfce_data(data['url'])
    market_info = result['market_info']
    products = result['products']
    
    # Auto-match market by CNPJ
    if market_info.get('cnpj'):
        market = Market.query.filter_by(cnpj=market_info['cnpj']).first()
        
        if not market:
            # Create new market automatically
            market = Market(
                name=market_info['name'],
                address=market_info['address'],
                cnpj=market_info['cnpj']
            )
            db.session.add(market)
            db.session.commit()
    
    # Now save products with auto-matched market_id
    for product in products:
        purchase = Purchase(
            market_id=market.id,  # Auto-matched!
            ncm=product['ncm'],
            quantity=product['quantity'],
            # ...
        )
```

---

### Improvement 3: Add Product Names

**Update schema in `app.py`:**

```python
class Purchase(db.Model):
    # ... existing columns ...
    product_name = db.Column(db.String(200), nullable=True, index=True)
    ncm = db.Column(db.String(8), nullable=False, index=True)
    # ...

class UniqueProduct(db.Model):
    # ... existing columns ...
    product_name = db.Column(db.String(200), nullable=True, index=True)
    ncm = db.Column(db.String(8), nullable=False, index=True)
    # ...
```

**Product names already extracted!** Just need to save them.

---

## ✅ PRIORITY FIXES (IN ORDER)

### 1. Fix Purchase Date (HIGH PRIORITY)
**Impact:** Historical data accuracy  
**Effort:** Low (15 minutes)  
**Code:** Add date extraction regex

### 2. Extract Market Info (MEDIUM PRIORITY)
**Impact:** Removes manual market creation  
**Effort:** Medium (30 minutes)  
**Code:** Add market info extraction function

### 3. Add Product Names (LOW PRIORITY)
**Impact:** Better user experience (search by name)  
**Effort:** Medium (schema change + migration)  
**Code:** Add column, update extraction, migrate DB

### 4. Add CNPJ to Markets (LOW PRIORITY)
**Impact:** Enables auto-matching markets  
**Effort:** Medium (schema change + migration)  
**Code:** Add column, update extraction, add unique constraint

---

## 🎯 IDEAL FINAL STATE

```python
# User scans QR code → Gets URL
# App sends:
{
  "url": "https://nfce.fazenda.sp.gov.br/...",
  "save": true
}

# Backend auto-extracts:
{
  "market": {
    "name": "Supermercado Shibata Ltda",     # Auto-extracted
    "address": "Av Getulio vargas, 1430...",  # Auto-extracted
    "cnpj": "48.093.892/0010-30"              # Auto-extracted
  },
  "receipt": {
    "date": "2025-09-20T19:44:53",           # Auto-extracted
    "number": "31010",
    "total": 96.88
  },
  "products": [
    {
      "product_name": "ABOBORA PESCOCO KG",   # Auto-extracted
      "ncm": "07099300",                      # Auto-extracted ✅
      "quantity": 0.431,                      # Auto-extracted ✅
      "unidade_comercial": "KG",              # Auto-extracted ✅
      "price": 2.15                           # Auto-extracted ✅
    },
    # ... 16 more
  ]
}

# Backend logic:
# 1. Check if market exists (by CNPJ)
# 2. If not: Create new market
# 3. Save all products
# 4. Update unique_products
# 5. Return everything to app

# Result: ZERO manual input required! 🎉
```

---

**Current Status:** 5/9 fields working ✅  
**Recommended:** Implement the 4 fixes above for 100% automation 🚀

