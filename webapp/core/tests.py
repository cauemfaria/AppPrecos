from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class DashboardViewTests(TestCase):
    @patch("core.views.supabase_service.list_markets")
    @patch("core.views.supabase_service.get_stats")
    def test_dashboard_renders_stats(self, mock_stats, mock_markets):
        mock_stats.return_value = {
            "total_markets": 2,
            "total_purchases": 10,
            "total_unique_products": 5,
        }
        mock_markets.return_value = [
            {"market_id": "MKT123", "name": "Mercado Teste", "address": "Rua 1"},
        ]
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Mercado Teste")
        self.assertContains(response, "Compras salvas")


class ApiViewTests(TestCase):
    @patch("core.api_views.supabase_service.list_markets", return_value=[])
    def test_markets_endpoint(self, _mock):
        response = self.client.get(reverse("api-markets"))
        self.assertEqual(response.status_code, 200)

    def test_nfce_extract_requires_url(self):
        response = self.client.post(reverse("api-nfce-extract"), data={}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("NFCe URL is required", response.json()["error"])


class ManifestViewTests(TestCase):
    def test_manifest_returns_pwa_metadata(self):
        response = self.client.get(reverse("pwa-manifest"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "AppPrecos")
