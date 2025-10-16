"""
NFCe Extractor Module
Standalone function to extract NCM codes from NFCe URLs
Can be imported by Flask API
"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
import re
import time

def extract_ncm_from_url(url, headless=True):
    """
    Extract NCM codes from NFCe URL
    
    Args:
        url: NFCe URL from QR code
        headless: Run browser in headless mode (default True)
    
    Returns:
        List of dictionaries with product data:
        [
            {
                'number': 1,
                'product': 'ABOBORA PESCOCO KG',
                'ncm': '07099300'
            },
            ...
        ]
    """
    
    ncm_data = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            try:
                # Load page
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(2)
                
                # Click "Visualizar em Abas" using exact ID
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                page.click('#btnVisualizarAbas', timeout=10000)
                time.sleep(4)
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # Extract from HTML (all data now loaded)
                html = page.content()
                
                # Find all NCM codes
                ncm_matches = re.findall(r'Código NCM</label>\s*<span>(\d{8})</span>', html)
                
                # Find all product names
                product_matches = re.findall(
                    r'<table class="toggle box">.*?'
                    r'class="fixo-prod-serv-descricao">\s*<span>([^<]+)</span>',
                    html,
                    re.DOTALL
                )
                
                # Combine products with NCM codes
                for i, (product, ncm) in enumerate(zip(product_matches, ncm_matches), 1):
                    ncm_data.append({
                        'number': i,
                        'product': product.strip(),
                        'ncm': ncm
                    })
                
            finally:
                browser.close()
        
        return ncm_data
        
    except Exception as e:
        print(f"Error extracting NCM codes: {e}")
        return []


def extract_full_nfce_data(url, headless=True):
    """
    Extract complete NFCe data including prices and quantities
    
    Returns:
        List of dictionaries with complete product data
    """
    
    products = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            try:
                # Load and navigate
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(2)
                
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                page.click('#btnVisualizarAbas', timeout=10000)
                time.sleep(4)
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # Get HTML
                html = page.content()
                
                # Extract all data using regex patterns
                # Pattern for NCM codes
                ncm_pattern = r'Código NCM</label>\s*<span>(\d{8})</span>'
                ncm_codes = re.findall(ncm_pattern, html)
                
                # Pattern for product names
                product_pattern = r'class="fixo-prod-serv-descricao">\s*<span>([^<]+)</span>'
                product_names = re.findall(product_pattern, html)
                
                # Pattern for quantities
                quantity_pattern = r'class="fixo-prod-serv-qtd">\s*<span>([^<]+)</span>'
                quantities = re.findall(quantity_pattern, html)
                
                # Pattern for commercial units
                unit_pattern = r'class="fixo-prod-serv-uc">\s*<span>([^<]+)</span>'
                units = re.findall(unit_pattern, html)
                
                # Pattern for prices
                price_pattern = r'class="fixo-prod-serv-vb">\s*<span>([^<]+)</span>'
                prices = re.findall(price_pattern, html)
                
                # Combine all data
                for i in range(len(ncm_codes)):
                    try:
                        # Convert Brazilian number format to float
                        quantity = float(quantities[i].replace(',', '.')) if i < len(quantities) else 0
                        price = float(prices[i].replace(',', '.')) if i < len(prices) else 0
                        
                        products.append({
                            'number': i + 1,
                            'product': product_names[i].strip() if i < len(product_names) else '',
                            'ncm': ncm_codes[i],
                            'quantity': quantity,
                            'unidade_comercial': units[i].strip() if i < len(units) else 'UN',
                            'price': price
                        })
                    except Exception as e:
                        print(f"Error processing product {i+1}: {e}")
                        continue
                
            finally:
                browser.close()
        
        return products
        
    except Exception as e:
        print(f"Error extracting full NFCe data: {e}")
        return []


# For testing
if __name__ == "__main__":
    test_url = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=35250948093892001030653080000310101000606075%7C2%7C1%7C1%7Ca9ee07ab1d3a169800dc587738bc26ef7ffbc8db"
    
    print("Testing full data extraction...")
    products = extract_full_nfce_data(test_url, headless=False)
    
    if products:
        print(f"\n✓ Extracted {len(products)} products:")
        for p in products[:5]:
            print(f"  {p['number']}. {p['product']} - NCM: {p['ncm']} - {p['quantity']} {p['unidade_comercial']} - R$ {p['price']}")
        if len(products) > 5:
            print(f"  ... and {len(products) - 5} more")
    else:
        print("\n✗ No products extracted")

