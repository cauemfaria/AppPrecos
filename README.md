# AppPrecos - Brazilian Price Comparison App

Price comparison application that extracts product data from NFCe receipts and uses AI-powered enrichment to standardize products across multiple markets.

---

## 🏗️ Architecture Overview

AppPrecos uses a **decoupled architecture** to ensure a fast user experience while maintaining high data quality:

1.  **Fast Extraction (Backend API):** Instantly extracts raw data from NFCe (receipts) using Playwright and saves it to a history table.
2.  **Product Enrichment (Background Worker):** A separate worker process standardizes product names using the Bluesoft Cosmos API and LLMs (GPT-4o-mini).
3.  **Mobile Frontend:** Android app (Kotlin) for scanning and price comparison.
4.  **Database:** Supabase (PostgreSQL) as the central data hub.

---

## 🚀 Key Technical Features

### ✅ Decoupled Data Flow
The extraction process no longer waits for external product enrichment.
- **NFCe Scan:** Extracted in ~15s and immediately available in history.
- **Enrichment:** Handled by a "one-shot" worker that rotates through multiple API tokens to bypass rate limits.

### ✅ Smart Product Standardization
Standardizes "ugly" receipt names (e.g., `QJ MUSS PARLAK`) into clean, standardized names in **UPPER CASE** (e.g., `QUEIJO MUSSARELA PARLAK`) using:
- **Bluesoft Cosmos API:** Primary source for Brazilian product data (with intelligent token rotation).
- **LLM Matching (GPT-4o-mini):** AI for matching similar products within the same NCM and formatting new entries in CAIXA ALTA.

### ✅ Database-Backed Extraction Lock
Prevents concurrent extractions of the same URL across multiple workers using a PostgreSQL-based status lock.

---

## 📂 Project Structure

```
AppPrecos/
├── android/                    # Android mobile app (Kotlin)
│   └── app/src/main/          # UI, Scanner, API Client
│
└── backend/                    # Python Flask Backend
    ├── app.py                  # Main REST API server & Enrichment Logic
    ├── enrichment_worker.py    # Background worker (Cosmos Blue + LLM)
    ├── nfce_extractor.py       # Playwright scraper for SEFAZ sites
    ├── browser_profile/        # (Auto-generated) Playwright cache
    ├── .env                    # Environment variables (Tokens, Keys)
    └── pyproject.toml          # Dependency management (uv)
```

---

## 🛠️ Technology Stack

- **Backend:** Python 3.13+, Flask, Playwright (Chromium)
- **Frontend:** Android (Kotlin, Material Design 3, CameraX)
- **Database:** Supabase (PostgreSQL)
- **AI/APIs:** OpenAI (GPT-4o-mini), Bluesoft Cosmos
- **Package Manager:** `uv` (faster than pip)

---

## 📊 Database Schema (Supabase)

The system uses 8 key tables for data persistence and auditing:

1.  **`markets`**: Stores market metadata (unique by name + address).
2.  **`purchases`**: Raw purchase history. Tracks `enriched` status (boolean).
3.  **`unique_products`**: Standardized products with the **latest** price per market.
4.  **`processed_urls`**: Tracks receipt URLs and extraction status (lock mechanism).
5.  **`product_lookup_log`**: Audit trail of every API lookup (Cosmos, LLM).
6.  **`gtin_cache`**: Cache for EAN/GTIN lookups to save API credits.
7.  **`product_backlog`**: Stores items that failed enrichment for manual review.
8.  **`llm_product_decisions`**: Logs AI reasoning for product matching.

---

## ⚙️ Setup Instructions

### Backend Setup (using `uv`)

1.  **Install `uv`** (if not installed):
    ```bash
    pip install uv
    ```

2.  **Sync Dependencies:**
    ```bash
    cd backend
    uv sync
    ```

3.  **Install Playwright Browser:**
    ```bash
    uv run playwright install chromium
    ```

4.  **Configure Environment Variables (`.env`):**
    ```env
    SUPABASE_URL=...
    SUPABASE_SERVICE_ROLE_KEY=...
    OPENAI_API_KEY=...
    COSMOS_TOKENS=token1,token2,token3  # Supports rotation
    COSMOS_USER_AGENT=Cosmos-API-Request
    ```

### Running the System

-   **Start API Server:** `uv run python app.py`
-   **Run Enrichment Worker:** `uv run python enrichment_worker.py` (Processes pending products and terminates)

---

## 🔄 Data Flow Detail

1.  **Extraction:**
    - App scans QR → Backend checks `processed_urls`.
    - Playwright navigates SEFAZ → Extracts raw name/EAN/Price.
    - Saves to `purchases` with `enriched=False`.
2.  **Enrichment (Worker):**
    - Worker fetches items where `enriched=False`.
    - **Step 1:** Cosmos Blue (tries Token 1, if 429 rotates to Token 2...).
    - **Step 2:** LLM GPT-4o-mini (match with existing products or format new name in CAIXA ALTA).
    - Upserts result to `unique_products` and marks `enriched=True`.

---

**Built with a focus on data quality, speed, and resilient API integration.** ✨
