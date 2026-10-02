import unittest
from unittest.mock import MagicMock, patch

from src.copyminas import create_app
from src.copyminas.notifications import send_contact_notifications


class ContactNotificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            SMTP_HOST="smtp.example.test",
            SMTP_PORT=587,
            SMTP_SECURITY="starttls",
            SMTP_USER="ti.processos@copyminas.com.br",
            SMTP_PASSWORD="test-password",
            CONTACT_NOTIFICATION_FROM="ti.processos@copyminas.com.br",
            CONTACT_NOTIFICATION_TO="ti.processos@copyminas.com.br",
            CONTACT_SERVICE_LABELS={
                "suporte": "Suporte",
            },
            CONTACT_PREFERENCE_LABELS={
                "email": "E-mail",
            },
        )
        self.data = {
            "name": "Cliente Teste",
            "company": "Empresa Teste",
            "email": "cliente@example.com",
            "phone": "(35) 99999-9999",
            "city": "Elói Mendes",
            "service_type": "suporte",
            "equipment_quantity": 2,
            "preferred_contact": "email",
            "message": "Preciso de ajuda com meu equipamento.",
        }

    @patch("src.copyminas.notifications.smtplib.SMTP")
    def test_sends_internal_and_customer_messages(self, smtp_class):
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        smtp.__exit__.return_value = False
        smtp_class.return_value = smtp

        with self.app.app_context():
            send_contact_notifications(
                "CM261002ABCDEF123456",
                self.data,
            )

        self.assertEqual(smtp.send_message.call_count, 2)

        internal = smtp.send_message.call_args_list[0].args[0]
        customer = smtp.send_message.call_args_list[1].args[0]

        self.assertEqual(internal["From"], "ti.processos@copyminas.com.br")
        self.assertEqual(internal["To"], "ti.processos@copyminas.com.br")
        self.assertEqual(internal["Reply-To"], "cliente@example.com")

        self.assertEqual(customer["From"], "ti.processos@copyminas.com.br")
        self.assertEqual(customer["To"], "cliente@example.com")
        self.assertIn("CM261002ABCDEF123456", customer.get_content())
        self.assertIn("Suporte", customer.get_content())
        self.assertNotIn("main_bd", customer.get_content())
        self.assertNotIn("contatos", customer.get_content())
        self.assertNotIn("Status inicial", customer.get_content())


if __name__ == "__main__":
    unittest.main()
