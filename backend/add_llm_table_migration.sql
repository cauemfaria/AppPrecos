-- Migration: LLM-based Product Identification
-- Run this in Supabase SQL Editor
-- This migration:
--   1. Removes the unique constraint from unique_products (allows multiple products with same NCM)
--   2. Creates the llm_product_decisions table for logging LLM calls

-- ============================================================================
-- STEP 1: Remove unique constraint from unique_products
-- ============================================================================
-- This allows multiple products with the same NCM in the same market
-- (e.g., Coca-Cola and Pepsi both have NCM 22021000)

ALTER TABLE unique_products 
DROP CONSTRAINT IF EXISTS unique_product_per_market;

-- Add composite index for faster lookups
CREATE INDEX IF NOT EXISTS idx_unique_products_market_ncm 
ON unique_products(market_id, ncm);

-- ============================================================================
-- STEP 2: Create llm_product_decisions table
-- ============================================================================
-- Logs all LLM calls for product identification decisions

CREATE TABLE IF NOT EXISTS llm_product_decisions (
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

-- Indexes for debugging queries
CREATE INDEX IF NOT EXISTS idx_llm_decisions_market ON llm_product_decisions(market_id);
CREATE INDEX IF NOT EXISTS idx_llm_decisions_ncm ON llm_product_decisions(ncm);
CREATE INDEX IF NOT EXISTS idx_llm_decisions_created ON llm_product_decisions(created_at);
CREATE INDEX IF NOT EXISTS idx_llm_decisions_success ON llm_product_decisions(success);

-- Comment on table
COMMENT ON TABLE llm_product_decisions IS 'Log of all LLM calls for product identification decisions';

