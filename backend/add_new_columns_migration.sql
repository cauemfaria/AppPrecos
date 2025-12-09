-- Migration: Add market_name and error_message columns to processed_urls table
-- Run this in Supabase SQL Editor before deploying the new backend

-- Add market_name column (to store market name for quick access in status response)
ALTER TABLE processed_urls 
ADD COLUMN IF NOT EXISTS market_name TEXT DEFAULT '';

-- Add error_message column (to store error details when processing fails)
ALTER TABLE processed_urls 
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Verify the columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'processed_urls'
ORDER BY ordinal_position;

