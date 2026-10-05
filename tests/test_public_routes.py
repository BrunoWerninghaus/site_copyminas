import os
import unittest
from unittest.mock import patch

from src.copyminas import create_app
from src.copyminas.db import DatabaseUnavailable


class PublicRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, CATALOG_SOURCE="fixture")
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
        response = self.client.get("/solucoes")
        self.assertGreaterEqual(
            response.data.count("Consultar esta área".encode("utf-8")),
            5,
        )
        self.assertNotIn("ÍNDICE / ATENDIMENTO".encode("utf-8"), response.data)
        self.assertIn("Onde podemos ajudar.".encode("utf-8"), response.data)
        self.assertIn("Não sabe qual solução se encaixa?".encode("utf-8"), response.data)
        for code in ("01", "02", "03", "04", "05"):
            self.assertIn(f'id="solucao-{code}"'.encode("utf-8"), response.data)

    def test_products(self):
        self.assert_page("/produtos", "Catálogo Copy Minas")
        response = self.client.get("/produtos")
        self.assertIn(b"Brother DCP-8157DN", response.data)
        self.assertIn(b'id="categoria-1"', response.data)
        self.assertIn(b'id="categoria-2"', response.data)
        self.assertIn(b'id="categoria-8"', response.data)
        self.assertIn("Impressoras / 6".encode("utf-8"), response.data)
        self.assertIn("Computadores / 3".encode("utf-8"), response.data)
        self.assertIn("Redes / 1".encode("utf-8"), response.data)
        self.assertIn(b"data-catalog-search", response.data)
        self.assertIn(b'data-category-filter="all"', response.data)
        self.assertIn("Sob consulta".encode("utf-8"), response.data)
        self.assertIn("Manutenção".encode("utf-8"), response.data)

    def test_product_detail(self):
        self.assert_page(
            "/produtos/brother-dcp-8157dn",
            "Brother DCP-8157DN",
        )
        response = self.client.get("/produtos/brother-dcp-8157dn")
        self.assertIn("Consultar este produto".encode("utf-8"), response.data)
        self.assertIn(b"/contato?product=brother-dcp-8157dn", response.data)
        self.assertIn("Venda".encode("utf-8"), response.data)
        self.assertIn("Aluguel".encode("utf-8"), response.data)
        self.assertIn("Manutenção".encode("utf-8"), response.data)

    def test_contact_can_be_prefilled_from_product(self):
        response = self.client.get(
            "/contato?product=brother-dcp-8157dn"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Produto selecionado".encode("utf-8"), response.data)
        self.assertIn(b"Brother DCP-8157DN", response.data)
        self.assertIn(
            "Tenho interesse no produto".encode("utf-8"),
            response.data,
        )

    @patch(
        "src.copyminas.routes.public.get_public_products",
        side_effect=DatabaseUnavailable("catalog offline"),
    )
    def test_catalog_database_outage_returns_branded_503(self, _products):
        response = self.client.get("/produtos")

        self.assertEqual(response.status_code, 503)
        self.assertIn("Não foi possível consultar os produtos agora.".encode("utf-8"), response.data)
        self.assertIn("Falar com a Copy Minas".encode("utf-8"), response.data)

    @patch(
        "src.copyminas.routes.public.get_public_products",
        side_effect=DatabaseUnavailable("catalog offline"),
    )
    def test_home_survives_catalog_database_outage(self, _products):
        response = self.client.get("/home")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Impressão, tecnologia e equipamentos".encode("utf-8"), response.data)

    def test_public_pages_do_not_expose_migration_or_storage_language(self):
        for path in ("/home", "/produtos", "/produtos/brother-dcp-8157dn", "/empresa", "/contato"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                for forbidden in (
                    b"Site 2",
                    b"Site 3",
                    b"main_bd",
                    b"main_bd.contatos",
                    b"Asset original:",
                    b"Origem do registro:",
                    b"STATUS INICIAL",
                ):
                    self.assertNotIn(forbidden, response.data)


    def test_public_pages_share_navigation_and_footer(self):
        for path in (
            "/home",
            "/solucoes",
            "/produtos",
            "/produtos/brother-dcp-8157dn",
            "/empresa",
            "/contato",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'class="public-header"', response.data)
                self.assertIn(b'data-public-menu-toggle', response.data)
                self.assertIn(b'class="public-footer"', response.data)
                self.assertIn("Falar com a Copy Minas".encode("utf-8"), response.data)
                self.assertIn("Localização".encode("utf-8"), response.data)


    def test_customer_pages_do_not_show_construction_placeholders(self):
        for path in (
            "/home",
            "/produtos",
            "/produtos/brother-dcp-8157dn",
            "/solucoes",
            "/empresa",
            "/contato",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("EM ATUALIZAÇÃO".encode("utf-8"), response.data)

    def test_home_uses_real_company_facts_instead_of_institutional_placeholder(self):
        response = self.client.get("/home")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"EMPRESA / RESUMO", response.data)
        self.assertIn(b"12/07/2011", response.data)
        self.assertIn("Situação".encode("utf-8"), response.data)
        self.assertNotIn(b"home.company.image", response.data)

    def test_company(self):
        self.assert_page("/empresa", "Desde 2011 em Elói Mendes")
        response = self.client.get("/empresa")
        self.assertIn("Abrir no Google Maps".encode("utf-8"), response.data)
        self.assertIn("Falar com a Copy Minas".encode("utf-8"), response.data)

    def test_contact(self):
        self.assert_page("/contato", "(35) 98877-6969")
        response = self.client.get("/contato")
        self.assertIn(b"copyminas@hotmail.com", response.data)
        self.assertIn(b"/contato/enviar", response.data)
        self.assertIn("Enviar solicitação".encode("utf-8"), response.data)
        self.assertNotIn(b"main_bd", response.data)
        self.assertNotIn(b"main_bd.contatos", response.data)
        self.assertNotIn(b"STATUS INICIAL", response.data)

    @patch("src.copyminas.routes.public.send_contact_notifications")
    @patch(
        "src.copyminas.routes.public.create_contact_request",
        return_value="CM261002A1B2C3D4E5F6",
    )
    def test_contact_form_persists_and_returns_protocol(
        self,
        create_request,
        send_notification,
    ):
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
        self.assertIn("Solicitação recebida".encode("utf-8"), response.data)
        self.assertIn("confirmação".encode("utf-8"), response.data)
        self.assertNotIn(b"CM261002A1B2C3D4E5F6", response.data)
        self.assertNotIn(b"main_bd", response.data)
        create_request.assert_called_once()
        saved = create_request.call_args.args[0]
        self.assertEqual(saved["service_type"], "locacao_impressora")
        self.assertEqual(saved["equipment_quantity"], 3)
        self.assertEqual(saved["preferred_contact"], "whatsapp")
        send_notification.assert_called_once_with(
            "CM261002A1B2C3D4E5F6",
            saved,
        )

    @patch("src.copyminas.routes.public.send_contact_notifications")
    @patch("src.copyminas.routes.public.create_contact_request")
    def test_contact_form_rejects_implausible_submission(
        self,
        create_request,
        send_notification,
    ):
        response = self.client.post(
            "/contato/enviar",
            data={
                "name": "a",
                "company": "a",
                "email": "cliente@example.com",
                "phone": "a",
                "city": "a",
                "service_type": "manutencao_impressora",
                "equipment_quantity": "1",
                "preferred_contact": "telefone",
                "message": "a",
                "consent_privacy": "1",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("telefone válido".encode("utf-8"), response.data)
        self.assertIn("pelo menos 8 caracteres".encode("utf-8"), response.data)
        create_request.assert_not_called()
        send_notification.assert_not_called()

    @patch("src.copyminas.routes.public.send_contact_notifications")
    @patch("src.copyminas.routes.public.create_contact_request")
    def test_contact_form_rejects_incomplete_submission(
        self,
        create_request,
        send_notification,
    ):
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
        send_notification.assert_not_called()

    @patch(
        "src.copyminas.routes.public.send_contact_notifications",
        side_effect=Exception("unexpected raw exception"),
    )
    @patch(
        "src.copyminas.routes.public.create_contact_request",
        return_value="CM261002A1B2C3D4E5F6",
    )
    def test_unexpected_notification_errors_are_not_silently_swallowed(
        self,
        create_request,
        send_notification,
    ):
        with self.assertRaises(Exception):
            self.client.post(
                "/contato/enviar",
                data={
                    "name": "Cliente Teste",
                    "company": "",
                    "email": "cliente@example.com",
                    "phone": "(35) 99999-9999",
                    "city": "Eloi Mendes",
                    "service_type": "suporte",
                    "equipment_quantity": "",
                    "preferred_contact": "email",
                    "message": "Mensagem de teste.",
                    "consent_privacy": "1",
                },
            )

    def test_unknown_product_returns_branded_404(self):
        response = self.client.get("/produtos/produto-inexistente")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Página não encontrada".encode("utf-8"), response.data)
        self.assertIn(b"/produtos", response.data)

    def test_unknown_route_returns_branded_404(self):
        response = self.client.get("/pagina-que-nao-existe")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Este endereço não existe".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
