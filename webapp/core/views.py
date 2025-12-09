from __future__ import annotations

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .services import supabase_service


def dashboard(request: HttpRequest) -> HttpResponse:
    """
    Landing page for the PWA. Mirrors the Android dashboard by showing high level
    stats, recent markets, and a quick NFCe submission form.
    """
    stats = {}
    markets = []
    stats_error = None
    markets_error = None
    try:
        stats = supabase_service.get_stats()
    except Exception as exc:
        stats_error = str(exc)
    try:
        markets = supabase_service.list_markets()[:10]
    except Exception as exc:
        markets_error = str(exc)

    return render(
        request,
        "core/dashboard.html",
        {
            "stats": stats,
            "markets": markets,
            "stats_error": stats_error,
            "markets_error": markets_error,
        },
    )


def market_detail(request: HttpRequest, market_id: str) -> HttpResponse:
    market = supabase_service.get_market_by_code(market_id)
    if not market:
        raise Http404("Market not found")
    products = supabase_service.get_unique_products_for_market(market_id)
    return render(
        request,
        "core/market_detail.html",
        {
            "market": market,
            "products": products,
        },
    )


def qr_scanner(request: HttpRequest) -> HttpResponse:
    """
    Dedicated page for scanning NFCe QR codes from the browser.
    """
    return render(request, "core/qr_scanner.html")


@require_POST
def submit_nfce(request: HttpRequest) -> HttpResponse:
    """
    Handle NFCe submissions from the dashboard. This mirrors the Android client's
    synchronous flow but stays inside Django templates.
    """
    nfce_url = request.POST.get("nfce_url", "").strip()
    async_mode = bool(request.POST.get("async", False))

    if not nfce_url:
        messages.error(request, "Informe a URL NFC-e encontrada no QR Code.")
        return redirect(reverse("dashboard"))

    try:
        if async_mode:
            existing = supabase_service.get_processed_url(nfce_url)
            if existing:
                messages.warning(
                    request,
                    "Essa NFC-e já foi processada anteriormente.",
                )
                return redirect(reverse("dashboard"))
            record_id = supabase_service.mark_url_processing(nfce_url)
            supabase_service.process_nfce_async(nfce_url, record_id)
            messages.success(
                request,
                "NFC-e recebida! Estamos processando em segundo plano (15–20s).",
            )
        else:
            response = supabase_service.process_nfce_and_save(
                nfce_url,
                save=True,
                record_id=None,
            )
            messages.success(
                request,
                f"NFC-e salva com sucesso para {response['market']['name']}.",
            )
    except ValueError as exc:
        messages.error(request, str(exc))
    except Exception as exc:
        messages.error(request, f"Erro ao processar NFC-e: {exc}")

    return redirect(reverse("dashboard"))


def pwa_manifest(_: HttpRequest) -> JsonResponse:
    """
    Serve the manifest dynamically so values stay in sync with settings.
    """
    return JsonResponse(
        {
            "name": "AppPrecos",
            "short_name": "AppPrecos",
            "description": "Compare preços lendo QR codes NFC-e.",
            "start_url": "/",
            "display": "standalone",
            "theme_color": "#0f172a",
            "background_color": "#0f172a",
            "icons": [
                {"src": "/static/pwa/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/static/pwa/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            ],
        }
    )
