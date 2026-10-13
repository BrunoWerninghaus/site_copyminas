import os
import unittest
from unittest.mock import patch

from src.copyminas import create_app


VALID_CONTACT = {
    "name": "Cliente Teste",
    "company": "Copy Minas",
    "email": "cliente@example.com",
    "phone": "(35) 99999-9999",
    "city": "Eloi Mendes",
    "service_type": "suporte",
    "equipment_quantity": "1",
    "preferred_contact": "email",
    "message": "Solicito um atendimento.",
    "consent_privacy": "1",
}


class ContactAbuseTestCase(unittest.TestCase):
    def setUp(self):
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "development",
                "CONTACT_RATE_LIMIT_COUNT": "3",
                "CONTACT_RATE_WINDOW_SECONDS": "900",
                "CONTACT_MAX_BYTES": "32768",
                "CONTACT_TRUSTED_PROXY_CIDRS": "",
            },
        ), patch("src.copyminas.load_dotenv"):
            self.app = create_app()
        self.app.config.update(TESTING=True, CATALOG_SOURCE="fixture")
        self.client = self.app.test_client()

    @patch("src.copyminas.routes.public.send_contact_notifications")
    @patch("src.copyminas.routes.public.create_contact_request", return_value="CM261013ABCDEF123456")
    def test_rate_limit_prevents_persistence_and_sets_retry_after(self, store, notify):
        for _ in range(3):
            response = self.client.post("/contato/enviar", data=VALID_CONTACT)
            self.assertEqual(response.status_code, 303)

        blocked = self.client.post("/contato/enviar", data=VALID_CONTACT)
        self.assertEqual(blocked.status_code, 429)
        self.assertGreater(int(blocked.headers["Retry-After"]), 0)
        self.assertIn("Muitas tentativas".encode("utf-8"), blocked.data)
        self.assertEqual(store.call_count, 3)
        self.assertEqual(notify.call_count, 3)

    @patch("src.copyminas.routes.public.send_contact_notifications")
    @patch("src.copyminas.routes.public.create_contact_request")
    def test_honeypot_is_not_persisted(self, store, notify):
        response = self.client.post(
            "/contato/enviar", data={**VALID_CONTACT, "website": "bot.example"}
        )
        self.assertEqual(response.status_code, 422)
        store.assert_not_called()
        notify.assert_not_called()
        self.assertIn(b'name="website"', self.client.get("/contato").data)

    @patch("src.copyminas.routes.public.create_contact_request")
    def test_oversize_contact_body_returns_413(self, store):
        response = self.client.post(
            "/contato/enviar", data={**VALID_CONTACT, "message": "a" * 40_000}
        )
        self.assertEqual(response.status_code, 413)
        store.assert_not_called()

    @patch("src.copyminas.routes.public.send_contact_notifications")
    @patch("src.copyminas.routes.public.create_contact_request", return_value="CM261013ABCDEF123456")
    def test_untrusted_forwarded_header_cannot_reset_limit(self, store, notify):
        for index in range(3):
            response = self.client.post(
                "/contato/enviar",
                data=VALID_CONTACT,
                headers={"CF-Connecting-IP": f"198.51.100.{index + 1}"},
            )
            self.assertEqual(response.status_code, 303)
        blocked = self.client.post(
            "/contato/enviar",
            data=VALID_CONTACT,
            headers={"CF-Connecting-IP": "198.51.100.99"},
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(store.call_count, 3)

    @patch("src.copyminas.routes.public.send_contact_notifications")
    @patch("src.copyminas.routes.public.create_contact_request", return_value="CM261013ABCDEF123456")
    def test_explicitly_trusted_local_proxy_uses_cloudflare_client_ip(self, store, notify):
        with patch.dict(
            os.environ, {"CONTACT_TRUSTED_PROXY_CIDRS": "127.0.0.1/32"}
        ), patch("src.copyminas.load_dotenv"):
            app = create_app()
        app.config.update(TESTING=True, CATALOG_SOURCE="fixture")
        client = app.test_client()
        for i in range(3):
            self.assertEqual(
                client.post(
                    "/contato/enviar",
                    data=VALID_CONTACT,
                    headers={"CF-Connecting-IP": "198.51.100.8"},
                ).status_code,
                303,
            )
        self.assertEqual(
            client.post(
                "/contato/enviar",
                data=VALID_CONTACT,
                headers={"CF-Connecting-IP": "198.51.100.9"},
            ).status_code,
            303,
        )
        self.assertEqual(store.call_count, 4)


if __name__ == "__main__":
    unittest.main()
