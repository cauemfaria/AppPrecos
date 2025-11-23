# RSC Sistemas GTIN API - Test Guide

## Overview

The RSC Sistemas GTIN API provides product information and images based on EAN/GTIN codes. This API requires authentication with username/password.

## API Information

- **Base URL**: https://gtin.rscsistemas.com.br
- **Authentication**: Username + Password → Bearer Token
- **Token Validity**: 1 hour
- **Rate Limiting**: According to your plan

## Endpoints

### 1. Authentication (Get Bearer Token)

**Endpoint**: `POST /oauth/token`

**Headers**:
```
username: your_username
password: your_password
Content-Type: application/json
```

**Response** (200 OK):
```json
{
  "token": "eyJhbGciOiAiQUVTMjU2IiwgInR5cCI6ICJKV1QifQ==..."
}
```

**Token is valid for 1 hour**

### 2. Get Product Information

**Endpoint**: `GET /api/gtin/infor/:gtin`

**Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Response** (200 OK):
```json
{
  "ean": "7896102000122",
  "ean_tipo": "EAN-13",
  "cest": "1700101",
  "ncm": 21032090,
  "nome": "KETCHUP HEINZ SQUEEZE 1,033KG",
  "nome_acento": "KETCHUP HEINZ SQUEEZE 1,033KG",
  "unid_abr": "UN",
  "unid_desc": "Unidade",
  "marca": "HEINZ",
  "pais": "Brasil",
  "categoria": "Alimentos",
  "dh_update": "2024-11-20T10:30:00",
  "link_foto": "https://..."
}
```

### 3. Get Product Image

**Endpoint**: `GET /api/gtin/img/:gtin`

**Headers**:
```
Authorization: Bearer {token}
```

**Response** (200 OK):
- **Content-Type**: `image/x-png` or `image/jpeg`
- **Body**: Image binary data
- Returns placeholder image if product has no photo

## Getting Started

### Step 1: Create Account

1. Visit https://gtin.rscsistemas.com.br/
2. Create an account or sign up for a plan
3. Get your username and password

### Step 2: Test the API

#### Test all EAN codes from NFCe:
```bash
python test_rsc_gtin_api.py "your_username" "your_password"
```

#### Test a single EAN:
```bash
python test_rsc_gtin_api.py "your_username" "your_password" 7896102000122
```

## Features

### ✅ What This API Provides

1. **Product Name** (with and without accents)
2. **Brand Name**
3. **NCM Code** (validation)
4. **CEST Code**
5. **Category**
6. **Country of Origin**
7. **Unit Type** (UN, KG, L, etc.)
8. **Product Images**
9. **Image Link URL**
10. **Last Update Date**

### ✅ Advantages

- **Detailed Information**: More fields than basic APIs
- **NCM + CEST**: Brazilian tax codes included
- **Image Support**: Direct image download
- **Portuguese**: Native Brazilian API
- **Unit Types**: Helps with inventory management

## Test Script Features

The `test_rsc_gtin_api.py` script includes:

- ✅ **Token Caching**: Reuses token for 1 hour
- ✅ **Batch Testing**: Tests all 6 EAN codes from NFCe
- ✅ **Single EAN Test**: Quick test for specific products
- ✅ **Image Download**: Automatically saves images
- ✅ **Image Dimensions**: Shows image size
- ✅ **Error Handling**: Clear error messages
- ✅ **JSON Export**: Saves results to file

## Expected Results

### Products from Your NFCe:

| Product | EAN | Expected to Find? |
|---------|-----|-------------------|
| ALFACE AMER BOLA 200G | 7898083580716 | Maybe (regional) |
| KETCHUP HEINZ 1,033KG | 7896102000122 | ✅ Very Likely |
| COENTRO MACO | 7898083580167 | Maybe (fresh produce) |
| RUCULA HIDROP MACO | 7898558680026 | Maybe (fresh produce) |
| CANJICA OKOSHI SAL M 40G | 7896639800325 | ✅ Likely |
| POLPA D.MARCHI ACER.100G | 7896519210206 | ✅ Likely |

**Note**: Packaged goods with well-known brands have higher success rates.

## API Comparison

### RSC GTIN API vs Cosmos API

| Feature | RSC GTIN | Cosmos API |
|---------|----------|------------|
| **Authentication** | Username/Password | Token only |
| **Token Validity** | 1 hour | Varies |
| **Product Name** | ✅ Yes | ✅ Yes |
| **Brand** | ✅ Yes | ✅ Yes |
| **NCM** | ✅ Yes | ✅ Yes |
| **CEST** | ✅ Yes | ❌ No |
| **Category** | ✅ Yes | ✅ Yes (GPC) |
| **Images** | ✅ Yes | ✅ Yes |
| **Price Info** | ❌ No | ✅ Yes |
| **Dimensions** | ❌ No | ✅ Yes (width/height/length) |
| **Weight** | ❌ No | ✅ Yes |
| **Country** | ✅ Yes | ❌ No |
| **Unit Type** | ✅ Yes | ❌ No |
| **Update Date** | ✅ Yes | ❌ No |

## Integration Example

```python
from test_rsc_gtin_api import get_bearer_token, get_product_info

# Step 1: Get token (valid for 1 hour)
username = "your_username"
password = "your_password"
token = get_bearer_token(username, password)

# Step 2: Query products
ean = "7896102000122"
product = get_product_info(ean, token)

if product:
    print(f"Nome: {product['nome']}")
    print(f"Marca: {product['marca']}")
    print(f"NCM: {product['ncm']}")
    print(f"CEST: {product['cest']}")
    print(f"Categoria: {product['categoria']}")
```

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Data retrieved |
| 400 | Bad Request | Check GTIN format |
| 401 | Unauthorized | Invalid credentials |
| 403 | Forbidden | Invalid auth header |
| 404 | Not Found | Product not in database |

## Rate Limiting

- Token valid for **1 hour**
- Number of requests depends on your **plan**
- **Tip**: Cache token and reuse it

## Cost Considerations

### Check Pricing:
- Visit: https://gtin.rscsistemas.com.br/
- Review available plans
- Compare with Cosmos API pricing

### Optimization Tips:
1. **Reuse tokens** (valid 1 hour)
2. **Cache responses** in your database
3. **Batch queries** when possible
4. **Only query new products**

## When to Use RSC GTIN API

### ✅ Use if:
- Need CEST codes specifically
- Need country of origin
- Need unit type information
- Prefer Brazilian-focused API
- Need product update dates

### ❌ Skip if:
- Need price information (use Cosmos)
- Need product dimensions (use Cosmos)
- Need weight information (use Cosmos)
- Budget is tight (Cosmos may be better value)

## Multi-API Strategy

### Best Approach: Use Both!

```python
# Try RSC first (for CEST, country, etc.)
rsc_data = get_product_info(ean, rsc_token)

# Then Cosmos (for prices, dimensions, etc.)
cosmos_data = get_product_by_gtin(ean)

# Combine both:
complete_data = {
    'ean': ean,
    'name': rsc_data['nome'] if rsc_data else cosmos_data['description'],
    'brand': rsc_data['marca'] if rsc_data else cosmos_data['brand']['name'],
    'ncm': rsc_data['ncm'] if rsc_data else cosmos_data['ncm']['code'],
    'cest': rsc_data['cest'] if rsc_data else None,  # Only RSC
    'price_range': cosmos_data['price'] if cosmos_data else None,  # Only Cosmos
    'country': rsc_data['pais'] if rsc_data else None,  # Only RSC
    'dimensions': {
        'width': cosmos_data['width'],
        'height': cosmos_data['height'],
        'length': cosmos_data['length']
    } if cosmos_data else None,  # Only Cosmos
}
```

## Troubleshooting

### Invalid Credentials
```
❌ Error 401: Invalid credentials
```
**Solution**: Check username and password

### Product Not Found
```
❌ Error 404: Product not found
```
**Solution**: Product not in their database (try Cosmos)

### Token Expired
```
❌ Error 403: Invalid authorization header
```
**Solution**: Request new token (automatic in test script)

### Connection Issues
```
⚠️  Connection timeout
```
**Solution**: Check internet connection, firewall settings

## Summary

### RSC GTIN API Status:
- ⏳ **Ready to test** (needs credentials)
- 📋 **Test script created** and ready
- 📚 **Documentation complete**
- 🔧 **Integration code prepared**

### Next Steps:
1. Create account at https://gtin.rscsistemas.com.br/
2. Get username and password
3. Run test: `python test_rsc_gtin_api.py "user" "pass"`
4. Compare results with Cosmos API
5. Decide which API(s) to use in production

---

**Documentation**: Complete
**Test Script**: Ready
**Status**: Waiting for credentials to test
**Last Updated**: 2025-11-21



