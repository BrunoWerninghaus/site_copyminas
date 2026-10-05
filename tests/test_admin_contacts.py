import re
import unittest
from datetime import datetime
from unittest.mock import patch

from src.copyminas import create_app


class AdminContactsRouteTestCase(unittest.TestCase):
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

    def _contact(self):
        stamp = datetime(2026, 10, 5, 8, 0)
        return {
            "id": 7,
            "protocol": "CM261005ABCDEF123456",
            "name": "Cliente Teste",
            "company": "Empresa Teste",
            "email": "cliente@example.com",
            "phone": "(35) 99999-9999",
            "city": "Elói Mendes",
            "service_type": "manutencao_impressora",
            "equipment_quantity": 1,
            "preferred_contact": "telefone",
            "message": "Minha impressora precisa de manutenção.",
            "consent_privacy": 1,
            "consent_at": stamp,
            "status": "novo",
            "source": "site",
            "created_at": stamp,
            "updated_at": stamp,
        }

    @patch("src.copyminas.routes.admin.list_contacts")
    def test_contacts_list_shows_workflow_information(self, list_contacts):
        list_contacts.return_value = [self._contact()]

        response = self.client.get("/admin/contatos")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cliente Teste", response.data)
        self.assertIn(b"CM261005ABCDEF123456", response.data)
        self.assertIn("Manutenção de impressora".encode("utf-8"), response.data)
        self.assertIn(b"data-admin-contact-search", response.data)

    @patch("src.copyminas.routes.admin.get_contact")
    def test_contact_detail_shows_private_operational_fields(self, get_contact):
        get_contact.return_value = self._contact()

        response = self.client.get("/admin/contatos/7")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"cliente@example.com", response.data)
        self.assertIn(b"(35) 99999-9999", response.data)
        self.assertIn(b"site", response.data)
        self.assertIn("Atualizar status".encode("utf-8"), response.data)

    @patch("src.copyminas.routes.admin.update_contact_status")
    @patch("src.copyminas.routes.admin.get_contact")
    def test_contact_status_requires_csrf(self, get_contact, update_status):
        get_contact.return_value = self._contact()

        response = self.client.post(
            "/admin/contatos/7/status",
            data={"csrf_token": "invalid", "status": "em_atendimento"},
        )

        self.assertEqual(response.status_code, 400)
        update_status.assert_not_called()

    @patch("src.copyminas.routes.admin.update_contact_status")
    @patch("src.copyminas.routes.admin.get_contact")
    def test_contact_status_updates_with_valid_csrf(self, get_contact, update_status):
        get_contact.return_value = self._contact()
        detail = self.client.get("/admin/contatos/7")
        token = self._csrf(detail)

        response = self.client.post(
            "/admin/contatos/7/status",
            data={
                "csrf_token": token,
                "status": "em_atendimento",
            },
        )

        self.assertEqual(response.status_code, 302)
        update_status.assert_called_once_with(7, "em_atendimento")

    def test_contacts_require_authenticated_session(self):
        other = self.app.test_client()
        response = other.get("/admin/contatos")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/login"))


if __name__ == "__main__":
    unittest.main()
