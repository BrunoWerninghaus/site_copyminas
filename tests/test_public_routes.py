import unittest

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

    def test_unknown_product_returns_404(self):
        response = self.client.get("/produtos/produto-inexistente")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
