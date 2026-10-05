import re
import unittest
from datetime import datetime
from unittest.mock import patch

from src.copyminas import create_app
from src.copyminas.db import DatabaseUnavailable


class AdminDashboardTestCase(unittest.TestCase):
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

    def _products(self):
        old = datetime(2026, 10, 1, 9, 0)
        new = datetime(2026, 10, 5, 8, 30)
        return [
            {
                "id": 21,
                "nome": "Samsung ProXpress SL-M4070FR",
                "descricao": "",
                "imagem1": "",
                "imagem2": "",
                "imagem3": "",
                "imagem4": "",
                "imagem5": "",
                "espec": "",
                "ativo": 1,
                "qtd": None,
                "categoria_id": 1,
                "categoria": "Impressoras",
                "categoria_ativa": 1,
                "created_at": old,
                "updated_at": new,
            },
            {
                "id": 20,
                "nome": "Samsung ProXpress SL-M4070FR",
                "descricao": "",
                "imagem1": "",
                "imagem2": "",
                "imagem3": "",
                "imagem4": "",
                "imagem5": "",
                "espec": "",
                "ativo": 0,
                "qtd": None,
                "categoria_id": 1,
                "categoria": "Impressoras",
                "categoria_ativa": 1,
                "created_at": old,
                "updated_at": old,
            },
        ]

    def _categories(self):
        return [
            {
                "id": 1,
                "nome": "Impressoras",
                "ativo": 1,
                "product_count": 2,
                "active_product_count": 1,
            },
            {
                "id": 9,
                "nome": "Legado",
                "ativo": 0,
                "product_count": 1,
                "active_product_count": 1,
            },
        ]

    def _contacts(self):
        return [
            {
                "id": 7,
                "protocol": "CM261005ABCDEF123456",
                "name": "Cliente Novo",
                "company": "",
                "email": "novo@example.com",
                "phone": "(35) 99999-9999",
                "city": "Elói Mendes",
                "service_type": "manutencao_impressora",
                "status": "novo",
                "created_at": datetime(2026, 10, 5, 8, 0),
                "updated_at": datetime(2026, 10, 5, 8, 0),
            },
            {
                "id": 6,
                "protocol": "CM261004ABCDEF654321",
                "name": "Cliente Em Atendimento",
                "company": "",
                "email": "atendimento@example.com",
                "phone": "(35) 98888-8888",
                "city": "Varginha",
                "service_type": "suporte",
                "status": "em_atendimento",
                "created_at": datetime(2026, 10, 4, 17, 0),
                "updated_at": datetime(2026, 10, 5, 7, 0),
            },
        ]

    @patch("src.copyminas.routes.admin.list_contacts")
    @patch("src.copyminas.routes.admin.list_categories")
    @patch("src.copyminas.routes.admin.list_products")
    def test_dashboard_surfaces_real_operational_attention(
        self,
        list_products,
        list_categories,
        list_contacts,
    ):
        list_products.return_value = self._products()
        list_categories.return_value = self._categories()
        list_contacts.return_value = self._contacts()

        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Visão geral".encode("utf-8"), response.data)
        self.assertIn("Possíveis duplicidades".encode("utf-8"), response.data)
        self.assertIn("Produtos publicados sem imagem".encode("utf-8"), response.data)
        self.assertIn(
            "Categoria inativa com produtos ativos".encode("utf-8"),
            response.data,
        )
        self.assertIn(
            "Novos contatos aguardando triagem".encode("utf-8"),
            response.data,
        )
        self.assertIn(b"Cliente Novo", response.data)
        self.assertIn(b"Samsung ProXpress SL-M4070FR", response.data)
        self.assertIn("Cadastrar produto".encode("utf-8"), response.data)
        self.assertIn("Criar categoria".encode("utf-8"), response.data)

    @patch("src.copyminas.routes.admin.static_asset_exists", return_value=True)
    @patch("src.copyminas.routes.admin.normalize_static_path", return_value="images/products/teste.webp")
    @patch("src.copyminas.routes.admin.list_contacts", return_value=[])
    @patch("src.copyminas.routes.admin.list_categories")
    @patch("src.copyminas.routes.admin.list_products")
    def test_dashboard_can_render_clear_state(
        self,
        list_products,
        list_categories,
        _list_contacts,
        _normalize,
        _exists,
    ):
        products = [self._products()[0]]
        products[0]["nome"] = "Produto único"
        products[0]["imagem1"] = "images/products/teste.webp"

        list_products.return_value = products
        list_categories.return_value = [self._categories()[0]]

        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Nenhuma pendência detectada".encode("utf-8"),
            response.data,
        )

    @patch(
        "src.copyminas.routes.admin.list_contacts",
        side_effect=DatabaseUnavailable("offline"),
    )
    @patch("src.copyminas.routes.admin.list_categories")
    @patch("src.copyminas.routes.admin.list_products")
    def test_dashboard_keeps_catalog_when_contacts_are_unavailable(
        self,
        list_products,
        list_categories,
        _list_contacts,
    ):
        products = [self._products()[0]]
        products[0]["nome"] = "Produto disponível"
        list_products.return_value = products
        list_categories.return_value = [self._categories()[0]]

        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Produto dispon", response.data)
        self.assertIn("Contatos indisponíveis no momento".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
