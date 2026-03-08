-- Migration: Add scanned_prices table and varejo/atacado columns to unique_products
-- Run this in the Supabase SQL Editor

-- 1. New table: scanned_prices (worker barcode scan log)
CREATE TABLE IF NOT EXISTS scanned_prices (
    id BIGSERIAL PRIMARY KEY,
    market_id VARCHAR(20) NOT NULL REFERENCES markets(market_id),
    ean VARCHAR(50) NOT NULL,
    varejo_price DECIMAL(10,2) NOT NULL,
    atacado_price DECIMAL(10,2),
    product_name VARCHAR(500),
    brand VARCHAR(200),
    image_url TEXT,
    ncm VARCHAR(20),
    enriched BOOLEAN DEFAULT FALSE,
    enrichment_status VARCHAR(50) DEFAULT 'pending',
    enrichment_error TEXT,
    source VARCHAR(50) DEFAULT 'worker_scan',
    scanned_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scanned_prices_market ON scanned_prices(market_id);
CREATE INDEX IF NOT EXISTS idx_scanned_prices_ean ON scanned_prices(ean);
CREATE INDEX IF NOT EXISTS idx_scanned_prices_market_ean ON scanned_prices(market_id, ean);
CREATE INDEX IF NOT EXISTS idx_scanned_prices_enriched ON scanned_prices(enriched) WHERE enriched = FALSE;

-- 2. Add varejo/atacado columns to unique_products
ALTER TABLE unique_products
    ADD COLUMN IF NOT EXISTS varejo_price DECIMAL(10,2),
    ADD COLUMN IF NOT EXISTS atacado_price DECIMAL(10,2);
