# EAN Code Integration Guide

## Overview
The products database has been updated to include EAN (European Article Number) codes, also known as GTIN (Global Trade Item Number). This code is scraped from the NFCe along with the NCM code and stored in both the `purchases` and `unique_products` tables.

## What Changed?

### 1. Data Extraction (`nfce_extractor.py`)
- **Added**: EAN code extraction from NFCe HTML
- **Field**: `Código EAN Comercial`
- **Values**: 
  - Numeric EAN code (e.g., `7898083580716`)
  - `SEM GTIN` when product doesn't have an EAN

### 2. Database Schema
Both tables now include an `ean` column:

#### `purchases` table
```sql
ALTER TABLE purchases 
ADD COLUMN ean VARCHAR(50);
```

#### `unique_products` table
```sql
ALTER TABLE unique_products 
ADD COLUMN ean VARCHAR(50);
```

### 3. API Updates (`app.py`)
- The `save_products_to_supabase()` function now saves the EAN code
- Both `purchases` and `unique_products` tables store the EAN
- Default value: `SEM GTIN` if not provided

## Migration Instructions

### For New Installations
Run the complete migration script:
```sql
-- Use backend/supabase_migrations.py
-- This creates all tables with EAN support included
```

### For Existing Databases
Run the migration script to add EAN support without losing data:

1. Go to [Supabase SQL Editor](https://app.supabase.com)
2. Select your project
3. Go to **SQL Editor** → **New Query**
4. Copy and paste the contents of `add_ean_migration.sql`
5. Click **Run**

The migration will:
- ✅ Add `ean` column to `purchases` table
- ✅ Add `ean` column to `unique_products` table
- ✅ Set `SEM GTIN` as default for existing records
- ✅ Verify the changes

## API Response Format

### Product Data Structure
```json
{
  "number": 1,
  "product": "ALFACE AMER BOLA 200G",
  "ncm": "07051900",
  "ean": "7898083580716",
  "quantity": 1.0,
  "unidade_comercial": "UN",
  "total_price": 4.99,
  "unit_price": 4.99,
  "price": 4.99
}
```

### Database Records

#### purchases table
```json
{
  "id": 1,
  "market_id": "MKTABC12345",
  "ncm": "07051900",
  "ean": "7898083580716",
  "quantity": 1.0,
  "unidade_comercial": "UN",
  "total_price": 4.99,
  "unit_price": 4.99,
  "nfce_url": "https://...",
  "purchase_date": "2025-11-21T10:30:00Z",
  "created_at": "2025-11-21T10:30:00Z"
}
```

#### unique_products table
```json
{
  "id": 1,
  "market_id": "MKTABC12345",
  "ncm": "07051900",
  "ean": "7898083580716",
  "unidade_comercial": "UN",
  "price": 4.99,
  "nfce_url": "https://...",
  "last_updated": "2025-11-21T10:30:00Z"
}
```

## EAN Code Examples

### Products WITH EAN
- Lettuce: `7898083580716`
- Ketchup Heinz: `7896102000122`
- Coentro: `7898083580167`
- Rúcula: `7898558680026`

### Products WITHOUT EAN (SEM GTIN)
- Abóbora Pescoço KG: `SEM GTIN`
- Pepino Japonês KG: `SEM GTIN`
- Pão Francês KG: `SEM GTIN`
- Maçã Pink Lady KG: `SEM GTIN`
- Maracujá Azedo KG: `SEM GTIN`
- Pimentão Verde KG: `SEM GTIN`
- Bacon Sadia KG: `SEM GTIN`
- Queijo Parmesão KG: `SEM GTIN`

## Testing

### Test Extraction
```python
from nfce_extractor import extract_full_nfce_data

url = "YOUR_NFCE_URL"
result = extract_full_nfce_data(url, headless=False)

for product in result['products']:
    print(f"{product['product']}: EAN = {product['ean']}")
```

### Expected Output
```
ABOBORA PESCOCO KG: EAN = SEM GTIN
PEPINO JAPONES KG: EAN = SEM GTIN
PAO FRANCES TRC KG: EAN = SEM GTIN
ALFACE AMER BOLA 200G: EAN = 7898083580716
KETCHUP HEINZ 1,033KG: EAN = 7896102000122
COENTRO MACO: EAN = 7898083580167
RUCULA HIDROP MACO: EAN = 7898558680026
```

## Benefits

1. **Better Product Identification**: EAN codes are globally unique and standardized
2. **Product Matching**: Easier to match products across different markets
3. **Integration**: Can be used with external product databases
4. **Barcode Scanning**: EAN codes can be scanned with barcode readers
5. **Price Comparison**: More accurate product comparison across stores

## Notes

- ⚠️ Fresh produce (sold by weight) typically don't have EAN codes
- ✅ Packaged products almost always have EAN codes
- 📦 The system handles both cases automatically
- 🔄 Existing data is backward compatible (will show "SEM GTIN")

## Support

If you encounter any issues:
1. Check that the migration ran successfully
2. Verify the NFCe URL is valid
3. Ensure the website structure hasn't changed
4. Check the backend logs for extraction errors

