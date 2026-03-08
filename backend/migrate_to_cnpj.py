"""
One-time migration: Replace random market_id values (MKT...) with CNPJ extracted from NFCe URLs.

Run this script once after deploying the new CNPJ-based market_id logic.
It reads existing processed_urls to build a mapping from old market_id -> CNPJ,
then updates all tables accordingly. Handles merges when multiple old IDs map to the same CNPJ.

Usage:
    python migrate_to_cnpj.py          # dry-run (no changes)
    python migrate_to_cnpj.py --apply  # apply changes
"""

import os
import sys
from urllib.parse import urlparse, parse_qs, unquote
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

SKIP_MARKET_IDS = {'SYSTEM', 'PROCESSING'}


def extract_cnpj_from_url(url: str) -> str:
    parsed = urlparse(url)
    p_value = parse_qs(parsed.query).get('p', [''])[0]
    p_decoded = unquote(p_value)
    access_key = p_decoded.split('|')[0]
    if len(access_key) != 44 or not access_key.isdigit():
        raise ValueError(f"Invalid NFCe access key from URL: {url}")
    return access_key[6:20]


def build_market_id_to_cnpj_mapping():
    """Build a mapping from old market_id -> cnpj using processed_urls and purchases tables."""
    mapping = {}

    print("=== Step 1: Reading processed_urls ===")
    result = supabase.table('processed_urls').select('market_id, nfce_url').execute()
    for row in result.data:
        mid = row.get('market_id')
        url = row.get('nfce_url')
        if not mid or not url or mid in SKIP_MARKET_IDS:
            continue
        if mid.isdigit() and len(mid) == 14:
            continue
        try:
            cnpj = extract_cnpj_from_url(url)
            if mid not in mapping:
                mapping[mid] = cnpj
        except ValueError as e:
            print(f"  [WARN] Could not extract CNPJ for market_id={mid}: {e}")

    print(f"  Found {len(mapping)} mappings from processed_urls")

    # Fallback: check purchases table for markets not found above
    print("=== Step 2: Checking purchases for unmapped markets ===")
    markets = supabase.table('markets').select('market_id').execute()
    unmapped = [m['market_id'] for m in markets.data
                if m['market_id'] not in mapping
                and m['market_id'] not in SKIP_MARKET_IDS
                and not (m['market_id'].isdigit() and len(m['market_id']) == 14)]

    for mid in unmapped:
        purchase = supabase.table('purchases').select('nfce_url').eq('market_id', mid).limit(1).execute()
        if purchase.data and purchase.data[0].get('nfce_url'):
            try:
                cnpj = extract_cnpj_from_url(purchase.data[0]['nfce_url'])
                mapping[mid] = cnpj
                print(f"  Mapped {mid} -> {cnpj} via purchases table")
            except ValueError as e:
                print(f"  [WARN] Could not extract CNPJ for {mid} from purchases: {e}")
        else:
            print(f"  [WARN] No URL found for market_id={mid} - flagged for manual review")

    return mapping


def detect_merges(mapping):
    """Detect when multiple old market_ids map to the same CNPJ (need merging)."""
    cnpj_to_old_ids = defaultdict(list)
    for old_id, cnpj in mapping.items():
        cnpj_to_old_ids[cnpj].append(old_id)

    merges = {cnpj: ids for cnpj, ids in cnpj_to_old_ids.items() if len(ids) > 1}
    return merges


def apply_migration(mapping, merges, dry_run=True):
    prefix = "[DRY RUN] " if dry_run else ""

    print(f"\n=== Step 3: {'Simulating' if dry_run else 'Applying'} migration ===")
    print(f"  Total mappings: {len(mapping)}")
    print(f"  Merges detected: {len(merges)}")
    for cnpj, old_ids in merges.items():
        print(f"    CNPJ {cnpj} merges: {old_ids}")

    tables_with_fk = ['purchases', 'unique_products', 'product_backlog']
    tables_without_fk = ['processed_urls', 'product_lookup_log']

    for old_id, cnpj in mapping.items():
        if old_id == cnpj:
            continue
        print(f"\n{prefix}Migrating {old_id} -> {cnpj}")

        # Update child tables first (FK references)
        for table in tables_with_fk:
            rows = supabase.table(table).select('id').eq('market_id', old_id).execute()
            count = len(rows.data)
            if count > 0:
                print(f"  {prefix}{table}: {count} rows")
                if not dry_run:
                    supabase.table(table).update({'market_id': cnpj}).eq('market_id', old_id).execute()

        # Update non-FK tables
        for table in tables_without_fk:
            rows = supabase.table(table).select('id').eq('market_id', old_id).execute()
            count = len(rows.data)
            if count > 0:
                print(f"  {prefix}{table}: {count} rows")
                if not dry_run:
                    supabase.table(table).update({'market_id': cnpj}).eq('market_id', old_id).execute()

    # Handle merges: after updating all references, remove duplicate market entries
    print(f"\n=== Step 4: {'Simulating' if dry_run else 'Handling'} market merges ===")
    for cnpj, old_ids in merges.items():
        # Check if a market with the CNPJ already exists
        existing = supabase.table('markets').select('*').eq('market_id', cnpj).execute()
        if existing.data:
            print(f"  {prefix}Market {cnpj} already exists, removing old entries")
        else:
            # Pick the first old_id's market record to become the CNPJ-based record
            primary = supabase.table('markets').select('*').eq('market_id', old_ids[0]).execute()
            if primary.data and not dry_run:
                supabase.table('markets').update({'market_id': cnpj}).eq('market_id', old_ids[0]).execute()
                print(f"  Renamed {old_ids[0]} -> {cnpj} in markets table")
            old_ids = old_ids[1:]

        # Delete remaining duplicate market entries
        for old_id in old_ids:
            remaining = supabase.table('markets').select('id').eq('market_id', old_id).execute()
            if remaining.data:
                print(f"  {prefix}Deleting duplicate market entry: {old_id}")
                if not dry_run:
                    supabase.table('markets').delete().eq('market_id', old_id).execute()

    # Update non-merged markets
    print(f"\n=== Step 5: {'Simulating' if dry_run else 'Updating'} non-merged markets ===")
    merged_old_ids = set()
    for ids in merges.values():
        merged_old_ids.update(ids)

    for old_id, cnpj in mapping.items():
        if old_id == cnpj or old_id in merged_old_ids:
            continue
        existing = supabase.table('markets').select('id').eq('market_id', old_id).execute()
        if existing.data:
            print(f"  {prefix}Updating markets: {old_id} -> {cnpj}")
            if not dry_run:
                supabase.table('markets').update({'market_id': cnpj}).eq('market_id', old_id).execute()

    # Deduplicate unique_products after merges
    print(f"\n=== Step 6: {'Simulating' if dry_run else 'Deduplicating'} unique_products ===")
    for cnpj in merges.keys():
        products = supabase.table('unique_products').select('id, ean, last_updated').eq('market_id', cnpj).execute()
        ean_groups = defaultdict(list)
        for p in products.data:
            ean_groups[p['ean']].append(p)

        for ean, entries in ean_groups.items():
            if len(entries) <= 1:
                continue
            entries.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
            duplicates = entries[1:]
            print(f"  {prefix}CNPJ {cnpj}, EAN {ean}: keeping newest, removing {len(duplicates)} duplicates")
            if not dry_run:
                for dup in duplicates:
                    supabase.table('unique_products').delete().eq('id', dup['id']).execute()

    # Verification
    print(f"\n=== Step 7: Verification ===")
    markets = supabase.table('markets').select('market_id').execute()
    old_format = [m['market_id'] for m in markets.data if m['market_id'].startswith('MKT')]
    if old_format:
        print(f"  [WARN] {len(old_format)} markets still have old MKT... format: {old_format}")
    else:
        print("  All markets have been migrated to CNPJ format")


def main():
    dry_run = '--apply' not in sys.argv
    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE - No changes will be made")
        print("Run with --apply to execute the migration")
        print("=" * 60)
    else:
        print("=" * 60)
        print("APPLYING MIGRATION - Changes will be written to the database")
        print("=" * 60)
        confirm = input("Type 'yes' to confirm: ")
        if confirm.strip().lower() != 'yes':
            print("Aborted.")
            return

    mapping = build_market_id_to_cnpj_mapping()
    merges = detect_merges(mapping)
    apply_migration(mapping, merges, dry_run=dry_run)

    print("\n" + "=" * 60)
    if dry_run:
        print("Dry run complete. Review output above, then run with --apply")
    else:
        print("Migration complete.")
    print("=" * 60)


if __name__ == '__main__':
    main()
