# QR CODE SCAN DATA FLOW ANALYSIS

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER SCANS QR CODE (Android App)                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. QrCodeAnalyzer.kt extracts NFCe URL                         │
│    - CameraX analyzes frame                                     │
│    - BarcodeScanning API extracts URL                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. ScannerViewModel.processNFCe(url)                           │
│    - Changes state to Processing                                │
│    - Calls repository.extractNFCe(url)                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. AppRepository.extractNFCe()                                  │
│    - Creates NFCeRequest{url: "...", save: true}               │
│    - POST to https://appprecos.onrender.com/api/nfce/extract   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. BACKEND: /api/nfce/extract endpoint (SYNC mode)             │
│    app.py lines 352-469                                         │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
┌──────────────────┐                  ┌──────────────────┐
│ 5a. Check if URL │                  │ 5b. Record URL   │
│ already exists   │                  │ in processed_urls│
│ (line 357-369)   │                  │ (line 371-380)   │
└──────────────────┘                  └──────────────────┘
                                                │
                                                ▼
                        ┌──────────────────────────────────────┐
                        │ 5c. extract_full_nfce_data()         │
                        │ (nfce_extractor.py)                  │
                        │ - Launch Playwright browser          │
                        │ - Click "Visualizar em Abas"         │
                        │ - Extract market info + products     │
                        └──────────────────────────────────────┘
                                                │
                                                ▼
                        ┌──────────────────────────────────────┐
                        │ 5d. Check/Create Market              │
                        │ (lines 404-424)                      │
                        │ - Query markets table                │
                        │ - Create if not exists               │
                        └──────────────────────────────────────┘
                                                │
                                                ▼
                        ┌──────────────────────────────────────┐
                        │ 5e. save_products_to_supabase()      │
                        │ *** CRITICAL SECTION - BUG HERE ***  │
                        └──────────────────────────────────────┘
                                                │
                ┌───────────────────────────────┴────────────────────────┐
                ▼                                                        ▼
┌────────────────────────────────┐              ┌─────────────────────────────────┐
│ 6a. INSERT to purchases table  │              │ 6b. UPSERT to unique_products   │
│ (lines 137-151)                │              │ (lines 155-180)                 │
│                                │              │                                 │
│ ⚠️ BUG: Silent failures!       │              │ ✅ Working correctly            │
│ ⚠️ No error checking           │              │ ✅ Has error handling           │
│ ⚠️ No transaction safety       │              │                                 │
└────────────────────────────────┘              └─────────────────────────────────┘
                │                                                        │
                └────────────────────────────────────────────────────────┘
                                                │
                                                ▼
                        ┌──────────────────────────────────────┐
                        │ 7. Update processed_urls status      │
                        │ (lines 430-436)                      │
                        │ - Set status='success'               │
                        │ - Set products_count                 │
                        └──────────────────────────────────────┘
                                                │
                                                ▼
                        ┌──────────────────────────────────────┐
                        │ 8. Return response to Android        │
                        │ (lines 439-455)                      │
                        └──────────────────────────────────────┘
                                                │
                                                ▼
                        ┌──────────────────────────────────────┐
                        │ 9. Android shows success UI          │
                        │ ScannerFragment displays results     │
                        └──────────────────────────────────────┘
```

## Database Tables and Their Roles

### 1. **markets** Table
- **Purpose**: Store unique market information
- **Key**: market_id (MKT + 8 random chars)
- **Uniqueness**: (name, address) combination
- **Data Source**: Extracted from NFCe "Nome / Razão Social" + "Endereço"

### 2. **purchases** Table ⚠️ BUG HERE
- **Purpose**: Complete purchase history (unlimited entries, never updated)
- **Data Stored**: 
  - market_id, ncm, ean, product_name
  - quantity (amount bought)
  - total_price (total paid for quantity)
  - unit_price (price per KG or per UN)
  - purchase_date, nfce_url
- **Problem**: Inserts are FAILING SILENTLY

### 3. **unique_products** Table ✅ WORKING
- **Purpose**: Latest price per product per market (one entry per NCM per market)
- **Data Stored**:
  - market_id, ncm, ean, product_name
  - price (unit price - same as unit_price in purchases)
  - last_updated, nfce_url
- **Uniqueness**: (market_id, ncm) combination

### 4. **processed_urls** Table
- **Purpose**: Prevent duplicate processing of same NFCe
- **Status Values**: 'processing', 'success', 'error'

## IDENTIFIED BUGS

### 🔴 BUG #1: Silent Failures in Purchases Insert
**Location**: `app.py` lines 137-151

**Problem**: 
The code does NOT check if the Supabase insert actually succeeded:
```python
supabase.table('purchases').insert(purchase_data).execute()
saved_to_purchases += 1  # Increments even if insert failed!
```

**Why it fails silently**:
- Supabase Python client returns a response object, not an exception
- Need to check `response.data` or handle errors explicitly
- If the insert fails, no exception is raised

### 🔴 BUG #2: No Transaction Safety
**Location**: `app.py` lines 122-191

**Problem**:
- If purchases insert fails, unique_products still proceeds
- No rollback mechanism
- Database ends up in inconsistent state

### 🔴 BUG #3: Separate Loops = Partial Failures
**Location**: `app.py` lines 137-151 vs 155-180

**Problem**:
- Two separate loops for purchases and unique_products
- If first loop fails halfway, second loop still runs
- No atomic transaction

### 🔴 BUG #4: Poor Error Reporting
**Location**: `app.py` lines 188-190

**Problem**:
```python
except Exception as e:
    print(f"Error saving products to Supabase: {e}")
    raise
```
- Generic exception handling
- No detail about which table failed
- No information about which product failed

## EVIDENCE OF THE BUG

**User Report**: 
- ✅ Data went to unique_products correctly
- ❌ Data did NOT go to purchases
- ✅ App returned success response

**This proves**:
1. The purchases loop executed (no exception raised)
2. The inserts didn't fail with exceptions (otherwise unique_products wouldn't run)
3. The inserts are failing silently (Supabase returns error, not exception)

## ROOT CAUSE ANALYSIS

### Most Likely Cause: Schema Mismatch
The migration file `add_product_name_migration.sql` shows that `product_name` column was ADDED later. If the production database wasn't migrated properly:

1. Code tries to insert `product_name` into purchases table
2. Column doesn't exist in production database
3. Supabase returns error (but doesn't raise exception)
4. Code continues to unique_products (which might have been migrated)
5. unique_products succeeds, purchases fails

### Other Possible Causes:
1. **Permission Issues**: Service role might not have INSERT on purchases
2. **Constraint Violations**: Foreign key or check constraint failing
3. **Data Type Mismatches**: Python float vs PostgreSQL numeric issues

## REQUIRED FIXES

### Fix #1: Add Explicit Error Checking
```python
response = supabase.table('purchases').insert(purchase_data).execute()
if not response.data:
    raise Exception(f"Failed to insert purchase: {response}")
```

### Fix #2: Add Transaction Safety
- Use database transactions
- Rollback on any failure
- Ensure atomicity

### Fix #3: Better Error Logging
- Log each product being processed
- Log the exact error from Supabase
- Include product NCM in error messages

### Fix #4: Schema Validation
- Verify schema before inserting
- Add migration version checking
- Validate column existence

## TESTING PLAN

1. **Reproduce the bug**: Test with actual QR code on production
2. **Verify schema**: Check if product_name exists in purchases table
3. **Add logging**: Deploy with detailed logging
4. **Test fix**: Verify both tables get populated
5. **Verify consistency**: Ensure purchases and unique_products match

