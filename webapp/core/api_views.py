"""
REST API views that mirror the original Flask endpoints so the Android client
and new PWA can share a consistent contract.
"""
from __future__ import annotations

from datetime import datetime

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import supabase_service


@api_view(["GET"])
def api_root(_request):
    return Response(
        {
            "name": "AppPrecos API v2 (Django)",
            "version": "2.1",
            "architecture": "Supabase PostgreSQL - 3-Table Design",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "markets": "/api/markets",
                "market": "/api/markets/{market_id}",
                "market_products": "/api/markets/{market_id}/products",
                "nfce_extract": "/api/nfce/extract",
                "nfce_status": "/api/nfce/status/{url}",
                "stats": "/api/stats",
                "health": "/api/health",
                "schema_check": "/api/schema/validate",
            },
        }
    )


@api_view(["GET"])
def health(_request):
    try:
        supabase_service.get_supabase_client().table("markets").select("id").limit(1).execute()
        return Response(
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as exc:  # pragma: no cover - relies on Supabase connectivity
        return Response(
            {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["GET"])
def markets_list(_request):
    try:
        return Response(supabase_service.list_markets())
    except Exception as exc:
        return Response({"error": str(exc)}, status=500)


@api_view(["GET"])
def market_detail(_request, market_id: str):
    try:
        market = supabase_service.get_market_by_code(market_id)
        if not market:
            return Response({"error": "Market not found"}, status=404)
        return Response(market)
    except Exception as exc:
        return Response({"error": str(exc)}, status=500)


@api_view(["GET"])
def market_products(_request, market_id: str):
    try:
        market = supabase_service.get_market_by_code(market_id)
        if not market:
            return Response({"error": "Market not found"}, status=404)
        products = supabase_service.get_unique_products_for_market(market_id)
        return Response(
            {
                "market": market,
                "products": products,
                "total": len(products),
            }
        )
    except Exception as exc:
        return Response({"error": f"Failed to fetch products: {exc}"}, status=500)


@api_view(["POST"])
def nfce_extract(request):
    url = request.data.get("url")
    save = bool(request.data.get("save", True))
    use_async = bool(request.data.get("async", False))

    if not url:
        return Response({"error": "NFCe URL is required"}, status=400)

    record_id = None
    try:
        if save:
            existing = supabase_service.get_processed_url(url)
            if existing:
                return Response(
                    {
                        "error": "This NFCe has already been processed",
                        "message": "URL already exists in database",
                        "status": existing.get("status", "unknown"),
                        "processed_at": existing.get("processed_at"),
                        "market_id": existing.get("market_id"),
                        "products_count": existing.get("products_count"),
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            record_id = supabase_service.mark_url_processing(url)

            if use_async:
                supabase_service.process_nfce_async(url, record_id)
                return Response(
                    {
                        "message": "NFCe URL accepted successfully! Processing started.",
                        "status": "processing",
                        "url_record_id": record_id,
                        "check_status_at": f"/api/nfce/status/{url}",
                        "estimated_time": "15-20 seconds",
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

        if save:
            response = supabase_service.process_nfce_and_save(url, save=True, record_id=record_id)
            return Response(response, status=status.HTTP_201_CREATED)

        response = supabase_service.process_nfce_and_save(url, save=False, record_id=None)
        return Response(
            {
                "message": "NFCe data extracted successfully (not saved)",
                **response,
            }
        )

    except ValueError as exc:
        if record_id:
            supabase_service.update_processed_url(record_id, status="error")
        return Response({"error": str(exc)}, status=400)
    except Exception as exc:
        if record_id:
            supabase_service.update_processed_url(record_id, status="error")
        return Response({"error": str(exc)}, status=500)


@api_view(["GET"])
def nfce_status(_request, nfce_url: str):
    try:
        record = supabase_service.get_processed_url(nfce_url)
        if not record:
            return Response(
                {"status": "not_found", "message": "URL not processed yet"},
                status=404,
            )
        return Response(
            {
                "status": record["status"],
                "market_id": record["market_id"],
                "products_count": record["products_count"],
                "processed_at": record["processed_at"],
            }
        )
    except Exception as exc:
        return Response({"error": str(exc)}, status=500)


@api_view(["GET"])
def stats(_request):
    try:
        return Response(supabase_service.get_stats())
    except Exception as exc:
        return Response(
            {
                "error": str(exc),
                "hint": "Tables may not exist yet. Run SQL migrations in Supabase.",
                "total_markets": 0,
                "total_purchases": 0,
                "total_unique_products": 0,
            },
            status=500,
        )


@api_view(["GET"])
def schema_validate(_request):
    try:
        validation = supabase_service.validate_database_schema()
        status_code = status.HTTP_200_OK if validation["valid"] else status.HTTP_500_INTERNAL_SERVER_ERROR
        payload = {
            "status": "valid" if validation["valid"] else "invalid",
            "details": validation,
        }
        if not validation["valid"]:
            payload["action_required"] = "Run add_product_name_migration.sql in Supabase SQL Editor"
        return Response(payload, status=status_code)
    except Exception as exc:
        return Response(
            {
                "status": "error",
                "message": f"Schema validation failed: {exc}",
                "action_required": "Check database connectivity and table existence",
            },
            status=500,
        )


