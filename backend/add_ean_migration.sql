-- ============================================================================
-- Migration: Add EAN code support to existing tables
-- This script adds the 'ean' column to purchases and unique_products tables
-- Run this in Supabase SQL Editor if you already have existing tables
-- ============================================================================

-- Add EAN column to purchases table
ALTER TABLE purchases 
ADD COLUMN IF NOT EXISTS ean VARCHAR(50);

-- Add EAN column to unique_products table
ALTER TABLE unique_products 
ADD COLUMN IF NOT EXISTS ean VARCHAR(50);

-- Set default value for existing records (where ean is null)
UPDATE purchases 
SET ean = 'SEM GTIN' 
WHERE ean IS NULL;

UPDATE unique_products 
SET ean = 'SEM GTIN' 
WHERE ean IS NULL;

-- Verify the migration
SELECT 'Migration completed successfully!' as status;
SELECT COUNT(*) as total_purchases_with_ean FROM purchases WHERE ean IS NOT NULL;
SELECT COUNT(*) as total_unique_products_with_ean FROM unique_products WHERE ean IS NOT NULL;

