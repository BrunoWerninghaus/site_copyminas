import re
import unittest

from src.copyminas import create_app


class AdminAuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            CATALOG_SOURCE="fixture",
            ADMIN_USERNAME="copyminas-admin",
            ADMIN_PASSWORD="test-only-long-password",
            SECRET_KEY="test-secret-key",
        )
        self.client = self.app.test_client()

    def _csrf_from_login(self):
        response = self.client.get("/admin/login")
        self.assertEqual(response.status_code, 200)
        match = re.search(
            rb'name="csrf_token" value="([^"]+)"',
            response.data,
        )
        self.assertIsNotNone(match)
        return match.group(1).decode("utf-8")

    def test_admin_dashboard_requires_login(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/login"))

    def test_login_page_is_not_indexable_and_does_not_expose_credentials(self):
        response = self.client.get("/admin/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"noindex,nofollow,noarchive", response.data)
        self.assertNotIn(b"copyminas-admin", response.data)
        self.assertNotIn(b"test-only-long-password", response.data)

    def test_wrong_credentials_do_not_authenticate(self):
        csrf = self._csrf_from_login()
        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": csrf,
                "username": "wrong",
                "password": "wrong",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("Credenciais inválidas".encode("utf-8"), response.data)

        dashboard = self.client.get("/admin")
        self.assertEqual(dashboard.status_code, 302)

    def test_valid_environment_credentials_open_dashboard(self):
        csrf = self._csrf_from_login()
        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": csrf,
                "username": "copyminas-admin",
                "password": "test-only-long-password",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Visão geral".encode("utf-8"), response.data)
        self.assertIn("Produtos publicados".encode("utf-8"), response.data)
        self.assertIn("Ações rápidas".encode("utf-8"), response.data)
        self.assertNotIn(b"test-only-long-password", response.data)

    def test_logout_requires_csrf_and_clears_session(self):
        csrf = self._csrf_from_login()
        login = self.client.post(
            "/admin/login",
            data={
                "csrf_token": csrf,
                "username": "copyminas-admin",
                "password": "test-only-long-password",
            },
        )
        self.assertEqual(login.status_code, 302)

        dashboard = self.client.get("/admin")
        token_match = re.search(
            rb'name="csrf_token" value="([^"]+)"',
            dashboard.data,
        )
        self.assertIsNotNone(token_match)

        logout = self.client.post(
            "/admin/logout",
            data={"csrf_token": token_match.group(1).decode("utf-8")},
        )
        self.assertEqual(logout.status_code, 302)

        protected = self.client.get("/admin")
        self.assertEqual(protected.status_code, 302)

    def test_admin_without_environment_credentials_is_unavailable(self):
        self.app.config.update(ADMIN_USERNAME="", ADMIN_PASSWORD="")
        response = self.client.get("/admin/login")

        self.assertEqual(response.status_code, 503)
        self.assertIn(
            "Administração não configurada".encode("utf-8"),
            response.data,
        )

    def test_public_pages_do_not_link_to_admin(self):
        for path in ("/", "/home", "/solucoes", "/produtos", "/empresa", "/contato"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertNotIn(b'href="/admin', response.data)


if __name__ == "__main__":
    unittest.main()
