"""
Supabase Migration Script - Full Architecture (RESTORED)
Creates: markets, purchases, unique_products, processed_urls, product_backlog, product_lookup_log, llm_product_decisions, gtin_cache
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
-- DROP OLD SCHEMA
-- ============================================================================

DROP TABLE IF EXISTS product_backlog CASCADE;
DROP TABLE IF EXISTS product_lookup_log CASCADE;
DROP TABLE IF EXISTS unique_products CASCADE;
DROP TABLE IF EXISTS purchases CASCADE;
DROP TABLE IF EXISTS processed_urls CASCADE;
DROP TABLE IF EXISTS markets CASCADE;
DROP TABLE IF EXISTS llm_product_decisions CASCADE;
DROP TABLE IF EXISTS gtin_cache CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- ============================================================================
-- CREATE CLEAN SCHEMA (Current Architecture)
-- ============================================================================

-- 1. Markets
CREATE TABLE markets (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_market_name_address UNIQUE (name, address)
);

-- 2. Processed URLs (NFCe Tracking & Locking)
CREATE TABLE processed_urls (
    id BIGSERIAL PRIMARY KEY,
    nfce_url VARCHAR(1000) UNIQUE NOT NULL,
    market_id VARCHAR(20) NOT NULL,
    market_name VARCHAR(200),
    products_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing',
    error_message TEXT,
    processed_at TIMESTAMP DEFAULT NOW()
);

-- 3. Purchases (Raw Scan History)
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
    enriched BOOLEAN DEFAULT false,
    enrichment_status VARCHAR(20) DEFAULT 'pending',
    enrichment_error TEXT
);

-- 4. Unique Products (Enriched Data & Images)
CREATE TABLE unique_products (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(20) NOT NULL REFERENCES markets(market_id),
    ncm VARCHAR(8) NOT NULL,
    ean VARCHAR(50),
    product_name VARCHAR(200),
    unidade_comercial VARCHAR(10),
    price FLOAT NOT NULL,
    nfce_url VARCHAR(1000),
    image_url TEXT,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 5. Product Backlog (Failed matches for manual review)
CREATE TABLE product_backlog (
    id BIGSERIAL PRIMARY KEY,
    purchase_id BIGINT REFERENCES purchases(id),
    market_id VARCHAR(20) REFERENCES markets(market_id),
    original_product_name VARCHAR(200),
    ncm VARCHAR(8),
    ean VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Product Lookup Log (API Debugging)
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
    api_attempted BOOLEAN DEFAULT false,
    api_success BOOLEAN DEFAULT false,
    api_product_name VARCHAR(500),
    api_brand VARCHAR(200),
    api_image_url TEXT,
    api_error TEXT,
    api_from_cache BOOLEAN DEFAULT false,
    api_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_market_id ON markets(market_id);
CREATE INDEX idx_purchases_enriched ON purchases(enriched);
CREATE INDEX idx_unique_products_market_ean ON unique_products(market_id, ean);
CREATE INDEX idx_unique_products_ean ON unique_products(ean);
CREATE INDEX idx_unique_products_name ON unique_products(product_name);
CREATE INDEX idx_processed_status ON processed_urls(status);
"""
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
