"""
Supabase integration helpers used by both the Django views and background tasks.

This module ports the proven Flask business logic (markets, purchases, NFCe saving)
into a reusable services layer so we can keep the Django views slim.
"""
from __future__ import annotations

import random
import string
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from supabase import Client, create_client

from . import nfce_extractor


class SupabaseNotConfigured(RuntimeError):
    """Raised when mandatory Supabase credentials are missing."""


_supabase_client: Optional[Client] = None
_client_lock = threading.Lock()


def get_supabase_client() -> Client:
    """
    Lazily instantiate a Supabase admin client using Django settings.
    """
    global _supabase_client

    with _client_lock:
        if _supabase_client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
                raise SupabaseNotConfigured(
                    "Supabase credentials are missing. "
                    "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment."
                )
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        return _supabase_client


def validate_database_schema() -> Dict[str, Any]:
    """
    Validate that required tables and columns exist in Supabase.
    Mirrors the Flask validation endpoint for parity.
    """
    supabase = get_supabase_client()
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
    }

    try:
        test_market_id = ensure_validation_market(supabase)
        test_purchase = {
            "market_id": test_market_id,
            "ncm": "00000000",
            "ean": "TEST",
            "product_name": "Test Product",
            "quantity": 1.0,
            "unidade_comercial": "UN",
            "total_price": 1.0,
            "unit_price": 1.0,
            "nfce_url": "test",
            "purchase_date": datetime.utcnow().isoformat(),
        }
        response = supabase.table("purchases").insert(test_purchase).execute()
        if response.data:
            test_id = response.data[0]["id"]
            supabase.table("purchases").delete().eq("id", test_id).execute()
        else:
            validation_results["valid"] = False
            validation_results["errors"].append("purchases table test insert failed")
    except Exception as exc:  # pragma: no cover - relies on Supabase
        validation_results["valid"] = False
        validation_results["errors"].append(
            f"purchases table validation failed: {exc}",
        )

    try:
        test_market_id = ensure_validation_market(supabase)
        test_unique = {
            "market_id": test_market_id,
            "ncm": "00000000",
            "ean": "TEST",
            "product_name": "Test Product",
            "unidade_comercial": "UN",
            "price": 1.0,
            "nfce_url": "test",
            "last_updated": datetime.utcnow().isoformat(),
        }
        response = supabase.table("unique_products").insert(test_unique).execute()
        if response.data:
            test_id = response.data[0]["id"]
            supabase.table("unique_products").delete().eq("id", test_id).execute()
        else:
            validation_results["valid"] = False
            validation_results["errors"].append("unique_products table test insert failed")
    except Exception as exc:  # pragma: no cover - relies on Supabase
        validation_results["valid"] = False
        validation_results["errors"].append(
            f"unique_products table validation failed: {exc}",
        )

    return validation_results


def ensure_validation_market(supabase: Client) -> str:
    """
    Ensure a temporary market exists for validation inserts.
    """
    marker = "TEST_VALIDATION"
    result = (
        supabase.table("markets")
        .select("*")
        .eq("market_id", marker)
        .execute()
    )
    if result.data:
        return marker
    supabase.table("markets").insert(
        {
            "market_id": marker,
            "name": "Test Validation Market",
            "address": "Validation Address",
        }
    ).execute()
    return marker


def generate_market_id() -> str:
    """Generate a random unique market ID (format: MKT + 8 random chars)."""
    chars = string.ascii_uppercase + string.digits
    random_part = "".join(random.choices(chars, k=8))
    return f"MKT{random_part}"


def ensure_market(market_info: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Match or create a market based on name/address.
    Returns tuple of market row + action performed (matched|created).
    """
    supabase = get_supabase_client()
    market_result = (
        supabase.table("markets")
        .select("*")
        .match({"name": market_info["name"], "address": market_info["address"]})
        .execute()
    )

    if market_result.data:
        return market_result.data[0], "matched"

    new_market_id = generate_market_id()
    while True:
        check = (
            supabase.table("markets")
            .select("id")
            .eq("market_id", new_market_id)
            .execute()
        )
        if not check.data:
            break
        new_market_id = generate_market_id()

    market_data = {
        "market_id": new_market_id,
        "name": market_info["name"],
        "address": market_info["address"],
    }
    insert = supabase.table("markets").insert(market_data).execute()
    return insert.data[0], "created"


@dataclass
class SaveResult:
    saved_to_purchases: int
    created_unique: int
    updated_unique: int


def save_products_to_supabase(
    market_id: str,
    products: List[Dict[str, Any]],
    nfce_url: str,
    purchase_date: Optional[datetime] = None,
) -> SaveResult:
    """
    Ported transaction-safe saving logic from the Flask backend.
    """
    supabase = get_supabase_client()
    purchase_date = purchase_date or datetime.utcnow()
    inserted_purchase_ids: List[int] = []
    inserted_unique_ids: List[int] = []
    updated_unique_backup: Dict[int, Dict[str, Any]] = {}

    try:
        saved_to_purchases = 0
        updated_unique = 0
        created_unique = 0

        for product in products:
            purchase_data = {
                "market_id": market_id,
                "ncm": product["ncm"],
                "ean": product.get("ean", "SEM GTIN"),
                "product_name": product.get("product", ""),
                "quantity": product.get("quantity", 0),
                "unidade_comercial": product.get("unidade_comercial", "UN"),
                "total_price": product.get("total_price", 0),
                "unit_price": product.get("unit_price", 0),
                "nfce_url": nfce_url,
                "purchase_date": purchase_date.isoformat(),
            }
            response = supabase.table("purchases").insert(purchase_data).execute()
            if not response.data:
                raise RuntimeError("Failed to insert purchase row: no data returned")
            inserted_purchase_ids.append(response.data[0]["id"])
            saved_to_purchases += 1

        for product in products:
            unique_data = {
                "market_id": market_id,
                "ncm": product["ncm"],
                "ean": product.get("ean", "SEM GTIN"),
                "product_name": product.get("product", ""),
                "unidade_comercial": product.get("unidade_comercial", "UN"),
                "price": product.get("unit_price", 0),
                "nfce_url": nfce_url,
                "last_updated": datetime.utcnow().isoformat(),
            }
            response = (
                supabase.table("unique_products")
                .select("*")
                .match({"market_id": market_id, "ncm": product["ncm"]})
                .execute()
            )
            if response.data:
                existing = response.data[0]
                updated_unique_backup[existing["id"]] = existing
                update_result = (
                    supabase.table("unique_products")
                    .update(unique_data)
                    .eq("id", existing["id"])
                    .execute()
                )
                if not update_result.data:
                    raise RuntimeError(
                        "Failed to update unique_products row: no data returned",
                    )
                updated_unique += 1
            else:
                insert_result = (
                    supabase.table("unique_products").insert(unique_data).execute()
                )
                if not insert_result.data:
                    raise RuntimeError(
                        "Failed to insert unique_products row: no data returned",
                    )
                inserted_unique_ids.append(insert_result.data[0]["id"])
                created_unique += 1

        return SaveResult(
            saved_to_purchases=saved_to_purchases,
            created_unique=created_unique,
            updated_unique=updated_unique,
        )

    except Exception:
        # Rollback purchases
        if inserted_purchase_ids:
            for purchase_id in inserted_purchase_ids:
                supabase.table("purchases").delete().eq("id", purchase_id).execute()
        # Rollback newly created unique_products
        if inserted_unique_ids:
            for unique_id in inserted_unique_ids:
                supabase.table("unique_products").delete().eq("id", unique_id).execute()
        # Restore updated rows
        if updated_unique_backup:
            for unique_id, old_data in updated_unique_backup.items():
                restore_data = {
                    key: value
                    for key, value in old_data.items()
                    if key not in {"id", "created_at"}
                }
                supabase.table("unique_products").update(restore_data).eq(
                    "id",
                    unique_id,
                ).execute()
        raise


def mark_url_processing(nfce_url: str) -> int:
    """
    Insert a processed_urls row with processing status, returning the record ID.
    """
    supabase = get_supabase_client()
    temp_url_data = {
        "nfce_url": nfce_url,
        "market_id": "PROCESSING",
        "products_count": 0,
        "status": "processing",
        "processed_at": datetime.utcnow().isoformat(),
    }
    insert = supabase.table("processed_urls").insert(temp_url_data).execute()
    return insert.data[0]["id"]


def update_processed_url(record_id: int, **fields: Any) -> None:
    supabase = get_supabase_client()
    supabase.table("processed_urls").update(fields).eq("id", record_id).execute()


def get_processed_url(nfce_url: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client()
    response = supabase.table("processed_urls").select("*").eq("nfce_url", nfce_url).execute()
    return response.data[0] if response.data else None


def list_markets() -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    response = supabase.table("markets").select("*").execute()
    return response.data


def get_market_by_code(market_id: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client()
    response = supabase.table("markets").select("*").eq("market_id", market_id).execute()
    return response.data[0] if response.data else None


def get_unique_products_for_market(market_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase_client()
    response = (
        supabase.table("unique_products").select("*").eq("market_id", market_id).execute()
    )
    return response.data


def get_stats() -> Dict[str, Any]:
    supabase = get_supabase_client()
    markets = supabase.table("markets").select("id").execute()
    purchases = supabase.table("purchases").select("id").execute()
    unique_products = supabase.table("unique_products").select("id").execute()
    return {
        "total_markets": len(markets.data),
        "total_purchases": len(purchases.data),
        "total_unique_products": len(unique_products.data),
        "architecture": "Supabase PostgreSQL - 3-Table Design",
        "status": "connected",
    }


def process_nfce_and_save(
    url: str,
    save: bool,
    record_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Synchronous NFCe extraction path (used by API + background worker).
    """
    supabase = get_supabase_client()
    result = nfce_extractor.extract_full_nfce_data(url, headless=True)
    market_info = result.get("market_info", {})
    products = result.get("products", [])

    if not products:
        if record_id:
            update_processed_url(record_id, status="error")
        raise ValueError("No products extracted from NFCe")

    if not save:
        return {"market_info": market_info, "products": products}

    if not market_info.get("name") or not market_info.get("address"):
        if record_id:
            update_processed_url(record_id, status="error")
        raise ValueError("Could not extract market information")

    market, action = ensure_market(market_info)
    save_result = save_products_to_supabase(market["market_id"], products, url)

    if record_id:
        update_processed_url(
            record_id,
            market_id=market["market_id"],
            products_count=len(products),
            status="success",
        )

    response = {
        "message": "NFCe data extracted and saved successfully",
        "market": {
            "id": market["id"],
            "market_id": market["market_id"],
            "name": market["name"],
            "address": market["address"],
            "action": action,
        },
        "products": products,
        "statistics": {
            "products_saved_to_main": save_result.saved_to_purchases,
            "unique_products_created": save_result.created_unique,
            "unique_products_updated": save_result.updated_unique,
            "market_action": action,
        },
    }
    return response


def process_nfce_async(url: str, record_id: int) -> threading.Thread:
    """
    Spawn a daemon thread to process NFCe in the background.
    """
    thread = threading.Thread(
        target=_background_nfce_worker,
        args=(url, record_id),
        daemon=True,
    )
    thread.start()
    return thread


def _background_nfce_worker(url: str, record_id: int) -> None:
    """
    Mirror the Flask background worker logic.
    """
    try:
        process_nfce_and_save(url, save=True, record_id=record_id)
    except Exception as exc:
        update_processed_url(record_id, status="error")
        print(f"[BACKGROUND TASK] Processing error for URL {url}: {exc}")

