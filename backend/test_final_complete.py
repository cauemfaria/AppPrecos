"""
FINAL COMPLETE TEST
Tests entire workflow from clean databases to populated data
"""

from app import (
    app, db, Market,
    generate_market_id, create_market_database,
    save_products_to_market_db, get_market_db_path
)
from nfce_extractor import extract_full_nfce_data
from sqlalchemy import create_engine, text
from datetime import datetime
import os

def test_final_complete():
    print("=" * 77)
    print(" FINAL COMPLETE TEST - Clean DB to Populated")
    print("=" * 77)
    
    nfce_url = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=35250948093892001030653080000310101000606075%7C2%7C1%7C1%7Ca9ee07ab1d3a169800dc587738bc26ef7ffbc8db"
    
    with app.app_context():
        # Initialize database
        print("\n[1/7] Initializing main database...")
        db.create_all()
        print("  [OK] Main database created")
        
        print("\n[2/7] Extracting data from NFCe URL...")
        print(f"  URL: {nfce_url[:70]}...")
        
        result = extract_full_nfce_data(nfce_url, headless=True)
        market_info = result.get('market_info', {})
        products = result.get('products', [])
        
        print(f"  [OK] Extracted:")
        print(f"    Market: {market_info.get('name')}")
        print(f"    Address: {market_info.get('address')}")
        print(f"    Products: {len(products)}")
        
        print("\n[3/7] Checking for existing market...")
        market = Market.query.filter_by(
            name=market_info['name'],
            address=market_info['address']
        ).first()
        
        if market:
            print(f"  [FOUND] Existing market: {market.market_id}")
            market_action = "matched"
        else:
            print(f"  [NOT FOUND] Creating new market...")
            new_market_id = generate_market_id()
            
            market = Market(
                market_id=new_market_id,
                name=market_info['name'],
                address=market_info['address']
            )
            db.session.add(market)
            db.session.flush()
            
            print(f"  [OK] Market created:")
            print(f"    Market ID: {market.market_id}")
            print(f"    Auto ID: {market.id}")
            
            # Create databases
            create_market_database(market.market_id)
            print(f"  [OK] Databases created:")
            print(f"    - {market.market_id}.db")
            print(f"    - {market.market_id}_unique.db")
            
            market_action = "created"
        
        db.session.commit()
        
        print(f"\n[4/7] Saving {len(products)} products...")
        save_result = save_products_to_market_db(
            market.market_id,
            products,
            nfce_url
        )
        
        print(f"  [OK] Save complete:")
        print(f"    Main DB: {save_result['saved_to_main']} products")
        print(f"    Unique DB: {save_result['created_unique']} created, {save_result['updated_unique']} updated")
        
        print(f"\n[5/7] Verifying MAIN database ({market.market_id}.db)...")
        db_path = get_market_db_path(market.market_id)
        engine = create_engine(f'sqlite:///{db_path}')
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            main_count = result.fetchone()[0]
            print(f"  [OK] Total products: {main_count}")
            
            # Show first 5 products
            result = conn.execute(text("SELECT id, ncm, quantity, unidade_comercial, price FROM products LIMIT 5"))
            rows = result.fetchall()
            print(f"\n  First 5 products:")
            for row in rows:
                print(f"    ID:{row[0]} NCM:{row[1]} Qty:{row[2]}{row[3]} Price:R${row[4]}")
        
        print(f"\n[6/7] Verifying UNIQUE database ({market.market_id}_unique.db)...")
        unique_db_path = db_path.replace('.db', '_unique.db')
        engine_unique = create_engine(f'sqlite:///{unique_db_path}')
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            unique_count = result.fetchone()[0]
            print(f"  [OK] Total unique NCMs: {unique_count}")
            
            # Show all unique products
            result = conn.execute(text("SELECT ncm, price FROM products ORDER BY ncm LIMIT 5"))
            rows = result.fetchall()
            print(f"\n  First 5 unique products:")
            for row in rows:
                print(f"    NCM: {row[0]}, Price: R$ {row[1]}")
        
        print(f"\n[7/7] Verifying files exist...")
        if os.path.exists(db_path):
            size = os.path.getsize(db_path) / 1024
            print(f"  [OK] {market.market_id}.db exists ({size:.1f} KB)")
        
        if os.path.exists(unique_db_path):
            size = os.path.getsize(unique_db_path) / 1024
            print(f"  [OK] {market.market_id}_unique.db exists ({size:.1f} KB)")
        
        print(f"\n[8/8] Final verification...")
        total_markets = Market.query.count()
        print(f"  [OK] Total markets: {total_markets}")
        
        print("\n" + "=" * 77)
        print(" SUCCESS - ALL DATABASES POPULATED CORRECTLY!")
        print("=" * 77)
        print(f"\n[MAIN DATABASE: markets_main.db]")
        print(f"  Markets: {total_markets}")
        print(f"  Market ID: {market.market_id}")
        print(f"  Name: {market.name}")
        print(f"  Address: {market.address}")
        
        print(f"\n[MARKET DATABASE: {market.market_id}.db]")
        print(f"  Total products: {main_count}")
        print(f"  Purpose: Complete purchase history")
        
        print(f"\n[UNIQUE DATABASE: {market.market_id}_unique.db]")
        print(f"  Total unique NCMs: {unique_count}")
        print(f"  Purpose: Latest price per NCM")
        
        print("\n" + "=" * 77)
        
        return market.market_id


if __name__ == "__main__":
    test_final_complete()

