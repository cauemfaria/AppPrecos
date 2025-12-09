"""
Supabase Migration Script - 3-Table Architecture + LLM Logging
Creates: markets, purchases, unique_products, processed_urls, llm_product_decisions
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
    ean VARCHAR(50),
    product_name VARCHAR(200),
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
CREATE INDEX idx_purchases_product_name ON purchases(product_name);

-- TABLE 3: Unique Products (Latest Prices)
-- NOTE: No unique constraint on (market_id, ncm) because multiple products can share same NCM
-- LLM-based matching determines if products are the same or different
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
CREATE INDEX idx_unique_products_market_ncm ON unique_products(market_id, ncm);

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

-- TABLE 5: LLM Product Decisions (Debugging/Logging)
-- Logs all LLM calls for product identification decisions
CREATE TABLE llm_product_decisions (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(20) NOT NULL,
    ncm VARCHAR(8) NOT NULL,
    new_product_name VARCHAR(200),
    existing_products JSONB,  -- Array of {id, name} objects
    llm_prompt TEXT,
    llm_response TEXT,
    decision VARCHAR(50),     -- "CREATE_NEW" or "UPDATE:{id}" or "SKIPPED"
    matched_product_id BIGINT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_llm_decisions_market ON llm_product_decisions(market_id);
CREATE INDEX idx_llm_decisions_ncm ON llm_product_decisions(ncm);
CREATE INDEX idx_llm_decisions_created ON llm_product_decisions(created_at);
CREATE INDEX idx_llm_decisions_success ON llm_product_decisions(success);

COMMENT ON TABLE llm_product_decisions IS 'Log of all LLM calls for product identification decisions';
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
