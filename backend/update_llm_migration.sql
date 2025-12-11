-- Migration: Update for Cross-Market LLM Product Matching
-- Run this in Supabase SQL Editor AFTER the initial llm_table migration
-- 
-- This migration:
--   1. Adds canonical_name column to llm_product_decisions
--   2. Adds indexes for better query performance on unique_products

-- ============================================================================
-- STEP 1: Add canonical_name column to llm_product_decisions
-- ============================================================================
-- Stores the formatted/canonical product name for debugging

ALTER TABLE llm_product_decisions 
ADD COLUMN IF NOT EXISTS canonical_name VARCHAR(200);

-- ============================================================================
-- STEP 2: Add indexes to unique_products for cross-market queries
-- ============================================================================

-- Index for searching products by name (used in product search)
CREATE INDEX IF NOT EXISTS idx_unique_products_name 
ON unique_products(product_name);

-- Index for NCM-only queries (cross-market matching)
CREATE INDEX IF NOT EXISTS idx_unique_products_ncm 
ON unique_products(ncm);

-- Composite index for checking if product exists in specific market
CREATE INDEX IF NOT EXISTS idx_unique_products_market_ncm_name 
ON unique_products(market_id, ncm, product_name);

-- ============================================================================
-- STEP 3: Verify processed_urls has required columns
-- ============================================================================
-- These should already exist from add_new_columns_migration.sql

ALTER TABLE processed_urls 
ADD COLUMN IF NOT EXISTS market_name TEXT;

ALTER TABLE processed_urls 
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- ============================================================================
-- Summary of table structures after this migration:
-- ============================================================================
-- 
-- llm_product_decisions:
--   - id, market_id, ncm, new_product_name, canonical_name (NEW),
--   - existing_products, llm_prompt, llm_response, decision,
--   - matched_product_id, success, error_message, execution_time_ms, created_at
--
-- unique_products:
--   - id, market_id, ncm, ean, product_name (now canonical!), 
--   - unidade_comercial, price, nfce_url, last_updated, created_at
--   - Indexes: market_ncm, ncm, name, market_ncm_name
--
-- processed_urls:
--   - id, nfce_url, market_id, market_name, products_count,
--   - status, error_message, processed_at

