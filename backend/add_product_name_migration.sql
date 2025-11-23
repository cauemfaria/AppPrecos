-- ============================================================================
-- Migration: Add product_name column to purchases and unique_products
-- ============================================================================

-- Add product_name to purchases table
ALTER TABLE purchases 
ADD COLUMN product_name VARCHAR(200);

-- Add product_name to unique_products table
ALTER TABLE unique_products 
ADD COLUMN product_name VARCHAR(200);

-- Create index for product name searches
CREATE INDEX idx_purchases_product_name ON purchases(product_name);
CREATE INDEX idx_unique_products_product_name ON unique_products(product_name);

-- Verify the changes
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name IN ('purchases', 'unique_products') 
AND column_name = 'product_name';

