# AppPrecos API Reference

Base URL: `http://localhost:5000/api`

## Markets

### Get All Markets
```
GET /api/markets
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Supermercado Shibata Ltda",
    "address": "Av Getulio vargas, 1430, Jd.Primavera, Jacarei, SP",
    "created_at": "2025-10-15T20:00:00"
  }
]
```

### Create Market
```
POST /api/markets
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Market Name",
  "address": "Full Address"
}
```

**Response:** `201 Created`

### Get Market by ID
```
GET /api/markets/{id}
```

### Delete Market
```
DELETE /api/markets/{id}
```

## Purchases

### Get Purchases
```
GET /api/purchases?market_id={id}
```

### Add Purchase
```
POST /api/purchases
Content-Type: application/json
```

**Request Body:**
```json
{
  "market_id": 1,
  "ncm": "07099300",
  "quantity": 0.431,
  "unidade_comercial": "KG",
  "price": 2.15,
  "nfce_url": "https://...",
  "purchase_date": "2025-10-15T19:44:53"
}
```

### Bulk Add Purchases
```
POST /api/purchases/bulk
Content-Type: application/json
```

**Request Body:**
```json
{
  "market_id": 1,
  "nfce_url": "https://...",
  "products": [
    {
      "ncm": "07099300",
      "quantity": 0.431,
      "unidade_comercial": "KG",
      "price": 2.15
    }
  ]
}
```

## Unique Products

### Get Unique Products
```
GET /api/unique-products?market_id={id}
```

### Get Product by NCM
```
GET /api/unique-products/{ncm}?market_id={id}
```

## NFCe Integration

### Extract NCM from NFCe URL
```
POST /api/nfce/extract
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://www.nfce.fazenda.sp.gov.br/...",
  "market_id": 1,
  "save": true
}
```

**Response:**
```json
{
  "message": "NCM codes extracted and saved successfully",
  "products": [
    {
      "number": 1,
      "product": "ABOBORA PESCOCO KG",
      "ncm": "07099300",
      "quantity": 0.431,
      "unidade_comercial": "KG",
      "price": 2.15
    }
  ],
  "saved_to_market": 1
}
```

## Utilities

### Get Statistics
```
GET /api/stats
```

**Response:**
```json
{
  "total_markets": 2,
  "total_purchases": 45,
  "total_unique_products": 23
}
```

### Compare Prices
```
GET /api/price-comparison/{ncm}
```

**Response:**
```json
{
  "ncm": "07099300",
  "markets_count": 3,
  "cheapest_price": 1.99,
  "results": [
    {
      "market_id": 1,
      "market_name": "Market A",
      "market_address": "...",
      "ncm": "07099300",
      "price": 1.99,
      "unidade_comercial": "KG",
      "last_updated": "2025-10-15T20:00:00"
    }
  ]
}
```

