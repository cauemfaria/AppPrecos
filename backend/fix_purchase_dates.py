"""
One-time script to fix purchase_date in both `purchases` and `unique_products`.

For each unique nfce_url in purchases:
  1. Load the NFCe page with Playwright
  2. Extract the "Data de Emissão" (real purchase date)
  3. Update all purchases rows with that URL
  4. After all purchases are fixed, recalculate unique_products.purchase_date
     using the most recent purchase_date per (market_id, ean)
"""
import os
import sys
import re
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Clear Render's Playwright path if it doesn't exist locally
pw_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '')
if pw_path and not os.path.exists(pw_path):
    del os.environ['PLAYWRIGHT_BROWSERS_PATH']

from supabase import create_client
from playwright.sync_api import sync_playwright

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def extract_emission_date(page, url):
    """Load an NFCe page and extract just the emission date. Returns ISO string or None."""
    try:
        page.goto(url, wait_until="load", timeout=60000)
        time.sleep(5)

        html = page.content()

        # Pattern 1: Initial page format — "Emissão: </strong>DD/MM/YYYY HH:MM:SS"
        p1 = r'Emiss[aã]o:\s*</strong>\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})'
        m1 = re.search(p1, html)
        if m1:
            raw = m1.group(1).strip()
            try:
                dt = datetime.strptime(raw, "%d/%m/%Y %H:%M:%S")
                return dt.isoformat()
            except Exception:
                pass

        # Pattern 2: After-click format — "<label>Data de Emissão</label><span>...</span>"
        p2 = r'<label>Data de Emiss[aã]o</label>\s*<span>([^<]+)</span>'
        m2 = re.search(p2, html)
        if m2:
            raw = m2.group(1).strip()
            try:
                dt = datetime.strptime(raw, "%d/%m/%Y %H:%M:%S%z")
                return dt.isoformat()
            except Exception:
                pass
            try:
                dt = datetime.strptime(raw, "%d/%m/%Y %H:%M:%S")
                return dt.isoformat()
            except Exception:
                pass

        # Pattern 3: Generic — find any DD/MM/YYYY HH:MM:SS near "Emissão"
        p3 = r'Emiss[aã]o.*?(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})'
        m3 = re.search(p3, html, re.DOTALL)
        if m3:
            raw = m3.group(1).strip()
            try:
                dt = datetime.strptime(raw, "%d/%m/%Y %H:%M:%S")
                return dt.isoformat()
            except Exception:
                pass

        print(f"  [WARN] No date pattern found in HTML")
        return None
    except Exception as e:
        print(f"  [ERR] Failed to load {url[:60]}...: {e}")
        return None


def main():
    # ── Step 1: Get all unique NFCe URLs from purchases ─────────────────
    print("=" * 60)
    print(" Fix Purchase Dates — One-Time Script")
    print("=" * 60)

    all_purchases = sb.table('purchases').select('id, nfce_url, purchase_date, market_id, ean').execute()
    purchases = all_purchases.data
    print(f"\nTotal purchase rows: {len(purchases)}")

    url_set = sorted(set(p['nfce_url'] for p in purchases if p.get('nfce_url')))
    print(f"Unique NFCe URLs to scrape: {len(url_set)}")

    # ── Step 2: Scrape emission dates with Playwright ───────────────────
    url_to_date = {}
    print("\nStarting Playwright...\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        for i, url in enumerate(url_set, 1):
            print(f"[{i}/{len(url_set)}] Scraping: {url[:80]}...")
            iso_date = extract_emission_date(page, url)
            if iso_date:
                url_to_date[url] = iso_date
                print(f"  -> Emission date: {iso_date}")
            else:
                print(f"  -> FAILED to extract date")

        browser.close()

    print(f"\nSuccessfully extracted dates for {len(url_to_date)}/{len(url_set)} URLs")

    if not url_to_date:
        print("No dates extracted. Aborting.")
        return

    # ── Step 3: Update purchases table ──────────────────────────────────
    print("\nUpdating purchases table...")
    updated_count = 0
    failed_count = 0

    for url, iso_date in url_to_date.items():
        try:
            result = sb.table('purchases').update({
                'purchase_date': iso_date
            }).eq('nfce_url', url).execute()
            count = len(result.data) if result.data else 0
            updated_count += count
            print(f"  Updated {count} rows for date {iso_date[:10]}")
        except Exception as e:
            print(f"  [ERR] Failed to update for {url[:60]}: {e}")
            failed_count += 1

    print(f"\nPurchases updated: {updated_count} rows, {failed_count} failures")

    # ── Step 4: Recalculate unique_products.purchase_date ───────────────
    # For each (market_id, ean) in unique_products, find the MAX purchase_date
    # from purchases and set it.
    print("\nUpdating unique_products.purchase_date...")

    all_unique = sb.table('unique_products').select('id, market_id, ean').execute()
    unique_products = all_unique.data
    print(f"Total unique_products to update: {len(unique_products)}")

    up_updated = 0
    up_skipped = 0

    for up in unique_products:
        market_id = up['market_id']
        ean = up['ean']

        # Find the most recent purchase_date for this market+ean
        matches = sb.table('purchases').select('purchase_date') \
            .eq('market_id', market_id) \
            .eq('ean', ean) \
            .order('purchase_date', desc=True) \
            .limit(1) \
            .execute()

        if matches.data and matches.data[0].get('purchase_date'):
            newest_date = matches.data[0]['purchase_date']
            try:
                sb.table('unique_products').update({
                    'purchase_date': newest_date
                }).eq('id', up['id']).execute()
                up_updated += 1
            except Exception as e:
                print(f"  [ERR] Failed to update unique_product {up['id']}: {e}")
        else:
            up_skipped += 1

    print(f"Unique products updated: {up_updated}, skipped (no match): {up_skipped}")

    # ── Step 5: Summary ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    print(f"  URLs scraped:            {len(url_to_date)}/{len(url_set)}")
    print(f"  Purchases updated:       {updated_count}")
    print(f"  Unique products updated: {up_updated}")
    print(f"  Unique products skipped: {up_skipped}")
    print("=" * 60)


if __name__ == "__main__":
    main()
