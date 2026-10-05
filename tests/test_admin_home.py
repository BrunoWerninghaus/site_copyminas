import re
import unittest
from unittest.mock import patch

from src.copyminas import create_app


class AdminHomeManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            CATALOG_SOURCE="fixture",
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

    @patch("src.copyminas.routes.admin.home_schema_ready", return_value=False)
    def test_uninitialized_home_offers_explicit_setup(self, _ready):
        response = self.client.get("/admin/home")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Inicializar módulo Home".encode("utf-8"), response.data)
        self.assertIn(b"/admin/home/inicializar", response.data)

    @patch("src.copyminas.routes.admin.initialize_home_schema")
    @patch("src.copyminas.routes.admin.list_products")
    def test_home_setup_requires_csrf_and_seeds_featured_products(
        self,
        list_products,
        initialize,
    ):
        list_products.return_value = [
            {"id": 21, "ativo": 1, "categoria_ativa": 1},
            {"id": 25, "ativo": 1, "categoria_ativa": 1},
            {"id": 20, "ativo": 0, "categoria_ativa": 1},
        ]
        page = self.client.get("/admin/login")
        # Already authenticated: obtain a CSRF-bearing page through an existing form.
        page = self.client.get("/admin/categorias/nova")
        token = self._csrf(page)

        response = self.client.post(
            "/admin/home/inicializar",
            data={"csrf_token": token},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(initialize.call_count, 1)
        self.assertEqual(
            initialize.call_args.kwargs["featured_product_ids"],
            [21, 25],
        )

    @patch("src.copyminas.routes.admin.update_home_config")
    @patch("src.copyminas.routes.admin._decorate_products")
    @patch("src.copyminas.routes.admin.list_products", return_value=[])
    @patch("src.copyminas.routes.admin.list_home_news", return_value=[])
    @patch("src.copyminas.routes.admin.get_home_config")
    @patch("src.copyminas.routes.admin.home_schema_ready", return_value=True)
    def test_home_config_saves_selected_featured_order(
        self,
        _ready,
        get_config,
        _news,
        _products,
        decorate,
        update_config,
    ):
        get_config.return_value = {
            "announcement_active": False,
            "announcement_label": "AVISO",
            "announcement_text": "",
            "announcement_link_label": "",
            "announcement_link_url": "",
            "hero_kicker": "Copy Minas",
            "hero_title": "Título",
            "hero_summary": "Resumo",
            "primary_cta_label": "Soluções",
            "primary_cta_url": "/solucoes",
            "secondary_cta_label": "Produtos",
            "secondary_cta_url": "/produtos",
            "featured_product_ids": [21],
            "show_solutions": True,
            "show_company": True,
            "show_location": True,
        }
        decorate.return_value = [
            {
                "id": 21,
                "nome": "Produto 21",
                "categoria": "Impressoras",
                "ativo": 1,
                "categoria_ativa": 1,
            },
            {
                "id": 25,
                "nome": "Produto 25",
                "categoria": "Impressoras",
                "ativo": 1,
                "categoria_ativa": 1,
            },
        ]

        page = self.client.get("/admin/home")
        token = self._csrf(page)
        response = self.client.post(
            "/admin/home",
            data={
                "csrf_token": token,
                "hero_kicker": "Copy Minas",
                "hero_title": "Nova Home",
                "hero_summary": "Resumo atualizado",
                "primary_cta_label": "Produtos",
                "primary_cta_url": "/produtos",
                "secondary_cta_label": "Contato",
                "secondary_cta_url": "/contato",
                "featured_product_1": "25",
                "featured_product_2": "21",
                "show_solutions": "1",
                "show_company": "1",
                "show_location": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        saved = update_config.call_args.args[0]
        self.assertEqual(saved["featured_product_ids"], [25, 21])
        self.assertEqual(saved["hero_title"], "Nova Home")

    @patch("src.copyminas.routes.admin.create_home_news", return_value=7)
    @patch("src.copyminas.routes.admin.home_schema_ready", return_value=True)
    def test_new_home_news_is_created_through_admin(self, _ready, create_news):
        page = self.client.get("/admin/home/novidades/nova")
        token = self._csrf(page)

        response = self.client.post(
            "/admin/home/novidades/nova",
            data={
                "csrf_token": token,
                "label": "NOVIDADE",
                "title": "Novo atendimento",
                "body": "Agora também atendemos esta demanda.",
                "link_label": "Falar conosco",
                "link_url": "/contato",
                "active": "1",
                "sort_order": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        create_news.assert_called_once()

    def test_home_manager_requires_authentication(self):
        other = self.app.test_client()
        response = other.get("/admin/home")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/login"))


if __name__ == "__main__":
    unittest.main()
