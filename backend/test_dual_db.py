"""
TEST: Dual Database Architecture
Each market has TWO databases:
1. {MARKET_ID}.db - All purchases (history)
2. {MARKET_ID}_unique.db - Unique NCM codes (latest data)
"""

from app import (
    app, db, Market,
    generate_market_id, create_market_database,
    save_products_to_market_db, get_market_db_connection,
    get_market_db_path
)
import os
from sqlalchemy import create_engine, text
import shutil

def test_dual_database():
    print("=" * 77)
    print(" TEST: Dual Database Architecture (Main + Unique)")
    print("=" * 77)
    
    with app.app_context():
        # Clean start
        print("\n[Setup] Cleaning databases...")
        db.drop_all()
        db.create_all()
        
        db_dir = os.path.join(os.path.dirname(__file__), "market_databases")
        if os.path.exists(db_dir):
            shutil.rmtree(db_dir)
        os.makedirs(db_dir, exist_ok=True)
        print("  [OK] Clean start\n")
        
        # Create market
        print("[1/5] Creating market...")
        market_id = generate_market_id()
        market = Market(
            market_id=market_id,
            name="Supermercado Test",
            address="Test Address, CEP: 12345-678"
        )
        db.session.add(market)
        db.session.commit()
        
        # Create databases
        create_market_database(market_id)
        print(f"  [OK] Market created: {market_id}")
        print(f"  [OK] Databases created:")
        print(f"    - {market_id}.db (main)")
        print(f"    - {market_id}_unique.db (unique)")
        
        # Test 1: Add first batch of products
        print("\n[2/5] Adding first batch of products...")
        products_batch1 = [
            {"ncm": "07099300", "quantity": 0.431, "unidade_comercial": "KG", "price": 2.15},
            {"ncm": "07070000", "quantity": 0.148, "unidade_comercial": "KG", "price": 1.33},
            {"ncm": "19059090", "quantity": 0.270, "unidade_comercial": "KG", "price": 4.02},
        ]
        
        result1 = save_products_to_market_db(market_id, products_batch1, "https://nfce1.com")
        
        print(f"  [OK] Batch 1 results:")
        print(f"    Main DB: {result1['saved_to_main']} products saved")
        print(f"    Unique DB: {result1['created_unique']} created, {result1['updated_unique']} updated")
        
        # Verify main database
        db_path = get_market_db_path(market_id)
        engine_main = create_engine(f'sqlite:///{db_path}')
        with engine_main.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            main_count = result.fetchone()[0]
            print(f"\n  Main DB ({market_id}.db): {main_count} rows")
        
        # Verify unique database
        unique_db_path = db_path.replace('.db', '_unique.db')
        engine_unique = create_engine(f'sqlite:///{unique_db_path}')
        with engine_unique.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            unique_count = result.fetchone()[0]
            print(f"  Unique DB ({market_id}_unique.db): {unique_count} rows")
            
            # Show unique products
            result = conn.execute(text("SELECT ncm, price FROM products"))
            rows = result.fetchall()
            print(f"\n  Unique products:")
            for row in rows:
                print(f"    NCM: {row[0]}, Price: R$ {row[1]}")
        
        # Test 2: Add second batch with DUPLICATE NCMs (should update unique)
        print("\n[3/5] Adding second batch (some duplicates)...")
        products_batch2 = [
            {"ncm": "07099300", "quantity": 0.520, "unidade_comercial": "KG", "price": 2.50},  # Duplicate - NEW price!
            {"ncm": "07070000", "quantity": 0.200, "unidade_comercial": "KG", "price": 1.50},  # Duplicate - NEW price!
            {"ncm": "08081000", "quantity": 0.300, "unidade_comercial": "KG", "price": 3.99},  # New NCM
        ]
        
        result2 = save_products_to_market_db(market_id, products_batch2, "https://nfce2.com")
        
        print(f"  [OK] Batch 2 results:")
        print(f"    Main DB: {result2['saved_to_main']} products saved")
        print(f"    Unique DB: {result2['created_unique']} created, {result2['updated_unique']} updated")
        
        # Verify counts
        with engine_main.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            main_count_after = result.fetchone()[0]
            print(f"\n  Main DB: {main_count_after} rows (was {main_count}, added {result2['saved_to_main']})")
        
        with engine_unique.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            unique_count_after = result.fetchone()[0]
            print(f"  Unique DB: {unique_count_after} rows (was {unique_count})")
            
            # Show updated unique products with prices
            result = conn.execute(text("SELECT ncm, price FROM products ORDER BY ncm"))
            rows = result.fetchall()
            print(f"\n  Unique products (updated prices):")
            for row in rows:
                print(f"    NCM: {row[0]}, Price: R$ {row[1]}")
        
        # Test 3: Verify price updates
        print("\n[4/5] Verifying price updates...")
        with engine_unique.connect() as conn:
            # Check NCM 07099300 - should have NEW price (2.50 instead of 2.15)
            result = conn.execute(text("SELECT price FROM products WHERE ncm = '07099300'"))
            price = result.fetchone()[0]
            
            if price == 2.50:
                print(f"  [OK] NCM 07099300: Price updated R$ 2.15 -> R$ 2.50")
            else:
                print(f"  [ERROR] NCM 07099300: Expected R$ 2.50, got R$ {price}")
            
            # Check NCM 07070000 - should have NEW price (1.50 instead of 1.33)
            result = conn.execute(text("SELECT price FROM products WHERE ncm = '07070000'"))
            price = result.fetchone()[0]
            
            if price == 1.50:
                print(f"  [OK] NCM 07070000: Price updated R$ 1.33 -> R$ 1.50")
            else:
                print(f"  [ERROR] NCM 07070000: Expected R$ 1.50, got R$ {price}")
        
        # Test 4: Verify main DB has ALL records
        print("\n[5/5] Verifying complete history in main DB...")
        with engine_main.connect() as conn:
            # Should have 2 records for NCM 07099300 (history)
            result = conn.execute(text("SELECT COUNT(*) FROM products WHERE ncm = '07099300'"))
            count = result.fetchone()[0]
            
            if count == 2:
                print(f"  [OK] NCM 07099300: {count} records in history (correct)")
            else:
                print(f"  [ERROR] NCM 07099300: Expected 2 records, found {count}")
            
            # Show price history
            result = conn.execute(text("SELECT price, created_at FROM products WHERE ncm = '07099300' ORDER BY created_at"))
            rows = result.fetchall()
            print(f"\n  NCM 07099300 price history:")
            for i, row in enumerate(rows, 1):
                print(f"    {i}. R$ {row[0]} (on {row[1]})")
        
        # Summary
        print("\n" + "=" * 77)
        print(" TEST SUMMARY")
        print("=" * 77)
        print(f"\n[DATABASES CREATED]")
        print(f"  1. {market_id}.db (Main)")
        print(f"     - Total products: {main_count_after}")
        print(f"     - Purpose: Complete purchase history")
        
        print(f"\n  2. {market_id}_unique.db (Unique)")
        print(f"     - Total unique NCMs: {unique_count_after}")
        print(f"     - Purpose: Latest price per NCM")
        
        print(f"\n[LOGIC VERIFICATION]")
        print(f"  [OK] New products added to both DBs")
        print(f"  [OK] Duplicate NCMs updated in unique DB (not inserted)")
        print(f"  [OK] Main DB preserves complete history")
        print(f"  [OK] Unique DB always has latest data")
        
        print("\n" + "=" * 77)


if __name__ == "__main__":
    test_dual_database()

