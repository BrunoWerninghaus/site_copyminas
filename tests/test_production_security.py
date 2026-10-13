import os
import unittest
from unittest.mock import MagicMock, patch

from src.copyminas import create_app
from src.copyminas.notifications import ContactNotificationError, send_contact_notifications


class ProductionSecurityTestCase(unittest.TestCase):
    def _prod_env(self, **updates):
        values = {
            "APP_ENV": "production",
            "SECRET_KEY": "unique-production-secret-" + "x" * 40,
            "SMTP_SECURITY": "starttls",
            "FLASK_DEBUG": "0",
        }
        values.update(updates)
        return patch.dict(os.environ, values)

    def test_missing_production_secret_fails_closed(self):
        with self._prod_env(SECRET_KEY=""), patch("src.copyminas.load_dotenv"):
            with self.assertRaisesRegex(RuntimeError, "SECRET_KEY"):
                create_app()

    def test_published_development_secret_fails_closed(self):
        with self._prod_env(SECRET_KEY="copyminas-dev-only-change-me"), patch(
            "src.copyminas.load_dotenv"
        ):
            with self.assertRaisesRegex(RuntimeError, "SECRET_KEY"):
                create_app()

    def test_plaintext_smtp_in_production_fails_closed(self):
        with self._prod_env(SMTP_SECURITY="none"), patch("src.copyminas.load_dotenv"):
            with self.assertRaisesRegex(RuntimeError, "SMTP"):
                create_app()

    def test_debug_mode_in_production_fails_closed(self):
        with self._prod_env(FLASK_DEBUG="1"), patch("src.copyminas.load_dotenv"):
            with self.assertRaisesRegex(RuntimeError, "FLASK_DEBUG"):
                create_app()

    def test_production_cookie_and_response_headers(self):
        with self._prod_env(), patch("src.copyminas.load_dotenv"):
            app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.get("/admin/login")
        self.assertEqual(response.status_code, 503)
        cookie = response.headers.get("Set-Cookie", "")
        for flag in ("Secure", "HttpOnly", "SameSite=Lax"):
            self.assertIn(flag, cookie)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(
            response.headers["Strict-Transport-Security"], "max-age=31536000"
        )

        public = client.get("/solucoes")
        self.assertEqual(public.status_code, 200)
        csp = public.headers["Content-Security-Policy"]
        self.assertIn("script-src 'self' https://cdn.jsdelivr.net", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertNotIn("'unsafe-eval'", csp)

    def test_development_uses_ephemeral_secret_and_nonsecure_cookie(self):
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "development",
                "SECRET_KEY": "",
                "SMTP_SECURITY": "none",
                "FLASK_DEBUG": "0",
            },
        ), patch("src.copyminas.load_dotenv"):
            first, second = create_app(), create_app()
        self.assertNotEqual(first.secret_key, second.secret_key)
        self.assertFalse(first.config["SESSION_COOKIE_SECURE"])
        self.assertNotIn(
            "Strict-Transport-Security",
            first.test_client().get("/solucoes").headers,
        )

    def test_runtime_rejects_plaintext_even_if_config_is_changed(self):
        with self._prod_env(), patch("src.copyminas.load_dotenv"):
            app = create_app()
        app.config["SMTP_SECURITY"] = "none"
        app.config["CONTACT_SERVICE_LABELS"] = {"suporte": "Suporte"}
        app.config["CONTACT_PREFERENCE_LABELS"] = {"email": "E-mail"}
        with app.app_context(), self.assertRaises(ContactNotificationError):
            send_contact_notifications(
                "CM261013A1B2C3D4E5F6",
                {
                    "name": "Cliente",
                    "email": "cliente@example.com",
                    "phone": "(35) 99999-9999",
                    "city": "Eloi Mendes",
                    "service_type": "suporte",
                    "preferred_contact": "email",
                    "message": "Pedido de atendimento.",
                },
            )

    @patch("src.copyminas.notifications.smtplib.SMTP")
    def test_starttls_occurs_before_authentication(self, smtp_class):
        with patch.dict(os.environ, {"APP_ENV": "development", "SMTP_SECURITY": "starttls"}), patch(
            "src.copyminas.load_dotenv"
        ):
            app = create_app()
        app.config["CONTACT_SERVICE_LABELS"] = {"suporte": "Suporte"}
        app.config["CONTACT_PREFERENCE_LABELS"] = {"email": "E-mail"}
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        smtp_class.return_value = smtp
        with app.app_context():
            send_contact_notifications(
                "CM261013A1B2C3D4E5F6",
                {
                    "name": "Cliente",
                    "email": "cliente@example.com",
                    "phone": "(35) 99999-9999",
                    "city": "Eloi Mendes",
                    "service_type": "suporte",
                    "preferred_contact": "email",
                    "message": "Pedido de atendimento.",
                },
            )
        calls = [str(call) for call in smtp.mock_calls]
        self.assertLess(
            next(i for i, call in enumerate(calls) if "starttls" in call),
            next(i for i, call in enumerate(calls) if "login" in call),
        )


if __name__ == "__main__":
    unittest.main()
