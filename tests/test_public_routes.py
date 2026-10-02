import os
import unittest
from unittest.mock import patch

from src.copyminas import create_app


class PublicRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def assert_page(self, path, expected_text):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, path)
        self.assertIn(expected_text.encode("utf-8"), response.data)

    def test_existing_main_bd_defaults_are_compatible(self):
        with patch.dict(
            os.environ,
            {
                "DB_HOST": "",
                "DB_PORT": "",
                "DB_NAME": "",
                "DB_USER": "",
                "DB_PASSWORD": "",
                "DATABASE_HOST": "",
                "DATABASE_PORT": "",
                "DATABASE_NAME": "",
                "DATABASE_USER": "",
                "DATABASE_PASSWORD": "",
            },
            clear=False,
        ):
            for key in (
                "DB_HOST",
                "DB_PORT",
                "DB_NAME",
                "DB_USER",
                "DB_PASSWORD",
                "DATABASE_HOST",
                "DATABASE_PORT",
                "DATABASE_NAME",
                "DATABASE_USER",
                "DATABASE_PASSWORD",
            ):
                os.environ.pop(key, None)

            app = create_app()
            self.assertEqual(app.config["DB_HOST"], "127.0.0.1")
            self.assertEqual(app.config["DB_PORT"], 3306)
            self.assertEqual(app.config["DB_NAME"], "main_bd")
            self.assertEqual(app.config["DB_USER"], "root")
            self.assertEqual(app.config["DB_PASSWORD"], "")

    def test_legacy_database_environment_names_are_supported(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_HOST": "localhost",
                "DATABASE_PORT": "3307",
                "DATABASE_NAME": "main_bd",
                "DATABASE_USER": "copyminas",
                "DATABASE_PASSWORD": "secret",
            },
            clear=False,
        ):
            for key in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"):
                os.environ.pop(key, None)

            app = create_app()
            self.assertEqual(app.config["DB_HOST"], "localhost")
            self.assertEqual(app.config["DB_PORT"], 3307)
            self.assertEqual(app.config["DB_NAME"], "main_bd")
            self.assertEqual(app.config["DB_USER"], "copyminas")
            self.assertEqual(app.config["DB_PASSWORD"], "secret")

    def test_intro(self):
        self.assert_page("/", "Copy Minas")

    def test_home(self):
        self.assert_page("/home", "Impressão, tecnologia e equipamentos")

    def test_solutions(self):
        self.assert_page("/solucoes", "Tecnologia para a rotina de trabalho")

    def test_products(self):
        self.assert_page("/produtos", "Catálogo Copy Minas")
        response = self.client.get("/produtos")
        self.assertIn(b"Brother DCP-8157DN", response.data)

    def test_product_detail(self):
        self.assert_page(
            "/produtos/brother-dcp-8157dn",
            "Brother DCP-8157DN",
        )

    def test_company(self):
        self.assert_page("/empresa", "Desde 2011 em Elói Mendes")

    def test_contact(self):
        self.assert_page("/contato", "(35) 98877-6969")
        response = self.client.get("/contato")
        self.assertIn(b"copyminas@hotmail.com", response.data)
        self.assertIn(b"main_bd.contatos", response.data)
        self.assertIn(b"/contato/enviar", response.data)

    @patch(
        "src.copyminas.routes.public.create_contact_request",
        return_value="CM261002A1B2C3D4E5F6",
    )
    def test_contact_form_persists_and_returns_protocol(self, create_request):
        response = self.client.post(
            "/contato/enviar",
            data={
                "name": "Cliente Teste",
                "company": "Empresa Teste",
                "email": "cliente@example.com",
                "phone": "(35) 99999-9999",
                "city": "Eloi Mendes",
                "service_type": "locacao_impressora",
                "equipment_quantity": "3",
                "preferred_contact": "whatsapp",
                "message": "Preciso de uma cotacao.",
                "consent_privacy": "1",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CM261002A1B2C3D4E5F6", response.data)
        create_request.assert_called_once()
        saved = create_request.call_args.args[0]
        self.assertEqual(saved["service_type"], "locacao_impressora")
        self.assertEqual(saved["equipment_quantity"], 3)
        self.assertEqual(saved["preferred_contact"], "whatsapp")

    @patch("src.copyminas.routes.public.create_contact_request")
    def test_contact_form_rejects_incomplete_submission(self, create_request):
        response = self.client.post(
            "/contato/enviar",
            data={
                "name": "",
                "company": "",
                "email": "",
                "phone": "",
                "city": "",
                "service_type": "",
                "equipment_quantity": "",
                "preferred_contact": "",
                "message": "",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("Revise o formul".encode("utf-8"), response.data)
        create_request.assert_not_called()

    def test_unknown_product_returns_404(self):
        response = self.client.get("/produtos/produto-inexistente")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
