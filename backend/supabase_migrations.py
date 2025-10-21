"""
Supabase Migration Script - Creates Required Tables
Run this script once to set up Supabase PostgreSQL tables
"""

import os
from dotenv import load_dotenv
from supabase_config import get_supabase_admin_client

# Load environment variables
load_dotenv()

def create_tables():
    """Create all necessary tables in Supabase"""
    supabase = get_supabase_admin_client()
    
    print("=" * 77)
    print(" Supabase Migration - Creating Tables")
    print("=" * 77)
    
    try:
        # Note: In Supabase, you'll need to create tables using the SQL Editor in the web console
        # or use the PostgREST API with raw SQL. Here's the SQL to run:
        
        sql_commands = [
            """
            CREATE TABLE IF NOT EXISTS markets (
                id BIGSERIAL PRIMARY KEY,
                market_id VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                address VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX idx_market_id ON markets(market_id);
            """,
            
            """
            CREATE TABLE IF NOT EXISTS products (
                id BIGSERIAL PRIMARY KEY,
                market_id VARCHAR(20) NOT NULL REFERENCES markets(market_id),
                ncm VARCHAR(8) NOT NULL,
                quantity FLOAT NOT NULL,
                unidade_comercial VARCHAR(10),
                price FLOAT NOT NULL,
                nfce_url VARCHAR(1000),
                purchase_date TIMESTAMP NOT NULL,
                product_type VARCHAR(20) DEFAULT 'full_history',
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(market_id, ncm, product_type)
            );
            CREATE INDEX idx_market_ncm ON products(market_id, ncm);
            CREATE INDEX idx_product_type ON products(product_type);
            """,
            
            """
            CREATE TABLE IF NOT EXISTS processed_urls (
                id BIGSERIAL PRIMARY KEY,
                nfce_url VARCHAR(1000) UNIQUE NOT NULL,
                market_id VARCHAR(20) NOT NULL,
                products_count INTEGER DEFAULT 0,
                processed_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX idx_nfce_url ON processed_urls(nfce_url);
            CREATE INDEX idx_market_processed ON processed_urls(market_id);
            """
        ]
        
        print("\nSQL Commands to run in Supabase SQL Editor:")
        print("-" * 77)
        for i, sql in enumerate(sql_commands, 1):
            print(f"\n{i}. Execute this SQL in Supabase:")
            print(sql)
        
        print("\n" + "=" * 77)
        print(" Instructions:")
        print("=" * 77)
        print("\n1. Go to https://app.supabase.com")
        print("2. Select your project: gqfnbhhlvyrljfmfdcsf")
        print("3. Go to SQL Editor")
        print("4. Create a new query and paste the SQL commands above")
        print("5. Execute each SQL command to create the tables")
        print("\n6. Enable Row Level Security (RLS) for production:")
        print("   - Go to Authentication > Policies")
        print("   - Set up appropriate policies for your application")
        print("\n" + "=" * 77)
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    create_tables()
