"""
TEST SCRIPT: Extract Market Information from NFCe
Tests extraction of: Nome/Razão Social, Endereço, and CEP
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
import re
import time

def test_extract_market_info(url, headless=False):
    """Test market info extraction"""
    
    print("=" * 77)
    print(" TEST: Market Information Extraction")
    print("=" * 77)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        
        try:
            # Step 1: Load page
            print("\n[1/2] Loading NFCe page...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            print("  [OK] Page loaded")
            
            # Step 2: Click "Visualizar em Abas"
            print("\n[2/2] Clicking 'Visualizar em Abas'...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            page.click('#btnVisualizarAbas', timeout=10000)
            time.sleep(4)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            print("  [OK] Tabs view activated")
            
            # Step 3: Get HTML content
            print("\n[3/3] Extracting market information...")
            html = page.content()
            
            # Helper function to clean extracted text
            def clean_text(text):
                """Remove HTML entities and normalize whitespace"""
                if not text:
                    return ""
                # Remove HTML entities
                text = text.replace('&nbsp;', ' ')
                text = text.replace('&amp;', '&')
                text = text.replace('&lt;', '<')
                text = text.replace('&gt;', '>')
                # Normalize whitespace (multiple spaces/newlines to single space)
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
            
            # Extract Nome / Razão Social
            nome_pattern = r'<label>Nome / Razão Social</label>\s*<span>([^<]+)</span>'
            nome_match = re.search(nome_pattern, html)
            nome = clean_text(nome_match.group(1)) if nome_match else "NOT FOUND"
            
            # Extract Endereço
            endereco_pattern = r'<label>Endereço</label>\s*<span>([^<]+)</span>'
            endereco_match = re.search(endereco_pattern, html)
            endereco = clean_text(endereco_match.group(1)) if endereco_match else "NOT FOUND"
            
            # Extract CEP
            cep_pattern = r'<label>CEP</label>\s*<span>([^<]+)</span>'
            cep_match = re.search(cep_pattern, html)
            cep = clean_text(cep_match.group(1)) if cep_match else "NOT FOUND"
            
            # BONUS: Also extract CNPJ for verification
            cnpj_pattern = r'<label>CNPJ</label>\s*<span>([^<]+)</span>'
            cnpj_match = re.search(cnpj_pattern, html)
            cnpj = clean_text(cnpj_match.group(1)) if cnpj_match else "NOT FOUND"
            
            # BONUS: Extract Bairro and Município for complete address
            bairro_pattern = r'<label>Bairro / Distrito</label>\s*<span>([^<]+)</span>'
            bairro_match = re.search(bairro_pattern, html)
            bairro = clean_text(bairro_match.group(1)) if bairro_match else ""
            
            municipio_pattern = r'<label>Município</label>\s*<span>[^\-]*-\s*([^<]+)</span>'
            municipio_match = re.search(municipio_pattern, html)
            municipio = clean_text(municipio_match.group(1)) if municipio_match else ""
            
            uf_pattern = r'<label>UF</label>\s*<span>([^<]+)</span>'
            uf_match = re.search(uf_pattern, html)
            uf = clean_text(uf_match.group(1)) if uf_match else ""
            
            # Print Results
            print("\n" + "=" * 77)
            print(" EXTRACTION RESULTS")
            print("=" * 77)
            
            print(f"\n[REQUIRED FIELDS]")
            print(f"  Nome / Razão Social: {nome}")
            print(f"  Endereço:            {endereco}")
            print(f"  CEP:                 {cep}")
            
            print(f"\n[BONUS FIELDS]")
            print(f"  CNPJ:                {cnpj}")
            print(f"  Bairro:              {bairro}")
            print(f"  Município:           {municipio}")
            print(f"  UF:                  {uf}")
            
            # Build complete address
            print(f"\n[COMPLETE ADDRESS]")
            full_address = f"{endereco}, {bairro}, {municipio} - {uf}, CEP: {cep}"
            print(f"  {full_address}")
            
            print("\n" + "=" * 77)
            print(" TEST COMPLETE")
            print("=" * 77)
            
            # Return data for verification
            return {
                'nome': nome,
                'endereco': endereco,
                'cep': cep,
                'cnpj': cnpj,
                'bairro': bairro,
                'municipio': municipio,
                'uf': uf,
                'full_address': full_address
            }
            
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
    
    print("\nTesting Market Info Extraction...")
    print("This will extract: Nome, Endereço, and CEP")
    print("-" * 77)
    
    result = test_extract_market_info(test_url, headless=False)
    
    if result:
        print("\n✅ Extraction successful!")
        print("\nYou can verify these values match the NFCe receipt.")
        print("If correct, we'll implement this in the main extractor.")
    else:
        print("\n❌ Extraction failed - check errors above")

