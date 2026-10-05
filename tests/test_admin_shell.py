import re
import unittest
from unittest.mock import patch

from src.copyminas import create_app
from src.copyminas.db import DatabaseUnavailable


class AdminShellTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            ADMIN_USERNAME="admin",
            ADMIN_PASSWORD="password",
            SECRET_KEY="test-secret",
        )
        self.client = self.app.test_client()
        self._login()

    def _csrf(self, response):
        match = re.search(
            rb'name="csrf_token" value="([^"]+)"',
            response.data,
        )
        self.assertIsNotNone(match)
        return match.group(1).decode("utf-8")

    def _login(self):
        page = self.client.get("/admin/login")
        token = self._csrf(page)
        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": token,
                "username": "admin",
                "password": "password",
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("src.copyminas.routes.admin.list_contacts", return_value=[])
    @patch("src.copyminas.routes.admin.list_categories", return_value=[])
    @patch("src.copyminas.routes.admin.list_products", return_value=[])
    def test_dashboard_renders_application_shell(
        self,
        _products,
        _categories,
        _contacts,
    ):
        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-admin-sidebar", response.data)
        self.assertIn(b"data-admin-search-open", response.data)
        self.assertIn(b"data-admin-global-search", response.data)
        self.assertIn(b"admin-shell.js", response.data)
        self.assertIn(b"Ctrl K", response.data)
        self.assertIn(b"/admin/contatos", response.data)
        self.assertIn(b"/admin/produtos", response.data)
        self.assertIn(b"/admin/categorias", response.data)

    @patch("src.copyminas.routes.admin.list_contacts")
    @patch("src.copyminas.routes.admin.list_categories")
    @patch("src.copyminas.routes.admin.list_products")
    def test_global_search_returns_products_categories_and_contacts(
        self,
        list_products,
        list_categories,
        list_contacts,
    ):
        list_products.return_value = [
            {
                "id": 21,
                "nome": "Samsung ProXpress SL-M4070FR",
                "categoria": "Impressoras",
                "descricao": "Multifuncional laser",
                "ativo": 1,
            }
        ]
        list_categories.return_value = [
            {
                "id": 7,
                "nome": "Samsung",
                "ativo": 1,
                "product_count": 1,
            }
        ]
        list_contacts.return_value = [
            {
                "id": 9,
                "protocol": "CM-SAMSUNG-001",
                "name": "Samsung Cliente",
                "company": "",
                "email": "cliente@example.com",
                "phone": "(35) 99999-9999",
                "city": "Elói Mendes",
                "service_type": "manutencao_impressora",
                "status": "novo",
            }
        ]

        response = self.client.get("/admin/busca?q=samsung")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload["results"]), 3)
        self.assertEqual(
            {item["kind"] for item in payload["results"]},
            {"product", "category", "contact"},
        )
        self.assertTrue(all(payload["sources"].values()))
        self.assertIn("/admin/produtos/21", payload["results"][0]["href"])

    @patch("src.copyminas.routes.admin.list_contacts")
    @patch("src.copyminas.routes.admin.list_categories")
    @patch(
        "src.copyminas.routes.admin.list_products",
        side_effect=DatabaseUnavailable("offline"),
    )
    def test_global_search_degrades_per_source(
        self,
        _products,
        list_categories,
        list_contacts,
    ):
        list_categories.return_value = []
        list_contacts.return_value = [
            {
                "id": 9,
                "protocol": "CM261005ABC",
                "name": "Cliente Teste",
                "company": "",
                "email": "cliente@example.com",
                "phone": "(35) 99999-9999",
                "city": "Elói Mendes",
                "service_type": "suporte",
                "status": "em_atendimento",
            }
        ]

        response = self.client.get("/admin/busca?q=cliente")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertFalse(payload["sources"]["products"])
        self.assertTrue(payload["sources"]["contacts"])
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["kind"], "contact")

    def test_global_search_requires_authentication(self):
        other = self.app.test_client()
        response = other.get("/admin/busca?q=teste")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/login"))


if __name__ == "__main__":
    unittest.main()
