"""
Enrichment Worker Script
Processes pending items in the purchases table and performs product enrichment.
Handles Bluesoft Cosmos API token rotation.
"""

import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Import enrichment logic from app.py
from app import (
    supabase, 
    get_product_from_cosmos, 
    search_product_on_cosmos,
    log_product_lookup
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

# Configuration
BATCH_SIZE = 10
SLEEP_BETWEEN_BATCHES = 5

def process_pending_purchases():
    """Main loop to process pending purchases until the queue is empty (One-Shot)"""
    
    logger.info("Starting Enrichment Worker (Cosmos Blue Mode - One-Shot)...")
    
    while True:
        try:
            # Fetch batch of unenriched products
            response = supabase.table('purchases').select('*').eq('enriched', False).limit(BATCH_SIZE).execute()
            pending_items = response.data
            
            if not pending_items:
                logger.info("Queue is empty. Enrichment complete.")
                break
            
            logger.info(f"Processing batch of {len(pending_items)} items...")
            
            for item in pending_items:
                # Tentativa de enriquecimento
                status = enrich_single_purchase(item)
                
                if status == 'completed':
                    # Mark as enriched
                    supabase.table('purchases').update({
                        'enriched': True,
                        'enrichment_status': 'completed',
                        'enrichment_error': None
                    }).eq('id', item['id']).execute()
                    logger.info(f"Successfully enriched item {item['id']}")
                elif status == 'rate_limited':
                    # STOP EVERYTHING immediately
                    logger.error("!!! RATE LIMIT REACHED IN ALL TOKENS !!! Stopping worker to avoid backlog misclassification.")
                    return # Exit the function and script
                elif status == 'backlog':
                    # Mark as backlog in purchases
                    supabase.table('purchases').update({
                        'enriched': True, # Mark as enriched True so it doesn't try again in next batch
                        'enrichment_status': 'backlog',
                        'enrichment_error': 'No GTIN found via direct lookup or search'
                    }).eq('id', item['id']).execute()
                    
                    # Insert into product_backlog
                    backlog_data = {
                        'purchase_id': item['id'],
                        'market_id': item['market_id'],
                        'original_product_name': item['product_name'],
                        'ncm': item['ncm'],
                        'ean': item['ean'], # Original EAN (likely SEM GTIN)
                        'created_at': datetime.utcnow().isoformat()
                    }
                    supabase.table('product_backlog').insert(backlog_data).execute()
                    logger.info(f"Item {item['id']} moved to backlog")
                else:
                    # Mark as failed
                    supabase.table('purchases').update({
                        'enrichment_status': 'failed',
                        'enrichment_error': 'All enrichment sources failed or request error'
                    }).eq('id', item['id']).execute()
                    logger.warning(f"Failed to enrich item {item['id']}")
            
            logger.info(f"Batch completed. Sleeping for {SLEEP_BETWEEN_BATCHES}s...")
            time.sleep(SLEEP_BETWEEN_BATCHES)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(30)

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
        # STEP 1: Bluesoft Cosmos (Direct GTIN lookup)
        if ean and ean != 'SEM GTIN' and len(ean) >= 8:
            cosmos_success, cosmos_product_name, cosmos_brand, cosmos_time, cosmos_error = get_product_from_cosmos(ean)
            
            cosmos_result = {
                'success': cosmos_success, 'product_name': cosmos_product_name,
                'brand': cosmos_brand, 'time_ms': cosmos_time, 'error': cosmos_error
            }
            
            if cosmos_error == "TOKENS_EXHAUSTED":
                is_rate_limited = True
            
            if cosmos_success and cosmos_product_name:
                canonical_name = cosmos_product_name
                source_used = "COSMOS_BLUE"
        
        # STEP 2: Bluesoft Cosmos (Search by Name + NCM filter)
        if not canonical_name and not is_rate_limited:
            # Try searching by name since GTIN is missing or wasn't found
            search_success, search_name, search_gtin, search_brand, search_time, search_error = search_product_on_cosmos(
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
                    'brand': search_brand, 'time_ms': search_time, 'error': None,
                    'search_used': True, 'found_gtin': search_gtin
                }
                logger.info(f"Found GTIN {search_gtin} via search for '{original_product_name}'")

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
        unique_data = {
            'market_id': market_id,
            'ncm': ncm,
            'ean': ean,
            'product_name': canonical_name,
            'unidade_comercial': item.get('unidade_comercial', 'UN'),
            'price': item.get('unit_price', 0),
            'nfce_url': nfce_url,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Check if exists in this market by market_id AND ean (Deterministic)
        existing = supabase.table('unique_products').select('id').match({
            'market_id': market_id,
            'ean': ean
        }).execute()
        
        if existing.data:
            supabase.table('unique_products').update(unique_data).eq('id', existing.data[0]['id']).execute()
            logger.info(f"Updated existing product {existing.data[0]['id']} in market {market_id}")
        else:
            supabase.table('unique_products').insert(unique_data).execute()
            logger.info(f"Inserted new product with GTIN {ean} in market {market_id}")
            
        return 'completed'
        
    except Exception as e:
        logger.error(f"Error enriching item {item['id']}: {e}")
        return 'failed'

if __name__ == "__main__":
    process_pending_purchases()
