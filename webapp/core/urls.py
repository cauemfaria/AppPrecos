from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('markets/<str:market_id>/', views.market_detail, name='market-detail'),
    path('nfce/scan/', views.qr_scanner, name='qr-scanner'),
    path('nfce/submit/', views.submit_nfce, name='nfce-submit'),
    path('manifest.webmanifest', views.pwa_manifest, name='pwa-manifest'),
]


