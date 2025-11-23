# Cosmos API Setup Guide

## Overview
The Cosmos API provides access to a comprehensive product database using GTIN/EAN codes. This guide will help you set up the API integration.

## Getting API Credentials

1. **Visit**: https://cosmos.bluesoft.com.br/
2. **Create an account** or **log in**
3. **Get your credentials**:
   - `COSMOS_TOKEN`: Your API authentication token
   - `COSMOS_USER_AGENT`: Your specific user agent string

## Configuration

### Step 1: Create .env file

Create a `.env` file in the `backend/` directory (if it doesn't exist):

```bash
cd backend
touch .env  # Linux/Mac
type nul > .env  # Windows
```

### Step 2: Add Cosmos Credentials

Add the following lines to your `.env` file:

```env
# Cosmos API Configuration
COSMOS_TOKEN=your_actual_token_here
COSMOS_USER_AGENT=your_actual_user_agent_here
```

**Example** (with fake credentials):
```env
COSMOS_TOKEN=abc123def456ghi789jkl012mno345pqr678
COSMOS_USER_AGENT=MyApp/1.0 (contact@example.com)
```

## Testing the Integration

### Test 1: Run without credentials (shows what's needed)
```bash
cd backend
python test_cosmos_api.py
```

### Test 2: Run with credentials (tests all EANs from NFCe)
```bash
cd backend
python test_cosmos_api.py
```

### Test 3: Test a single EAN
```bash
cd backend
python test_cosmos_api.py 7896102000122
```

## API Endpoints

### Get Product by GTIN/EAN
```
GET https://api.cosmos.bluesoft.com.br/gtins/{code}.json
```

**Example Response:**
```json
{
    "gtin": 7891910000197,
    "description": "AÇÚCAR REFINADO UNIÃO 1KG",
    "brand": {
        "name": "UNIÃO"
    },
    "price": "R$ 2,99",
    "avg_price": 2.99,
    "ncm": {
        "code": "17019900",
        "description": "Outros"
    },
    "thumbnail": "https://cdn-cosmos.bluesoft.com.br/products/7891910000197"
}
```

### Other Available Endpoints
- `GET /gpcs/{code}` - Get GPC details
- `GET /ncms/{code}/products` - Get products by NCM
- `GET /products?query={query}` - Search products

## API Limits & Status Codes

### Success Codes
- `200 OK`: Request successful

### Error Codes
- `401 Unauthorized`: Invalid token
- `404 Not Found`: Product not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

The Cosmos API has rate limiting policies. If you exceed the limit, you'll receive a `429` status code. Wait a few moments before retrying.

## Integration with NFCe Scraper

The EAN codes extracted from NFCe receipts can be used to get additional product information from Cosmos:

```python
from test_cosmos_api import get_product_by_gtin

# EAN from NFCe
ean = "7896102000122"

# Get product details from Cosmos
product = get_product_by_gtin(ean)

if product:
    print(f"Product: {product['description']}")
    print(f"Brand: {product['brand']['name']}")
    print(f"Price: {product['price']}")
```

## Benefits of Cosmos Integration

1. **Product Names**: Get standardized product descriptions
2. **Brand Information**: Know the exact brand
3. **Images**: Get product thumbnails
4. **Pricing**: Compare with average market prices
5. **NCM Validation**: Cross-reference NCM codes
6. **Product Details**: Weight, dimensions, etc.

## Troubleshooting

### "COSMOS_TOKEN not configured"
- Make sure `.env` file exists in `backend/` directory
- Check that the token is correctly set
- No quotes needed around the values

### "Authentication failed"
- Verify your token is correct
- Check if your account is active
- Try logging in to the Cosmos website

### "Rate limit exceeded"
- Wait a few minutes before making more requests
- Implement caching for frequently accessed products
- Consider upgrading your API plan

### "Product not found (404)"
- Not all products are in the Cosmos database
- This is normal for very new or regional products
- The NFCe data is still valid and useful

## Example: Full Workflow

1. **Scan NFCe** → Get EAN codes
2. **For each EAN** → Query Cosmos API
3. **Enrich data** → Add product details from Cosmos
4. **Store in database** → Save complete product information
5. **Display to user** → Show product names, images, brands

## Cost Considerations

- Check Cosmos pricing at: https://cosmos.bluesoft.com.br/
- Most plans include a certain number of free requests
- Consider caching frequently accessed products
- Use database to avoid repeated API calls

## Support

- **Cosmos Documentation**: https://cosmos.bluesoft.com.br/api
- **Contact**: Check the Cosmos website for support options


