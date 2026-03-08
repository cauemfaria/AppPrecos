"""
Enrichment Worker Script
Processes pending items in the purchases table and performs product enrichment.
Handles Bluesoft Cosmos API token rotation and singleton execution via database lock.
"""

import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import enrichment logic from enrichment_service
from enrichment_service import (
    supabase, 
    get_product_from_cosmos, 
    search_product_on_cosmos,
    log_product_lookup,
    acquire_enrichment_lock,
    release_enrichment_lock
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def _parse_iso_date(s: str) -> datetime:
    """Parse an ISO-8601 timestamp string, stripping timezone info for comparison."""
    s = s.strip()
    if s.endswith('Z'):
        s = s[:-1]
    # Remove timezone offset so we can compare naive datetimes
    if '+' in s[10:]:
        s = s[:s.index('+', 10)]
    elif s[10:].count('-') > 0:
        # Find tz offset like -03:00 after the date portion
        tail = s[10:]
        dash_pos = tail.rfind('-')
        if dash_pos > 0:
            s = s[:10 + dash_pos]
    return datetime.fromisoformat(s)


# Configuration
BATCH_SIZE = 10
SLEEP_BETWEEN_BATCHES = 5

def process_pending_purchases(worker_id="manual"):
    """Main loop to process pending purchases AND scanned_prices until both queues are empty (One-Shot)"""
    
    logger.info(f"Worker {worker_id} attempting to acquire enrichment lock...")
    if not acquire_enrichment_lock(worker_id):
        logger.info(f"Enrichment already in progress or locked (ID: {worker_id}). Exiting after retries.")
        return

    logger.info(f"Lock acquired by {worker_id}. Starting Enrichment Worker...")
    
    try:
        # Phase 1: Process purchases (existing logic)
        _process_purchases_queue()

        # Phase 2: Process scanned_prices (worker barcode scans)
        _process_scanned_prices_queue()

    finally:
        release_enrichment_lock()


def _process_purchases_queue():
    """Process all pending purchases until the queue is empty."""
    logger.info("--- Phase 1: Processing purchases queue ---")
    while True:
        try:
            response = supabase.table('purchases').select('*').eq('enriched', False).limit(BATCH_SIZE).execute()
            pending_items = response.data
            
            if not pending_items:
                time.sleep(1)
                final_check = supabase.table('purchases').select('id').eq('enriched', False).limit(1).execute()
                if not final_check.data:
                    logger.info("Purchases queue is empty.")
                    break
                else:
                    continue
            
            logger.info(f"Processing batch of {len(pending_items)} purchase items...")
            
            for item in pending_items:
                status = enrich_single_purchase(item)
                
                if status == 'completed':
                    supabase.table('purchases').update({
                        'enriched': True,
                        'enrichment_status': 'completed',
                        'enrichment_error': None
                    }).eq('id', item['id']).execute()
                    logger.info(f"Successfully enriched purchase {item['id']}")
                elif status == 'rate_limited':
                    logger.error("!!! RATE LIMIT REACHED !!! Stopping purchases enrichment.")
                    return
                elif status in ['backlog', 'failed']:
                    error_msg = item.get('enrichment_error') or ('No GTIN found' if status == 'backlog' else 'Unexpected processing error')
                    
                    supabase.table('purchases').update({
                        'enriched': True,
                        'enrichment_status': status,
                        'enrichment_error': error_msg
                    }).eq('id', item['id']).execute()
                    
                    backlog_data = {
                        'purchase_id': item['id'],
                        'market_id': item['market_id'],
                        'original_product_name': item['product_name'],
                        'ncm': item['ncm'],
                        'ean': item['ean'],
                        'created_at': datetime.utcnow().isoformat()
                    }
                    supabase.table('product_backlog').insert(backlog_data).execute()
                    logger.info(f"Purchase {item['id']} moved to backlog (status: {status})")
            
            logger.info(f"Purchases batch done. Sleeping {SLEEP_BETWEEN_BATCHES}s...")
            time.sleep(SLEEP_BETWEEN_BATCHES)
            
        except Exception as e:
            logger.error(f"Error in purchases loop: {e}")
            time.sleep(30)


def _process_scanned_prices_queue():
    """Process all pending scanned_prices (worker barcode scans) until the queue is empty."""
    logger.info("--- Phase 2: Processing scanned_prices queue ---")
    while True:
        try:
            response = supabase.table('scanned_prices').select('*').eq('enriched', False).order('scanned_at').limit(BATCH_SIZE).execute()
            pending_items = response.data

            if not pending_items:
                time.sleep(1)
                final_check = supabase.table('scanned_prices').select('id').eq('enriched', False).limit(1).execute()
                if not final_check.data:
                    logger.info("Scanned prices queue is empty. All enrichment complete.")
                    break
                else:
                    continue

            logger.info(f"Processing batch of {len(pending_items)} scanned price items...")

            for item in pending_items:
                status = _enrich_single_scan(item)

                if status == 'rate_limited':
                    logger.error("!!! RATE LIMIT REACHED !!! Stopping scanned_prices enrichment.")
                    return

            logger.info(f"Scanned prices batch done. Sleeping {SLEEP_BETWEEN_BATCHES}s...")
            time.sleep(SLEEP_BETWEEN_BATCHES)

        except Exception as e:
            logger.error(f"Error in scanned_prices loop: {e}")
            time.sleep(30)


def _enrich_single_scan(item):
    """
    Enrich a single scanned_prices row via Cosmos API (GTIN lookup).
    Updates scanned_prices row and upserts into unique_products.
    Returns: 'completed', 'not_found', 'rate_limited', or 'failed'
    """
    scan_id = item['id']
    ean = item['ean']
    market_id = item['market_id']
    varejo_price = item.get('varejo_price')
    atacado_price = item.get('atacado_price')

    try:
        if not ean or len(ean) < 8:
            supabase.table('scanned_prices').update({
                'enriched': True,
                'enrichment_status': 'not_found',
                'enrichment_error': 'EAN inválido'
            }).eq('id', scan_id).execute()
            _upsert_unique_product_from_scan(item, None, None, None, None)
            return 'not_found'

        # Check local registry first
        local_match = supabase.table('unique_products').select('product_name, ncm, image_url').eq('ean', ean).limit(1).execute()
        if local_match.data:
            row = local_match.data[0]
            supabase.table('scanned_prices').update({
                'enriched': True,
                'enrichment_status': 'completed',
                'product_name': row['product_name'],
                'ncm': row.get('ncm'),
                'image_url': row.get('image_url'),
            }).eq('id', scan_id).execute()
            _upsert_unique_product_from_scan(item, row['product_name'], None, row.get('image_url'), row.get('ncm'))
            logger.info(f"Scan {scan_id}: enriched from local registry for EAN {ean}")
            return 'completed'

        # Call Cosmos API
        success, product_name, brand, image_url, time_ms, error = get_product_from_cosmos(ean)

        if error == "TOKENS_EXHAUSTED":
            return 'rate_limited'

        if success and product_name:
            supabase.table('scanned_prices').update({
                'enriched': True,
                'enrichment_status': 'completed',
                'product_name': product_name,
                'brand': brand,
                'image_url': image_url,
            }).eq('id', scan_id).execute()
            _upsert_unique_product_from_scan(item, product_name, brand, image_url, None)
            logger.info(f"Scan {scan_id}: enriched via Cosmos for EAN {ean} -> {product_name}")
            return 'completed'
        else:
            supabase.table('scanned_prices').update({
                'enriched': True,
                'enrichment_status': 'not_found',
                'enrichment_error': error or 'Produto não encontrado no Cosmos'
            }).eq('id', scan_id).execute()
            _upsert_unique_product_from_scan(item, None, None, None, None)
            logger.info(f"Scan {scan_id}: EAN {ean} not found in Cosmos")
            return 'not_found'

    except Exception as e:
        logger.error(f"Error enriching scan {scan_id}: {e}")
        try:
            supabase.table('scanned_prices').update({
                'enriched': True,
                'enrichment_status': 'failed',
                'enrichment_error': str(e)[:200]
            }).eq('id', scan_id).execute()
        except Exception:
            pass
        return 'failed'


def _upsert_unique_product_from_scan(item, product_name, brand, image_url, ncm):
    """Upsert a scanned product into unique_products using market_id + ean as the key."""
    market_id = item['market_id']
    ean = item['ean']
    varejo_price = item.get('varejo_price')
    atacado_price = item.get('atacado_price')

    unique_data = {
        'market_id': market_id,
        'ean': ean,
        'varejo_price': varejo_price,
        'purchase_date': item.get('scanned_at', datetime.utcnow().isoformat()),
    }
    if atacado_price:
        unique_data['atacado_price'] = atacado_price
    if product_name:
        unique_data['product_name'] = product_name
    if image_url:
        unique_data['image_url'] = image_url
    if ncm:
        unique_data['ncm'] = ncm

    try:
        existing = supabase.table('unique_products').select('id, price').match({
            'market_id': market_id,
            'ean': ean
        }).execute()

        if existing.data:
            update_data = {k: v for k, v in unique_data.items() if k != 'market_id' and v is not None}
            supabase.table('unique_products').update(update_data).eq('id', existing.data[0]['id']).execute()
            logger.info(f"Updated unique_product {existing.data[0]['id']} with scan data")
        else:
            unique_data.setdefault('product_name', f'EAN {ean}')
            unique_data.setdefault('ncm', '00000000')
            unique_data.setdefault('unidade_comercial', 'UN')
            unique_data['price'] = varejo_price
            unique_data['nfce_url'] = ''
            supabase.table('unique_products').insert(unique_data).execute()
            logger.info(f"Inserted new unique_product for EAN {ean} in market {market_id}")
    except Exception as e:
        logger.error(f"Failed to upsert unique_product for scan: {e}")

def enrich_single_purchase(item):
    """
    Perform enrichment for a single purchase item and upsert to unique_products
    Returns: status string ('completed', 'backlog', 'failed', 'rate_limited')
    """
    market_id = item['market_id']
    original_product_name = item['product_name']
    ncm = item['ncm']
    ean = item['ean']
    nfce_url = item['nfce_url']
    
    canonical_name = None
    source_used = None
    cosmos_result = None
    is_rate_limited = False
    
    try:
        # --- OPTIMIZATION: LOCAL DATABASE LOOKUP ---
        
        # 1. If we have a GTIN, check if we already enriched it in ANY market before
        if ean and ean != 'SEM GTIN' and len(ean) >= 8:
            # We look for the most recent enrichment for this GTIN
            local_match = supabase.table('unique_products').select('product_name, ncm').eq('ean', ean).limit(1).execute()
            if local_match.data:
                canonical_name = local_match.data[0]['product_name']
                if local_match.data[0].get('ncm'):
                    ncm = local_match.data[0]['ncm']
                source_used = "LOCAL_REGISTRY"
                logger.info(f"Reusing local registry data for GTIN {ean}: {canonical_name}")

        # 2. If it's a "SEM GTIN", check if we previously found a GTIN for this specific name/NCM
        if not canonical_name and ean == 'SEM GTIN':
            local_log = supabase.table('product_lookup_log').select('final_name, gtin').match({
                'original_name': original_product_name,
                'ncm': ncm,
                'success': True
            }).order('created_at', desc=True).limit(1).execute()
            
            if local_log.data and local_log.data[0].get('gtin'):
                canonical_name = local_log.data[0]['final_name']
                ean = local_log.data[0]['gtin']
                source_used = "LOCAL_LOG"
                logger.info(f"Reusing discovered GTIN {ean} from logs for '{original_product_name}'")

        # --- EXTERNAL API LOOKUP (Only if local lookup failed) ---
        
        # STEP 1: Bluesoft Cosmos (Direct GTIN lookup)
        if not canonical_name and ean and ean != 'SEM GTIN' and len(ean) >= 8:
            cosmos_success, cosmos_product_name, cosmos_brand, cosmos_image, cosmos_time, cosmos_error = get_product_from_cosmos(ean)
            
            cosmos_result = {
                'success': cosmos_success, 'product_name': cosmos_product_name,
                'brand': cosmos_brand, 'image_url': cosmos_image, 
                'time_ms': cosmos_time, 'error': cosmos_error
            }
            
            if cosmos_error == "TOKENS_EXHAUSTED":
                is_rate_limited = True
            
            if cosmos_success and cosmos_product_name:
                canonical_name = cosmos_product_name
                source_used = "COSMOS_BLUE"
        
        # STEP 2: Bluesoft Cosmos (Search by Name + NCM filter)
        if not canonical_name and not is_rate_limited:
            # Try searching by name since GTIN is missing or wasn't found
            search_success, search_name, search_gtin, search_brand, search_image, search_time, search_error = search_product_on_cosmos(
                query=original_product_name,
                ncm_filter=ncm
            )
            
            if search_error == "TOKENS_EXHAUSTED":
                is_rate_limited = True
            
            if search_success:
                canonical_name = search_name
                source_used = "COSMOS_SEARCH"
                ean = str(search_gtin) # Update EAN with the one found via search
                cosmos_result = {
                    'success': True, 'product_name': search_name,
                    'brand': search_brand, 'image_url': search_image,
                    'time_ms': search_time, 'error': None,
                    'search_used': True, 'found_gtin': search_gtin
                }
                logger.info(f"Found GTIN {search_gtin} via search for '{original_product_name}'")
            else:
                # Log the search attempt failure if it wasn't a rate limit
                if not is_rate_limited:
                    cosmos_result = {
                        'success': False, 'product_name': None,
                        'brand': None, 'image_url': None,
                        'time_ms': search_time, 'error': search_error,
                        'search_used': True
                    }

        if is_rate_limited:
            return 'rate_limited'
        
        # Log lookup
        log_product_lookup(
            nfce_url=nfce_url, market_id=market_id, gtin=ean, ncm=ncm,
            original_name=original_product_name, final_name=canonical_name,
            cosmos_result=cosmos_result,
            source_used=source_used, success=canonical_name is not None
        )
        
        # STEP 3: Handle Fallback to Backlog
        if not canonical_name:
            logger.info(f"No GTIN found for '{original_product_name}'. Moving to backlog.")
            return 'backlog'
            
        # STEP 4: Deterministic Upsert to unique_products (Market + GTIN)
        # Use the real purchase_date from the receipt instead of server processing time
        item_purchase_date = item.get('purchase_date')
        if isinstance(item_purchase_date, str):
            item_purchase_date_iso = item_purchase_date
        elif item_purchase_date:
            item_purchase_date_iso = item_purchase_date.isoformat()
        else:
            item_purchase_date_iso = datetime.utcnow().isoformat()

        unique_data = {
            'market_id': market_id,
            'ncm': ncm,
            'ean': ean,
            'product_name': canonical_name,
            'unidade_comercial': item.get('unidade_comercial', 'UN'),
            'price': item.get('unit_price', 0),
            'nfce_url': nfce_url,
            'purchase_date': item_purchase_date_iso,
        }
        
        if cosmos_result and cosmos_result.get('image_url'):
            unique_data['image_url'] = cosmos_result['image_url']
        
        existing = supabase.table('unique_products').select('id, purchase_date').match({
            'market_id': market_id,
            'ean': ean
        }).execute()
        
        if existing.data:
            existing_purchase_date = existing.data[0].get('purchase_date')
            should_update = True

            if existing_purchase_date and item_purchase_date_iso:
                try:
                    existing_dt = _parse_iso_date(existing_purchase_date)
                    new_dt = _parse_iso_date(item_purchase_date_iso)
                    should_update = new_dt >= existing_dt
                except Exception as cmp_err:
                    logger.warning(f"Could not compare dates, updating anyway: {cmp_err}")

            if should_update:
                try:
                    supabase.table('unique_products').update(unique_data).eq('id', existing.data[0]['id']).execute()
                except Exception as e:
                    if 'image_url' in unique_data:
                        del unique_data['image_url']
                        supabase.table('unique_products').update(unique_data).eq('id', existing.data[0]['id']).execute()
                    else:
                        raise e
                logger.info(f"Updated product {existing.data[0]['id']} in market {market_id} (purchase_date: {item_purchase_date_iso})")
            else:
                logger.info(f"Skipped product {existing.data[0]['id']} — existing record has a newer purchase_date ({existing_purchase_date})")
        else:
            try:
                supabase.table('unique_products').insert(unique_data).execute()
            except Exception as e:
                if 'image_url' in unique_data:
                    del unique_data['image_url']
                    supabase.table('unique_products').insert(unique_data).execute()
                else:
                    raise e
            logger.info(f"Inserted new product with GTIN {ean} in market {market_id}")
            
        return 'completed'
        
    except Exception as e:
        logger.error(f"Error enriching item {item['id']}: {e}")
        return 'failed'

if __name__ == "__main__":
    process_pending_purchases("manual")
