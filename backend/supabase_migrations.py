"""
Supabase Migration Script - Full Architecture
Creates: markets, purchases, unique_products, processed_urls, product_backlog, product_lookup_log
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    """Display SQL to create all necessary tables in Supabase"""
    
    print("=" * 77)
    print(" Supabase Migration - Full Architecture")
    print("=" * 77)
    
    sql_command = """
-- ============================================================================
-- DROP OLD SCHEMA (if exists)
-- ============================================================================

DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS product_backlog CASCADE;
DROP TABLE IF EXISTS product_lookup_log CASCADE;
DROP TABLE IF EXISTS unique_products CASCADE;
DROP TABLE IF EXISTS purchases CASCADE;
DROP TABLE IF EXISTS processed_urls CASCADE;
DROP TABLE IF EXISTS markets CASCADE;

-- ============================================================================
-- CREATE NEW SCHEMA
-- ============================================================================

-- TABLE 1: Markets
CREATE TABLE markets (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_market_name_address UNIQUE (name, address)
);

CREATE INDEX idx_market_id ON markets(market_id);

-- TABLE 2: Purchases (Full History - Raw Data)
CREATE TABLE purchases (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(20) NOT NULL REFERENCES markets(market_id),
    ncm VARCHAR(8) NOT NULL,
    ean VARCHAR(50),
    product_name VARCHAR(200),
    quantity FLOAT NOT NULL,
    unidade_comercial VARCHAR(10),
    total_price FLOAT NOT NULL,
    unit_price FLOAT NOT NULL,
    nfce_url VARCHAR(1000),
    purchase_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    -- Enrichment Tracking
    enriched BOOLEAN DEFAULT false,
    enrichment_status VARCHAR(20) DEFAULT 'pending',
    enrichment_error TEXT
);

CREATE INDEX idx_purchases_market_id ON purchases(market_id);
CREATE INDEX idx_purchases_ncm ON purchases(ncm);
CREATE INDEX idx_purchases_date ON purchases(purchase_date);
CREATE INDEX idx_purchases_product_name ON purchases(product_name);
CREATE INDEX idx_purchases_ean ON purchases(ean);
CREATE INDEX idx_purchases_enriched ON purchases(enriched);

-- TABLE 3: Unique Products (Latest Prices)
-- Matches products by market_id AND ean (Deterministic)
CREATE TABLE unique_products (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(20) NOT NULL REFERENCES markets(market_id),
    ncm VARCHAR(8) NOT NULL,
    ean VARCHAR(50),
    product_name VARCHAR(200),
    unidade_comercial VARCHAR(10),
    price FLOAT NOT NULL,
    nfce_url VARCHAR(1000),
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_unique_products_market_id ON unique_products(market_id);
CREATE INDEX idx_unique_products_ncm ON unique_products(ncm);
CREATE INDEX idx_unique_products_product_name ON unique_products(product_name);
CREATE INDEX idx_unique_products_market_ean ON unique_products(market_id, ean);
CREATE INDEX idx_unique_products_ean ON unique_products(ean);

-- TABLE 4: Processed URLs (with Status Tracking)
CREATE TABLE processed_urls (
    id BIGSERIAL PRIMARY KEY,
    nfce_url VARCHAR(1000) UNIQUE NOT NULL,
    market_id VARCHAR(20) NOT NULL,
    products_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing',
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_processed_urls_nfce ON processed_urls(nfce_url);
CREATE INDEX idx_processed_urls_market ON processed_urls(market_id);
CREATE INDEX idx_processed_urls_status ON processed_urls(status);

-- TABLE 5: Product Backlog (Items that failed enrichment)
CREATE TABLE product_backlog (
    id BIGSERIAL PRIMARY KEY,
    purchase_id BIGINT REFERENCES purchases(id),
    market_id VARCHAR(20) REFERENCES markets(market_id),
    original_product_name VARCHAR(200),
    ncm VARCHAR(8),
    ean VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_backlog_purchase ON product_backlog(purchase_id);

-- TABLE 6: Product Lookup Log (Debug & API tracking)
CREATE TABLE product_lookup_log (
    id BIGSERIAL PRIMARY KEY,
    nfce_url VARCHAR(1000),
    market_id VARCHAR(20),
    gtin VARCHAR(50),
    ncm VARCHAR(8),
    original_name VARCHAR(500),
    final_name VARCHAR(500),
    source_used VARCHAR(50),
    success BOOLEAN,
    -- API Details
    api_attempted BOOLEAN DEFAULT false,
    api_success BOOLEAN DEFAULT false,
    api_product_name VARCHAR(500),
    api_brand VARCHAR(200),
    api_error TEXT,
    api_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lookup_log_gtin ON product_lookup_log(gtin);
CREATE INDEX idx_lookup_log_success ON product_lookup_log(success);
"""
    
    print("\nCopy and run this SQL in Supabase SQL Editor:")
    print("-" * 77)
    print(sql_command)
    print("-" * 77)
    
    print("\n" + "=" * 77)
    print(" Instructions:")
    print("=" * 77)
    print("\n1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Go to SQL Editor")
    print("4. Click 'New Query'")
    print("5. Paste the SQL above")
    print("6. Click 'Run'")
    print("\n" + "=" * 77)


if __name__ == '__main__':
    create_tables()
