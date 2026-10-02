import io
import re
import unittest
from unittest.mock import patch

from src.copyminas import create_app


class AdminProductsRouteTestCase(unittest.TestCase):
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
        login = self.client.get("/admin/login")
        token = self._csrf(login)
        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": token,
                "username": "admin",
                "password": "password",
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("src.copyminas.routes.admin.list_products")
    def test_product_list_shows_active_and_inactive_records(self, list_products):
        list_products.return_value = [
            {
                "id": 19,
                "nome": "Brother DCP-8157DN",
                "categoria": "Impressoras",
                "categoria_ativa": 1,
                "qtd": 2,
                "ativo": 1,
            },
            {
                "id": 20,
                "nome": "Produto inativo",
                "categoria": "Impressoras",
                "categoria_ativa": 1,
                "qtd": 0,
                "ativo": 0,
            },
        ]

        response = self.client.get("/admin/produtos")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Brother DCP-8157DN", response.data)
        self.assertIn(b"Produto inativo", response.data)
        self.assertIn(b"Novo produto", response.data)
        self.assertIn(b"data-admin-product-search", response.data)
        self.assertIn(b"Poss\xc3\xadveis duplicidades", response.data)

    @patch("src.copyminas.routes.admin.create_product", return_value=77)
    @patch("src.copyminas.routes.admin.list_categories")
    def test_new_product_posts_validated_data(self, list_categories, create_product):
        list_categories.return_value = [
            {"id": 1, "nome": "Impressoras", "ativo": 1},
        ]
        page = self.client.get("/admin/produtos/novo")
        token = self._csrf(page)

        response = self.client.post(
            "/admin/produtos/novo",
            data={
                "csrf_token": token,
                "nome": "Nova impressora",
                "descricao": "Descrição do produto.",
                "categoria_id": "1",
                "qtd": "4",
                "espec": "Velocidade: 40 ppm",
                "imagem1": "images/products/nova.webp",
                "imagem2": "",
                "imagem3": "",
                "imagem4": "",
                "imagem5": "",
                "ativo": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        create_product.assert_called_once()
        saved = create_product.call_args.args[0]
        self.assertEqual(saved["nome"], "Nova impressora")
        self.assertEqual(saved["categoria_id"], 1)
        self.assertEqual(saved["qtd"], 4)
        self.assertEqual(saved["ativo"], 1)

    @patch("src.copyminas.routes.admin.list_products", return_value=[])
    @patch("src.copyminas.routes.admin.save_product_image", return_value="images/products/uploaded.webp")
    @patch("src.copyminas.routes.admin.create_product", return_value=88)
    @patch("src.copyminas.routes.admin.list_categories")
    def test_product_upload_replaces_image_slot(
        self,
        list_categories,
        create_product,
        save_product_image,
        _list_products,
    ):
        list_categories.return_value = [
            {"id": 1, "nome": "Impressoras", "ativo": 1},
        ]
        page = self.client.get("/admin/produtos/novo")
        token = self._csrf(page)

        response = self.client.post(
            "/admin/produtos/novo",
            data={
                "csrf_token": token,
                "nome": "Produto com imagem",
                "descricao": "",
                "categoria_id": "1",
                "qtd": "",
                "espec": "",
                "imagem1": "",
                "imagem2": "",
                "imagem3": "",
                "imagem4": "",
                "imagem5": "",
                "ativo": "1",
                "upload1": (io.BytesIO(b"fake-image"), "produto.webp"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 302)
        save_product_image.assert_called_once()
        saved = create_product.call_args.args[0]
        self.assertEqual(saved["imagem1"], "images/products/uploaded.webp")

    @patch("src.copyminas.routes.admin.update_product")
    @patch("src.copyminas.routes.admin.list_categories")
    @patch("src.copyminas.routes.admin.get_product")
    def test_edit_product_requires_csrf(
        self,
        get_product,
        list_categories,
        update_product,
    ):
        get_product.return_value = {
            "id": 19,
            "nome": "Brother",
            "descricao": "",
            "imagem1": "",
            "imagem2": "",
            "imagem3": "",
            "imagem4": "",
            "imagem5": "",
            "espec": "",
            "ativo": 1,
            "qtd": 1,
            "categoria_id": 1,
            "updated_at": None,
        }
        list_categories.return_value = [
            {"id": 1, "nome": "Impressoras", "ativo": 1},
        ]

        response = self.client.post(
            "/admin/produtos/19",
            data={
                "csrf_token": "invalid",
                "nome": "Alterado",
                "categoria_id": "1",
            },
        )

        self.assertEqual(response.status_code, 400)
        update_product.assert_not_called()

    @patch("src.copyminas.routes.admin.list_categories")
    def test_categories_page_is_available(self, list_categories):
        list_categories.return_value = [
            {
                "id": 1,
                "nome": "Impressoras",
                "ativo": 1,
                "product_count": 6,
                "active_product_count": 6,
            }
        ]

        response = self.client.get("/admin/categorias")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Impressoras", response.data)
        self.assertIn(b"Nova categoria", response.data)

    @patch("src.copyminas.routes.admin.create_category", return_value=12)
    def test_new_category_uses_csrf_and_persists(self, create_category):
        page = self.client.get("/admin/categorias/nova")
        token = self._csrf(page)

        response = self.client.post(
            "/admin/categorias/nova",
            data={
                "csrf_token": token,
                "nome": "Celulares",
                "ativo": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        create_category.assert_called_once_with(
            {"nome": "Celulares", "ativo": 1}
        )

    @patch("src.copyminas.routes.admin.set_product_active")
    @patch("src.copyminas.routes.admin.list_products")
    def test_status_action_uses_post_and_csrf(self, list_products, set_active):
        list_products.return_value = [
            {
                "id": 19,
                "nome": "Brother",
                "categoria": "Impressoras",
                "categoria_ativa": 1,
                "qtd": 1,
                "ativo": 1,
            }
        ]
        page = self.client.get("/admin/produtos")
        token = self._csrf(page)

        response = self.client.post(
            "/admin/produtos/19/status",
            data={"csrf_token": token, "active": "0"},
        )

        self.assertEqual(response.status_code, 302)
        set_active.assert_called_once_with(19, False)


if __name__ == "__main__":
    unittest.main()
