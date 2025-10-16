"""
Database Viewer - Visualize all data in a clean format
"""

from app import app, db, Market, get_market_db_path
from sqlalchemy import create_engine, text
import os

def view_all_data():
    print("\n" + "=" * 77)
    print(" APPPRECOS DATABASE VIEWER")
    print("=" * 77)
    
    with app.app_context():
        # View main database
        print("\n[MAIN DATABASE: markets_main.db]")
        print("-" * 77)
        
        markets = Market.query.all()
        print(f"\nTotal Markets: {len(markets)}\n")
        
        if not markets:
            print("  (No markets found)")
        else:
            for i, market in enumerate(markets, 1):
                print(f"{i}. Market ID: {market.market_id}")
                print(f"   Name: {market.name}")
                print(f"   Address: {market.address}")
                print(f"   Created: {market.created_at}")
                print()
        
        # View each market's databases
        for market in markets:
            market_id = market.market_id
            
            print("\n" + "=" * 77)
            print(f" MARKET: {market.name}")
            print(f" Market ID: {market_id}")
            print("=" * 77)
            
            # View main database
            print(f"\n[DATABASE: {market_id}.db - Complete History]")
            print("-" * 77)
            
            db_path = get_market_db_path(market_id)
            if os.path.exists(db_path):
                engine = create_engine(f'sqlite:///{db_path}')
                
                with engine.connect() as conn:
                    # Count
                    result = conn.execute(text("SELECT COUNT(*) FROM products"))
                    count = result.fetchone()[0]
                    print(f"\nTotal Products (History): {count}\n")
                    
                    # Show all products
                    result = conn.execute(text("""
                        SELECT id, ncm, quantity, unidade_comercial, price, purchase_date 
                        FROM products 
                        ORDER BY id
                    """))
                    rows = result.fetchall()
                    
                    if rows:
                        print(f"{'ID':<5} {'NCM':<10} {'Quantity':<10} {'Unit':<6} {'Price':<10} {'Purchase Date':<20}")
                        print("-" * 77)
                        for row in rows:
                            print(f"{row[0]:<5} {row[1]:<10} {row[2]:<10.4f} {row[3]:<6} R$ {row[4]:<7.2f} {str(row[5]):<20}")
                    else:
                        print("  (No products)")
            else:
                print(f"  [ERROR] Database file not found")
            
            # View unique database
            print(f"\n[DATABASE: {market_id}_unique.db - Latest Prices Only]")
            print("-" * 77)
            
            unique_db_path = db_path.replace('.db', '_unique.db')
            if os.path.exists(unique_db_path):
                engine_unique = create_engine(f'sqlite:///{unique_db_path}')
                
                with engine_unique.connect() as conn:
                    # Count
                    result = conn.execute(text("SELECT COUNT(*) FROM products"))
                    count_unique = result.fetchone()[0]
                    print(f"\nTotal Unique NCMs: {count_unique}\n")
                    
                    # Show all unique products
                    result = conn.execute(text("""
                        SELECT id, ncm, quantity, unidade_comercial, price, purchase_date 
                        FROM products 
                        ORDER BY ncm
                    """))
                    rows = result.fetchall()
                    
                    if rows:
                        print(f"{'ID':<5} {'NCM':<10} {'Quantity':<10} {'Unit':<6} {'Price':<10} {'Last Updated':<20}")
                        print("-" * 77)
                        for row in rows:
                            print(f"{row[0]:<5} {row[1]:<10} {row[2]:<10.4f} {row[3]:<6} R$ {row[4]:<7.2f} {str(row[5]):<20}")
                    else:
                        print("  (No unique products)")
            else:
                print(f"  [ERROR] Unique database file not found")
        
        # Summary
        print("\n" + "=" * 77)
        print(" SUMMARY")
        print("=" * 77)
        print(f"\nTotal Markets: {len(markets)}")
        
        total_products = 0
        total_unique = 0
        
        for market in markets:
            db_path = get_market_db_path(market.market_id)
            
            if os.path.exists(db_path):
                engine = create_engine(f'sqlite:///{db_path}')
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM products"))
                    total_products += result.fetchone()[0]
            
            unique_db_path = db_path.replace('.db', '_unique.db')
            if os.path.exists(unique_db_path):
                engine = create_engine(f'sqlite:///{unique_db_path}')
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM products"))
                    total_unique += result.fetchone()[0]
        
        print(f"Total Products (All History): {total_products}")
        print(f"Total Unique NCMs (All Markets): {total_unique}")
        
        print("\n" + "=" * 77)


if __name__ == "__main__":
    view_all_data()

