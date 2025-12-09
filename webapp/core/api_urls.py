from django.urls import path

from . import api_views

urlpatterns = [
    path('', api_views.api_root, name='api-root'),
    path('health/', api_views.health, name='api-health'),
    path('markets/', api_views.markets_list, name='api-markets'),
    path('markets/<str:market_id>/', api_views.market_detail, name='api-market-detail'),
    path(
        'markets/<str:market_id>/products/',
        api_views.market_products,
        name='api-market-products',
    ),
    path('nfce/extract/', api_views.nfce_extract, name='api-nfce-extract'),
    path('nfce/status/<path:nfce_url>/', api_views.nfce_status, name='api-nfce-status'),
    path('stats/', api_views.stats, name='api-stats'),
    path('schema/validate/', api_views.schema_validate, name='api-schema-validate'),
]


