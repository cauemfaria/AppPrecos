# AppPrecos Web App - Complete Architecture Analysis

## 🏗️ Project Structure

```
frontend/src/
├── App.tsx                 # Main routing (React Router)
├── main.tsx               # Entry point
├── index.css              # Tailwind CSS imports
├── components/
│   └── Layout.tsx         # Main layout with navigation
├── pages/
│   ├── ScannerPage.tsx    # NFCe QR/URL scanning
│   ├── MarketsPage.tsx    # Browse markets & products
│   ├── ShoppingListPage.tsx # Create lists & compare prices
│   └── SettingsPage.tsx   # App settings
├── services/
│   └── api.ts             # API client (axios + services)
├── store/
│   └── useStore.ts        # State management (Zustand)
├── types/
│   └── index.ts           # TypeScript interfaces
└── assets/
    └── react.svg
```

---

## 📊 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     BACKEND API                              │
│         https://appprecos.onrender.com/api                   │
└───────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   MARKETS API    PRODUCTS API    NFCE API
   - GET /markets - GET /search  - POST /extract
   - GET /markets - POST /compare - GET /status
     /{id}/products
        │               │               │
        └───────────────┼───────────────┘
                        │
            ┌───────────▼────────────┐
            │   API SERVICE LAYER    │
            │   (api.ts)             │
            ├───────────────────────┤
            │ • marketService       │
            │ • productService      │
            │ • nfceService         │
            └───────────┬────────────┘
                        │
            ┌───────────▼────────────┐
            │   ZUSTAND STORE        │
            │   (useStore.ts)        │
            ├───────────────────────┤
            │ • shoppingList        │
            │ • selectedMarketIds   │
            │ • searchResults       │
            │                       │
            │ (Persisted to Local   │
            │  Storage)             │
            └───────────┬────────────┘
                        │
        ┌───────────────┼───────────────────────┐
        │               │                       │
        │               │                       │
  SCANNER PAGE    MARKETS PAGE    SHOPPING LIST PAGE
  • QR scanning   • List markets  • Search products
  • URL input     • View products • Manage list
  • Status queue  • Filter search • Select markets
                                  • Compare prices
                                  • View results
```

---

## 🎯 User Workflows

### **WORKFLOW 1: SCAN & IMPORT (Scanner Page)**

**Purpose:** Import receipt data into the system

**Steps:**
1. User opens **Scanner** tab
2. User either:
   - **Option A:** Clicks "Scan QR" → Camera opens → QR code captured
   - **Option B:** Manually pastes URL → Clicks "Add URL"
3. URL added to **Processing Queue** (displayed on right panel)
4. Frontend sends: `POST /api/nfce/extract { url, save: true, async: true }`
5. Backend processes asynchronously:
   - Extracts receipt data (products, market info)
   - Saves to database
   - Returns `record_id`
6. Frontend **polls** `/api/nfce/status/{record_id}` every 3 seconds
7. Status updates in real-time: `sending → processing → extracting → success/error`
8. Queue item auto-removes after 5 seconds if success/error
9. Market + Products now available in database

**Data Stored:**
- Market: name, address, market_id
- Products: product_name, ean, ncm, price, quantity, etc.

---

### **WORKFLOW 2: BROWSE MARKETS (Markets Page)**

**Purpose:** Explore imported markets and their products

**Steps:**
1. User opens **Markets** tab
2. Frontend calls: `GET /api/markets`
3. List of all markets displayed as cards
4. User can **search** by market name or address
5. User clicks on a market card
6. Modal opens showing market details
7. Frontend calls: `GET /api/markets/{market_id}/products`
8. Products list displayed in modal (sorted by name)
9. User can **search products** within market by name or NCM code
10. Product details visible: name, price, unit, EAN, NCM

**Search Logic:**
- `market_name.toLowerCase().includes(searchTerm)`
- `market_address.toLowerCase().includes(searchTerm)`

---

### **WORKFLOW 3: PRICE COMPARISON (Shopping List Page)**

**Purpose:** Compare product prices across multiple markets

**Complete Flow:**

#### **Step 1: Add Products to List**
```
User clicks "Add Product"
  ↓
Search Modal Opens
  ↓
User types product name (min 2 chars)
  ↓
Frontend calls: GET /api/products/search?name={query}&limit=50
  ↓
Results show: product_name, markets_count, min_price, max_price
  ↓
User clicks product
  ↓
Product added to shoppingList (via Zustand store)
  ↓
Modal closes, product visible in list
```

**Storage:**
- Shopping list stored in **localStorage** via Zustand persist
- Survives page refresh

#### **Step 2: Select Markets for Comparison**
```
User clicks "Markets" button
  ↓
Market Selection Modal Opens
  ↓
Frontend calls: GET /api/markets
  ↓
List of checkboxes displayed
  ↓
User selects up to 5 markets (MAX_MARKETS_FOR_COMPARISON = 5)
  ↓
Selection stored in Zustand selectedMarketIds
  ↓
Modal closes with updated count
```

**Validation:**
- Max 5 markets enforced with error message
- Error auto-clears after 3 seconds
- Selection persisted to localStorage

#### **Step 3: Compare Prices**
```
User clicks "Compare" button
  ↓
Frontend validates:
   - Shopping list not empty ✓
   - At least one market selected ✓
  ↓
Frontend calls: POST /api/products/compare
  Body: {
    products: [
      { product_name, ean, ncm },
      ...
    ],
    market_ids: ["MKT001", "MKT002", ...]
  }
  ↓
Backend processes:
   - Queries unique_products table for each product
   - Matches by EAN first, falls back to NCM
   - Returns prices per market
  ↓
Comparison Modal Opens
  ↓
Table displayed:
   - Left column: Product names (sticky)
   - Market columns: Prices with color coding
       • Green: Lowest price (best deal)
       • Red: Highest price
       • Blue: All prices equal
       • Gray: Product not available (N/A)
  ↓
User can close modal
```

---

## 💾 State Management (Zustand Store)

**Persisted to localStorage as `app-precos-storage`:**

```typescript
Interface AppState {
  // Shopping List Management
  shoppingList: ProductSearchItem[]
  addToShoppingList(product)        // Prevents duplicates
  removeFromShoppingList(product)   // Removes by EAN + name
  clearShoppingList()               // Empties list

  // Market Selection
  selectedMarketIds: string[]
  toggleMarketSelection(marketId)   // Toggle on/off
  clearMarketSelection()            // Clear all

  // Search Results (NOT persisted)
  searchResults: ProductSearchItem[]
  setSearchResults(results)
  clearSearchResults()
}
```

**Duplicate Prevention Logic:**
```typescript
// When adding product:
shoppingList.some(p => 
  p.ean === product.ean && 
  p.product_name === product.product_name
)
// If true, don't add
```

---

## 📡 API Endpoints & Data Models

### **Markets Service**
- `GET /api/markets` → `Market[]`
  - Returns: id, market_id, name, address
  
- `GET /api/markets/{market_id}/products` → `MarketProductsResponse`
  - Returns: market data + products array

### **Products Service**
- `GET /api/products/search?name={query}&limit={n}` → `ProductSearchResponse`
  - Returns aggregated data: markets_count, min/max_price
  
- `POST /api/products/compare` → `CompareResponse`
  - Request: products array + market_ids
  - Response: markets map + comparison table with prices

### **NFCe Service**
- `POST /api/nfce/extract` → `NFCeAsyncResponse`
  - Request: { url, save, async }
  - Response: record_id (for polling)
  
- `GET /api/nfce/status/{record_id}` → `NFCeStatusResponse`
  - Response: status, market_name, products_count, error_message

---

## 🔴 IDENTIFIED ISSUES & PROBLEMS

### **🚨 CRITICAL ISSUES**

#### **1. Race Condition in Shopping List Duplicates**
**Location:** `useStore.ts` line 30-32
```typescript
shoppingList.some(p => p.ean === product.ean && p.product_name === product.product_name)
```
**Problem:**
- Check and add happen in separate Redux updates (not atomic)
- Fast double-clicks can add duplicates to list
- Zustand doesn't prevent this race condition

**Impact:** Users can end up with duplicate items in comparison

**Fix:**
```typescript
addToShoppingList: (product) => 
  set((state) => {
    const exists = state.shoppingList.some(p => 
      p.ean === product.ean && p.product_name === product.product_name
    );
    return {
      shoppingList: exists ? state.shoppingList : [...state.shoppingList, product]
    };
  })
```

---

#### **2. Polling Loop Never Stops - Memory Leak**
**Location:** `ScannerPage.tsx` line 100-125
```typescript
useEffect(() => {
  const pollInterval = setInterval(async () => {
    // Polling happens every 3 seconds
    // No condition to stop polling when page unmounts
  }, 3000);
  
  return () => clearInterval(pollInterval);  // ← This runs on unmount
}, [processingQueue]);  // ← Dependency on changing array!
```

**Problems:**
1. **Dependency array includes `processingQueue`** - causes new interval on every update
2. **Multiple intervals created** - old ones keep running
3. **Memory leak** - intervals stack up (could have 50+ running)
4. **Infinite polls** - even completed items keep being polled

**Impact:** Severe performance degradation, browser slowdown, wasted API calls

**Fix:**
```typescript
useEffect(() => {
  const pendingItems = processingQueue.filter(item => 
    item.status === 'processing' || item.status === 'extracting'
  );

  if (pendingItems.length === 0) return;  // Don't poll if nothing pending

  const pollInterval = setInterval(async () => {
    // Poll only pending items
  }, 3000);

  return () => clearInterval(pollInterval);
}, [processingQueue.length]);  // Better: just track if items exist
```

---

#### **3. No Error Handling in Search Modal**
**Location:** `ShoppingListPage.tsx` line 44-61
```typescript
const handleSearch = async (query: string) => {
  // No try-catch around productService.searchProducts()
  try {
    const data = await productService.searchProducts(query);
    setSearchResults(data.results);
  } catch (error) {
    console.error("Search failed", error);
    // ← No user feedback! User doesn't know search failed
    // searchResults stays empty, user confused
  }
};
```

**Problem:** Network errors silently fail, user gets empty results with no explanation

**Impact:** Poor UX - user thinks there are no products when actually network failed

**Fix:**
```typescript
const [searchError, setSearchError] = useState<string | null>(null);

const handleSearch = async (query: string) => {
  setSearchTerm(query);
  setSearchError(null);
  
  if (query.length < 2) {
    setSearchResults([]);
    return;
  }
  
  setIsSearching(true);
  try {
    const data = await productService.searchProducts(query);
    setSearchResults(data.results);
  } catch (error: any) {
    const message = error.response?.data?.error || error.message || "Search failed";
    setSearchError(message);
    setSearchResults([]);
  } finally {
    setIsSearching(false);
  }
};

// Display in modal:
{searchError && <div className="error-banner">{searchError}</div>}
```

---

#### **4. Markets Modal State Not Cleared**
**Location:** `ShoppingListPage.tsx`
```typescript
// Issue: When user opens Markets modal, then opens Shopping List page again:
// - Modal still shows selected state from before
// - But user can deselect/reselect and it affects comparison
// - Confusing UI state
```

**Problem:** Modal state (isMarketModalOpen, markets list) persists across page navigation

**Impact:** User confusion about what markets are actually selected

---

### **⚠️ HIGH PRIORITY ISSUES**

#### **5. No Debounce on Product Search**
**Location:** `ShoppingListPage.tsx` line 44-61
```typescript
onChange={(e) => handleSearch(e.target.value)}
```

**Problem:** 
- Every keystroke triggers API call
- 10 characters = 10 API calls
- Backend gets hammered
- Unnecessary network traffic

**Fix:** Add 500ms debounce
```typescript
import { useMemo } from 'react';

const [searchTerm, setSearchTerm] = useState('');
const [searchResults, setSearchResults] = useState([]);

// Debounced search
useEffect(() => {
  const timer = setTimeout(() => {
    if (searchTerm.length >= 2) {
      handleSearch(searchTerm);
    }
  }, 500);
  
  return () => clearTimeout(timer);
}, [searchTerm]);
```

---

#### **6. No Network Error Handling in Markets Modal**
**Location:** `ShoppingListPage.tsx` line 35-42
```typescript
const fetchMarkets = async () => {
  try {
    const data = await marketService.getMarkets();
    setMarkets(data);
  } catch (error) {
    console.error("Failed to fetch markets", error);
    // ← Modal shows empty list, user thinks there are no markets
  }
};
```

**Impact:** User can't see markets to select for comparison

**Fix:** Show error message instead of empty list

---

#### **7. Temporary ID Collisions in Scanner**
**Location:** `ScannerPage.tsx` line 63
```typescript
const tempId = -Math.floor(Math.random() * 1000000); // Random negative ID
```

**Problem:**
- Pure random can collide
- Two simultaneous scans could get same ID
- UI state gets mixed up

**Fix:** Use timestamp + random or UUID
```typescript
const tempId = -Date.now() - Math.random();
// or
import { v4 as uuidv4 } from 'uuid';
const tempId = uuidv4();
```

---

#### **8. No Connection Error Handling (Global)**
**Location:** `api.ts`
```typescript
const api = axios.create({
  baseURL: API_BASE_URL,
  // No error interceptor
  // No timeout handling
  // No retry logic
});
```

**Problem:**
- If backend unreachable, all pages break silently
- No retry mechanism
- User gets stuck indefinitely

**Fix:**
```typescript
api.interceptors.response.use(
  response => response,
  error => {
    if (!error.response) {
      // Network error - backend unreachable
      console.error("Backend unreachable:", error.message);
      // Could show toast: "Backend server is down"
    }
    return Promise.reject(error);
  }
);
```

---

### **⚠️ MEDIUM PRIORITY ISSUES**

#### **9. Shopping List Items Not Validated Before Compare**
**Location:** `ShoppingListPage.tsx` line 73-82
```typescript
// Products added to list are from search results
// But search results don't have complete product data
// Comparison might fail if data is incomplete
```

**Potential Issue:**
- ProductSearchItem might be missing required fields
- Backend comparison expects specific format
- Type mismatch between search and compare data

---

#### **10. No Loading State for Markets Fetch**
**Location:** `ShoppingListPage.tsx` line 31-42
```typescript
useEffect(() => {
  fetchMarkets();  // Called on mount
}, []);

// No setIsLoadingMarkets state
// Markets modal shows empty list while loading
// User clicks but nothing happens
```

**Fix:** Add loading state with spinner

---

#### **11. Comparison Table Not Responsive for Small Screens**
**Location:** `ShoppingListPage.tsx` (Comparison Modal)
```typescript
// Sticky left column implementation might break on mobile
// Market column headers might overflow
// Font sizes too large for mobile
```

---

### **ℹ️ LOW PRIORITY / NICE-TO-HAVE**

#### **12. No Pagination for Markets**
- If there are 1000+ markets, all loaded at once
- Could implement lazy loading or pagination

#### **13. No Sorting Options**
- Markets list not sortable by name, location, etc.
- Products not sortable by price, popularity, etc.

#### **14. No Recent Searches**
- Search history could help users find products faster

#### **15. QR Scanner Has No Fallback UI**
- If camera permission denied, shows blank screen
- Should show message like "Camera permission required"

---

## ✅ What Works Well

1. **Clean Architecture** - Separated concerns (services, store, pages)
2. **Type Safety** - Full TypeScript types for all data models
3. **State Persistence** - Shopping list survives refresh
4. **Responsive Design** - Tailwind classes handle mobile/desktop
5. **Queue System** - Good UX for async NFCe processing
6. **Error Status Handling** - Duplicate detection (409 status)
7. **Color Coding** - Visual indicators for price comparisons
8. **Modal Architecture** - Clean modal stacking for dialogs

---

## 📋 Summary of Issues by Severity

| Severity | Count | Issues |
|----------|-------|--------|
| 🚨 Critical | 2 | Race condition, Memory leak |
| ⚠️ High | 4 | Error handling, Debounce, ID collisions, Network errors |
| ⚠️ Medium | 2 | Data validation, Loading states |
| ℹ️ Low | 4 | Pagination, Sorting, History, Fallbacks |

