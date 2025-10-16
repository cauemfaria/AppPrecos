"""
Clean all databases - Fresh start
"""

import os
import shutil
from app import app, db

def clean_all():
    print("=" * 77)
    print(" CLEANING ALL DATABASES")
    print("=" * 77)
    
    basedir = os.path.dirname(__file__)
    
    with app.app_context():
        # Drop main database
        print("\n[1/3] Dropping main database tables...")
        db.drop_all()
        print("  [OK] Tables dropped")
        
    # Delete main database file
    print("\n[2/3] Deleting database files...")
    files_to_delete = ['markets_main.db', 'appprecos.db']
    for file in files_to_delete:
        file_path = os.path.join(basedir, file)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"  [OK] Deleted {file}")
    
    # Delete market_databases folder
    market_db_dir = os.path.join(basedir, 'market_databases')
    if os.path.exists(market_db_dir):
        shutil.rmtree(market_db_dir)
        print(f"  [OK] Deleted market_databases/ folder")
    
    print("\n[3/3] Recreating main database...")
    with app.app_context():
        db.create_all()
        print("  [OK] Main database recreated")
    
    print("\n" + "=" * 77)
    print(" ALL DATABASES CLEANED!")
    print("=" * 77)
    print("\nFresh start - ready for testing\n")

if __name__ == "__main__":
    clean_all()

