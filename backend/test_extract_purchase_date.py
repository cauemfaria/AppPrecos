"""
TEST SCRIPT: Extract Purchase Date from NFCe
Tests extraction of "Data de Emissão" with date and time
"""

from playwright.sync_api import sync_playwright
import re
import time
from datetime import datetime

def test_extract_purchase_date(url, headless=False):
    """Test purchase date extraction"""
    
    print("=" * 77)
    print(" TEST: Purchase Date Extraction")
    print("=" * 77)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        try:
            # Load page and click button
            print("\n[1/2] Loading NFCe and activating tabs...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            page.click('#btnVisualizarAbas', timeout=10000)
            time.sleep(4)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            print("  [OK] Page ready")
            
            # Extract date
            print("\n[2/2] Extracting purchase date...")
            html = page.content()
            
            # Pattern for "Data de Emissão"
            date_pattern = r'<label>Data de Emissão</label>\s*<span>([^<]+)</span>'
            date_match = re.search(date_pattern, html)
            
            if date_match:
                raw_date = date_match.group(1).strip()
                print(f"  [OK] Found raw date: {raw_date}")
                
                # Clean the date string
                # Format: "20/09/2025 19:44:53-03:00"
                # Remove timezone part for simplicity
                date_clean = raw_date.split('-')[0].strip()  # "20/09/2025 19:44:53"
                
                print(f"  [OK] Cleaned date: {date_clean}")
                
                # Convert to datetime object
                try:
                    purchase_datetime = datetime.strptime(date_clean, '%d/%m/%Y %H:%M:%S')
                    print(f"  [OK] Parsed datetime: {purchase_datetime}")
                    print(f"  [OK] ISO format: {purchase_datetime.isoformat()}")
                    
                    # Show components
                    print(f"\n  Components:")
                    print(f"    Date: {purchase_datetime.strftime('%d/%m/%Y')}")
                    print(f"    Time: {purchase_datetime.strftime('%H:%M:%S')}")
                    print(f"    Day: {purchase_datetime.day}")
                    print(f"    Month: {purchase_datetime.month}")
                    print(f"    Year: {purchase_datetime.year}")
                    print(f"    Hour: {purchase_datetime.hour}")
                    print(f"    Minute: {purchase_datetime.minute}")
                    print(f"    Second: {purchase_datetime.second}")
                    
                    # For database storage
                    print(f"\n  For Database:")
                    print(f"    SQLite format: {purchase_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"    Python datetime: {purchase_datetime}")
                    
                    print("\n" + "=" * 77)
                    print(" SUCCESS!")
                    print("=" * 77)
                    print(f"\nExtracted Purchase Date:")
                    print(f"  Raw:      {raw_date}")
                    print(f"  Cleaned:  {date_clean}")
                    print(f"  Parsed:   {purchase_datetime}")
                    print(f"  Database: {purchase_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    return purchase_datetime
                    
                except ValueError as e:
                    print(f"  [ERROR] Could not parse date: {e}")
                    return None
            else:
                print(f"  [ERROR] Date not found in HTML")
                return None
                
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            print("\n[Cleanup] Closing browser...")
            browser.close()
            print("[OK] Done\n")


if __name__ == "__main__":
    # Sample NFCe URL
    test_url = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=35250948093892001030653080000310101000606075%7C2%7C1%7C1%7Ca9ee07ab1d3a169800dc587738bc26ef7ffbc8db"
    
    print("\nTesting Purchase Date Extraction...")
    print("Expected: 20/09/2025 19:44:53")
    print("-" * 77)
    
    result = test_extract_purchase_date(test_url, headless=True)
    
    if result:
        print("\n✅ Extraction successful!")
        print(f"\nPurchase Date: {result}")
        print("\nIf this matches the NFCe receipt, say 'good' to implement!")
    else:
        print("\n❌ Extraction failed")

