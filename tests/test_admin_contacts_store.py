import unittest
from unittest.mock import MagicMock, patch

from src.copyminas import create_app
from src.copyminas.admin_contacts import (
    AdminContactError,
    contact_summary,
    get_contact,
    list_contacts,
    update_contact_status,
)


class AdminContactsStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)

    def _connection(self):
        connection = MagicMock()
        cursor = MagicMock()
        cursor.__enter__.return_value = cursor
        cursor.__exit__.return_value = False
        connection.cursor.return_value = cursor
        return connection, cursor

    def test_list_contacts_reads_existing_table_without_mutation(self):
        connection, cursor = self._connection()
        cursor.fetchall.return_value = [
            {
                "id": 1,
                "protocol": "CM261002ABCDEF123456",
                "name": "Cliente",
                "status": "novo",
            }
        ]

        with self.app.app_context(), patch(
            "src.copyminas.admin_contacts.open_database",
            return_value=connection,
        ):
            rows = list_contacts()

        self.assertEqual(len(rows), 1)
        sql = cursor.execute.call_args.args[0]
        self.assertIn("FROM contatos", sql)
        self.assertNotIn("DELETE", sql.upper())
        connection.commit.assert_not_called()
        connection.close.assert_called_once()

    def test_get_contact_uses_parameterized_id(self):
        connection, cursor = self._connection()
        cursor.fetchone.return_value = {"id": 7, "protocol": "CMTEST"}

        with self.app.app_context(), patch(
            "src.copyminas.admin_contacts.open_database",
            return_value=connection,
        ):
            row = get_contact(7)

        self.assertEqual(row["id"], 7)
        sql, params = cursor.execute.call_args.args
        self.assertIn("WHERE id = %s", sql)
        self.assertEqual(params, (7,))

    def test_status_update_commits_and_never_deletes(self):
        connection, cursor = self._connection()
        cursor.rowcount = 1

        with self.app.app_context(), patch(
            "src.copyminas.admin_contacts.open_database",
            return_value=connection,
        ):
            update_contact_status(7, "em_atendimento")

        sql, params = cursor.execute.call_args.args
        self.assertIn("UPDATE contatos", sql)
        self.assertNotIn("DELETE", sql.upper())
        self.assertEqual(params, ("em_atendimento", 7))
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()

    def test_invalid_status_is_rejected_before_database_access(self):
        with self.app.app_context(), patch(
            "src.copyminas.admin_contacts.open_database"
        ) as open_database:
            with self.assertRaises(AdminContactError):
                update_contact_status(7, "qualquer_status")

        open_database.assert_not_called()

    def test_contact_summary_reads_workflow_counts(self):
        connection, cursor = self._connection()
        cursor.fetchone.return_value = {
            "total": 12,
            "novos": 4,
            "em_atendimento": 3,
            "convertidos": 2,
        }

        with self.app.app_context(), patch(
            "src.copyminas.admin_contacts.open_database",
            return_value=connection,
        ):
            summary = contact_summary()

        self.assertEqual(summary["total"], 12)
        self.assertEqual(summary["novos"], 4)
        sql = cursor.execute.call_args.args[0]
        self.assertIn("status = 'novo'", sql)
        self.assertIn("status = 'em_atendimento'", sql)


if __name__ == "__main__":
    unittest.main()
