# Database Columns Quick Reference

## 🗃️ ALL DATABASE COLUMNS

### TABLE 1: MARKETS (Store Information)

| # | Column | Type | Required | Auto-Filled | Available in NFCe? | Currently Working? |
|---|--------|------|----------|-------------|-------------------|-------------------|
| 1 | **id** | INTEGER | YES | ✅ Auto | N/A | ✅ YES |
| 2 | **name** | VARCHAR(200) | YES | ❌ Manual | ✅ YES | ⚠️ NOT EXTRACTED |
| 3 | **address** | VARCHAR(500) | YES | ❌ Manual | ✅ YES | ⚠️ NOT EXTRACTED |
| 4 | **created_at** | DATETIME | YES | ✅ Auto | N/A | ✅ YES |

**Example NFCe Data:**
```
Name:    "Supermercado Shibata Ltda"
Address: "Av Getulio vargas , 1430 , , Jd.Primavera , Jacarei , SP"
CNPJ:    "48.093.892/0010-30"  (available but not in schema)
```

---

### TABLE 2: PURCHASES (Complete Purchase History)

| # | Column | Type | Required | Auto-Filled | Available in NFCe? | Currently Working? |
|---|--------|------|----------|-------------|-------------------|-------------------|
| 1 | **id** | INTEGER | YES | ✅ Auto | N/A | ✅ YES |
| 2 | **market_id** | INTEGER | YES | ❌ User selects | N/A | ⚠️ MANUAL |
| 3 | **ncm** | VARCHAR(8) | YES | ✅ Extracted | ✅ YES | ✅ YES |
| 4 | **quantity** | FLOAT | YES | ✅ Extracted | ✅ YES | ✅ YES |
| 5 | **unidade_comercial** | VARCHAR(10) | YES | ✅ Extracted | ✅ YES | ✅ YES |
| 6 | **price** | FLOAT | YES | ✅ Extracted | ✅ YES | ✅ YES |
| 7 | **nfce_url** | VARCHAR(1000) | NO | ✅ From QR | ✅ YES | ✅ YES |
| 8 | **purchase_date** | DATETIME | YES | ⚠️ Wrong! | ✅ YES | ❌ USES CURRENT TIME |
| 9 | **created_at** | DATETIME | YES | ✅ Auto | N/A | ✅ YES |

**Example NFCe Data per Product:**
```
NCM:              "07099300"        ✅ Extracted & saved
Quantity:         "0,4310"          ✅ Extracted & saved (converted to 0.431)
Unit:             "KG"              ✅ Extracted & saved
Price:            "2,15"            ✅ Extracted & saved (converted to 2.15)
Product Name:     "ABOBORA..."      ✅ Extracted but NOT saved
Purchase Date:    "20/09/2025..."   ❌ NOT extracted (uses current time)
```

---

### TABLE 3: UNIQUE_PRODUCTS (Latest Prices Only)

| # | Column | Type | Required | Auto-Filled | Available in NFCe? | Currently Working? |
|---|--------|------|----------|-------------|-------------------|-------------------|
| 1 | **id** | INTEGER | YES | ✅ Auto | N/A | ✅ YES |
| 2 | **market_id** | INTEGER | YES | ✅ From purchase | N/A | ✅ YES |
| 3 | **ncm** | VARCHAR(8) | YES | ✅ From purchase | ✅ YES | ✅ YES |
| 4 | **unidade_comercial** | VARCHAR(10) | YES | ✅ From purchase | ✅ YES | ✅ YES |
| 5 | **price** | FLOAT | YES | ✅ From purchase | ✅ YES | ✅ YES |
| 6 | **nfce_url** | VARCHAR(1000) | NO | ✅ From purchase | ✅ YES | ✅ YES |
| 7 | **last_updated** | DATETIME | YES | ✅ Auto-update | N/A | ✅ YES |

**Auto-Update Logic:**
```
When purchase added:
  IF NCM exists for market:
    UPDATE price, unit, url, last_updated
  ELSE:
    INSERT new row
```

---

## ✅ FULLY WORKING (5/9 product fields)

These are **automatically extracted and saved** from NFCe URL:

1. ✅ **ncm** → Extracted from: `<label>Código NCM</label><span>07099300</span>`
2. ✅ **quantity** → Extracted from: `class="fixo-prod-serv-qtd"><span>0,4310</span>`
3. ✅ **unidade_comercial** → Extracted from: `class="fixo-prod-serv-uc"><span>KG</span>`
4. ✅ **price** → Extracted from: `class="fixo-prod-serv-vb"><span>2,15</span>`
5. ✅ **nfce_url** → Provided by QR code scan

---

## ⚠️ NEEDS FIXING (4/9 fields)

### 1. **purchase_date** (HIGH PRIORITY)

**Current:** Uses `datetime.utcnow()` - WRONG!  
**Should be:** Actual receipt date

**Available in NFCe:**
```html
<strong>Emissão:</strong> 20/09/2025 19:44:53
```

**Fix:**
```python
# In nfce_extractor.py
date_pattern = r'Emissão:</strong>\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})'
date_match = re.search(date_pattern, html)
if date_match:
    purchase_date = datetime.strptime(date_match.group(1), '%d/%m/%Y %H:%M:%S')
```

---

### 2. **market name** (MEDIUM PRIORITY)

**Current:** Must be entered manually  
**Should be:** Auto-extracted from NFCe

**Available in NFCe:**
```html
Nome / Razão Social
<span>Supermercado Shibata Ltda</span>
```

**Fix:**
```python
name_pattern = r'Nome / Razão Social[^<]*<[^>]*>([^<]+)'
name_match = re.search(name_pattern, html)
market_name = name_match.group(1).strip()
```

---

### 3. **market address** (MEDIUM PRIORITY)

**Current:** Must be entered manually  
**Should be:** Auto-extracted from NFCe

**Available in NFCe:**
```html
Av Getulio vargas , 1430 , , Jd.Primavera , Jacarei , SP
```

**Fix:**
```python
# Address usually appears after CNPJ
address_pattern = r'CNPJ[^<]+</span>.*?<div>([^<]+(?:Jacarei|SP)[^<]*)</div>'
```

---

### 4. **product_name** (LOW PRIORITY - Schema Change Required)

**Current:** Extracted but NOT saved  
**Should be:** Add column to schema and save

**Available in NFCe:**
```html
<span>ABOBORA PESCOCO KG</span>
```

**Already extracted!** Just needs schema update:
```python
# Add to Purchase and UniqueProduct models:
product_name = db.Column(db.String(200), nullable=True, index=True)
```

---

## 🎯 SUMMARY BY TABLE

### MARKETS Table (2/3 fields need work)

| Column | Status | Action Needed |
|--------|--------|---------------|
| id | ✅ Working | None |
| name | ⚠️ Manual | Extract from NFCe |
| address | ⚠️ Manual | Extract from NFCe |
| created_at | ✅ Working | None |

---

### PURCHASES Table (5/9 fields working)

| Column | Status | Action Needed |
|--------|--------|---------------|
| id | ✅ Working | None |
| market_id | ⚠️ Manual | Auto-match by CNPJ |
| ncm | ✅ Working | None |
| quantity | ✅ Working | None |
| unidade_comercial | ✅ Working | None |
| price | ✅ Working | None |
| nfce_url | ✅ Working | None |
| purchase_date | ❌ Wrong date | Extract from "Emissão" |
| created_at | ✅ Working | None |

---

### UNIQUE_PRODUCTS Table (6/7 fields working)

| Column | Status | Action Needed |
|--------|--------|---------------|
| id | ✅ Working | None |
| market_id | ⚠️ From manual | Auto-match by CNPJ |
| ncm | ✅ Working | None |
| unidade_comercial | ✅ Working | None |
| price | ✅ Working | None |
| nfce_url | ✅ Working | None |
| last_updated | ✅ Working | None |

---

## 📝 BOTTOM LINE

### Currently From NFCe URL:
- ✅ **5 fields automatically populated** (NCM, qty, unit, price, URL)
- ⚠️ **4 fields need fixes** (store name, address, purchase date, market matching)
- ❌ **1 field not in schema** (product names - recommended to add)

### All Data IS Available:
- ✅ **Everything** can be extracted from NFCe URL
- ✅ **Zero manual input** possible with recommended fixes
- ✅ **100% automation** achievable

### Current Automation Level:
**56%** - More than half working, rest needs extraction logic added

---

**See `docs/DATABASE_POPULATION.md` for detailed implementation guide!**

