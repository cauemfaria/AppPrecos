"""
Supabase Migration Script - 3-Table Architecture
Creates: markets, purchases, unique_products, processed_urls
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    """Display SQL to create all necessary tables in Supabase"""
    
    print("=" * 77)
    print(" Supabase Migration - 3-Table Architecture")
    print("=" * 77)
    
    sql_command = """
-- ============================================================================
-- DROP OLD SCHEMA (if exists)
-- ============================================================================

DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS processed_urls CASCADE;
DROP TABLE IF EXISTS markets CASCADE;

-- ============================================================================
-- CREATE NEW SCHEMA - 3-Table Design
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
    quantity FLOAT NOT NULL,
    unidade_comercial VARCHAR(10),
    total_price FLOAT NOT NULL,
    unit_price FLOAT NOT NULL,
    nfce_url VARCHAR(1000),
    purchase_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_purchases_market_id ON purchases(market_id);
CREATE INDEX idx_purchases_ncm ON purchases(ncm);
CREATE INDEX idx_purchases_date ON purchases(purchase_date);

-- TABLE 3: Unique Products (Latest Prices)
CREATE TABLE unique_products (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(20) NOT NULL REFERENCES markets(market_id),
    ncm VARCHAR(8) NOT NULL,
    unidade_comercial VARCHAR(10),
    price FLOAT NOT NULL,
    nfce_url VARCHAR(1000),
    last_updated TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_product_per_market UNIQUE(market_id, ncm)
);

CREATE INDEX idx_unique_products_market_id ON unique_products(market_id);
CREATE INDEX idx_unique_products_ncm ON unique_products(ncm);

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
"""
    
    print("\nCopy and run this SQL in Supabase SQL Editor:")
    print("-" * 77)
    print(sql_command)
    print("-" * 77)
    
    print("\n" + "=" * 77)
    print(" Instructions:")
    print("=" * 77)
    print("\n1. Go to https://app.supabase.com")
    print("2. Select your project: gqfnbhhlvyrljfmfdcsf")
    print("3. Go to SQL Editor")
    print("4. Click 'New Query'")
    print("5. Paste the SQL above")
    print("6. Click 'Run'")
    print("\n" + "=" * 77)


if __name__ == '__main__':
    create_tables()
