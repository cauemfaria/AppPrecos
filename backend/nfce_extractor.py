"""
NFCe Extractor Module
Extracts product data from NFCe URLs using Playwright
"""

import sys
import io

# Only set encoding when running as standalone script
if sys.platform == 'win32' and __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
import re
import time


def extract_market_info(html):
    """
    Extract market information from NFCe HTML
    
    Returns:
        dict with: name, endereco, cep, address (combined)
    """
    
    def clean_text(text):
        if not text:
            return ""
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    market_info = {}
    
    # Extract Nome / Razão Social
    nome_pattern = r'<label>Nome / Razão Social</label>\s*<span>([^<]+)</span>'
    nome_match = re.search(nome_pattern, html)
    market_info['name'] = clean_text(nome_match.group(1)) if nome_match else ""
    
    # Extract Endereço
    endereco_pattern = r'<label>Endereço</label>\s*<span>([^<]+)</span>'
    endereco_match = re.search(endereco_pattern, html)
    endereco = clean_text(endereco_match.group(1)) if endereco_match else ""
    
    # Extract CEP
    cep_pattern = r'<label>CEP</label>\s*<span>([^<]+)</span>'
    cep_match = re.search(cep_pattern, html)
    cep = clean_text(cep_match.group(1)) if cep_match else ""
    
    # Combine Endereço + CEP as address
    market_info['endereco'] = endereco
    market_info['cep'] = cep
    market_info['address'] = f"{endereco}, CEP: {cep}" if endereco and cep else endereco
    
    return market_info


def extract_full_nfce_data(url, headless=True):
    """
    Extract complete NFCe data including market info and products
    
    Returns:
        Dictionary with:
        {
            'market_info': {'name': '...', 'address': '...', 'cep': '...'},
            'products': [{'ncm': '...', 'quantity': ..., ...}, ...]
        }
    """
    
    result = {
        'market_info': {},
        'products': []
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            try:
                # Load and navigate
                page.goto(url, wait_until="load", timeout=60000)
                time.sleep(4)
                
                # Scroll to make button visible
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Wait for button and click
                page.wait_for_selector('#btnVisualizarAbas', state='attached', timeout=20000)
                page.evaluate("document.getElementById('btnVisualizarAbas').click()")
                time.sleep(6)
                page.wait_for_load_state("load", timeout=60000)
                time.sleep(3)
                
                # Get HTML
                html = page.content()
                
                # Extract market information
                result['market_info'] = extract_market_info(html)
                
                # Extract all product data using regex patterns
                ncm_pattern = r'Código NCM</label>\s*<span>(\d{8})</span>'
                ncm_codes = re.findall(ncm_pattern, html)
                
                ean_pattern = r'<label>Código EAN Comercial</label>\s*<span>([^<]+)</span>'
                ean_codes = re.findall(ean_pattern, html)
                
                product_pattern = r'class="fixo-prod-serv-descricao">\s*<span>([^<]+)</span>'
                product_names = re.findall(product_pattern, html)
                
                quantity_pattern = r'class="fixo-prod-serv-qtd">\s*<span>([^<]+)</span>'
                quantities = re.findall(quantity_pattern, html)
                
                unit_pattern = r'class="fixo-prod-serv-uc">\s*<span>([^<]+)</span>'
                units = re.findall(unit_pattern, html)
                
                total_price_pattern = r'class="fixo-prod-serv-vb">\s*<span>([^<]+)</span>'
                total_prices = re.findall(total_price_pattern, html)
                
                unit_price_pattern = r'<label>Valor unitário de comercialização</label>\s*<span>([^<]+)</span>'
                unit_prices = re.findall(unit_price_pattern, html)
                
                # Combine all data
                for i in range(len(ncm_codes)):
                    try:
                        quantity = float(quantities[i].replace(',', '.')) if i < len(quantities) else 0
                        total_price = float(total_prices[i].replace(',', '.')) if i < len(total_prices) else 0
                        unit_price = float(unit_prices[i].replace(',', '.')) if i < len(unit_prices) else 0
                        unit = units[i].strip() if i < len(units) else 'UN'
                        ean = ean_codes[i].strip() if i < len(ean_codes) else 'SEM GTIN'
                        
                        result['products'].append({
                            'number': i + 1,
                            'product': product_names[i].strip() if i < len(product_names) else '',
                            'ncm': ncm_codes[i],
                            'ean': ean,
                            'quantity': quantity,
                            'unidade_comercial': unit,
                            'total_price': total_price,
                            'unit_price': unit_price,
                            'price': unit_price
                        })
                    except Exception as e:
                        print(f"Error processing product {i+1}: {e}")
                        continue
                
            finally:
                browser.close()
        
        return result
        
    except Exception as e:
        print(f"Error extracting NFCe data: {e}")
        return {'market_info': {}, 'products': []}


# For testing
if __name__ == "__main__":
    test_url = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=35250948093892001030653080000310101000606075%7C2%7C1%7C1%7Ca9ee07ab1d3a169800dc587738bc26ef7ffbc8db"
    
    print("Testing NFCe extraction...")
    result = extract_full_nfce_data(test_url, headless=False)
    
    market_info = result.get('market_info', {})
    products = result.get('products', [])
    
    if market_info:
        print(f"\n✓ Market: {market_info.get('name', 'N/A')}")
        print(f"  Address: {market_info.get('address', 'N/A')}")
    
    if products:
        print(f"\n✓ Extracted {len(products)} products:")
        for p in products[:5]:
            print(f"  {p['number']}. {p['product']} - NCM: {p['ncm']} - R$ {p['price']}")
        if len(products) > 5:
            print(f"  ... and {len(products) - 5} more")
    else:
        print("\n✗ No products extracted")
