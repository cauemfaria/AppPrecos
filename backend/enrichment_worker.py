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
    get_product_from_open_food_facts,
    call_llm_for_product_match,
    log_llm_decision,
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
                success = enrich_single_purchase(item)
                
                if success:
                    # Mark as enriched
                    supabase.table('purchases').update({
                        'enriched': True,
                        'enrichment_status': 'completed',
                        'enrichment_error': None
                    }).eq('id', item['id']).execute()
                    logger.info(f"Successfully enriched item {item['id']}")
                else:
                    # Mark as failed
                    supabase.table('purchases').update({
                        'enrichment_status': 'failed',
                        'enrichment_error': 'All enrichment sources failed or limit reached'
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
    Returns: success_bool
    """
    market_id = item['market_id']
    original_product_name = item['product_name']
    ncm = item['ncm']
    ean = item['ean']
    nfce_url = item['nfce_url']
    
    canonical_name = None
    source_used = None
    cosmos_result = None
    off_result = None
    llm_result = None
    
    try:
        # STEP 1: Bluesoft Cosmos
        if ean and ean != 'SEM GTIN' and len(ean) >= 8:
            cosmos_success, cosmos_product_name, cosmos_brand, cosmos_time, cosmos_error = get_product_from_cosmos(ean)
            
            cosmos_result = {
                'success': cosmos_success, 'product_name': cosmos_product_name,
                'brand': cosmos_brand, 'time_ms': cosmos_time, 'error': cosmos_error
            }
            if cosmos_success and cosmos_product_name:
                canonical_name = cosmos_product_name
                source_used = "COSMOS_BLUE"
        
        # STEP 2: Open Food Facts (Fallback)
        if not canonical_name and ean and ean != 'SEM GTIN' and len(ean) >= 8:
            off_success, off_product_name, off_time = get_product_from_open_food_facts(ean)
            off_result = {
                'success': off_success, 'product_name': off_product_name,
                'time_ms': off_time, 'error': None if off_success else 'Not found'
            }
            if off_success and off_product_name:
                canonical_name = off_product_name
                source_used = "OPEN_FOOD_FACTS"
        
        # STEP 3: LLM (Final Fallback)
        if not canonical_name:
            # Query existing products with same NCM from ALL markets
            response = supabase.table('unique_products').select('*').eq('ncm', ncm).execute()
            existing_products = response.data if response.data else []
            
            llm_decision, llm_matched_id, llm_canonical, llm_prompt, llm_response, llm_time, llm_error = call_llm_for_product_match(
                new_product_name=original_product_name,
                existing_products=existing_products
            )
            llm_result = {
                'success': llm_canonical is not None, 'decision': llm_decision,
                'matched_id': llm_matched_id, 'time_ms': llm_time, 'error': llm_error
            }
            if llm_canonical:
                canonical_name = llm_canonical
                source_used = "LLM"
            
            log_llm_decision(
                market_id=market_id, ncm=ncm, new_product_name=original_product_name,
                canonical_name=canonical_name, existing_products=existing_products,
                llm_prompt=llm_prompt, llm_response=llm_response,
                decision=llm_decision, matched_product_id=llm_matched_id,
                success=llm_canonical is not None, error_message=llm_error,
                execution_time_ms=llm_time
            )
        
        # Log lookup
        log_product_lookup(
            nfce_url=nfce_url, market_id=market_id, gtin=ean, ncm=ncm,
            original_name=original_product_name, final_name=canonical_name,
            cosmos_result=cosmos_result, off_result=off_result, llm_result=llm_result,
            source_used=source_used, success=canonical_name is not None
        )
        
        if not canonical_name:
            return False
            
        # Upsert to unique_products
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
        
        # Check if exists in this market
        existing = supabase.table('unique_products').select('id').match({
            'market_id': market_id,
            'ncm': ncm,
            'product_name': canonical_name
        }).execute()
        
        if existing.data:
            supabase.table('unique_products').update(unique_data).eq('id', existing.data[0]['id']).execute()
        else:
            supabase.table('unique_products').insert(unique_data).execute()
            
        return True
        
    except Exception as e:
        logger.error(f"Error enriching item {item['id']}: {e}")
        return False

if __name__ == "__main__":
    process_pending_purchases()
