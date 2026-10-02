import unittest
from unittest.mock import MagicMock, patch

from src.copyminas import create_app
from src.copyminas.admin_catalog import (
    create_product,
    set_product_active,
    update_product,
)


class AdminCatalogStoreTestCase(unittest.TestCase):
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

    def _product_data(self):
        return {
            "nome": "Produto Teste",
            "descricao": "Descrição.",
            "imagem1": "images/products/teste.webp",
            "imagem2": "",
            "imagem3": "",
            "imagem4": "",
            "imagem5": "",
            "espec": "Tipo: Teste",
            "ativo": 1,
            "categoria_id": 1,
            "qtd": 3,
        }

    def test_create_product_commits_existing_schema_insert(self):
        connection, cursor = self._connection()
        cursor.fetchone.return_value = {"id": 1}
        cursor.lastrowid = 99

        with self.app.app_context(), patch(
            "src.copyminas.admin_catalog.open_database",
            return_value=connection,
        ):
            product_id = create_product(self._product_data())

        self.assertEqual(product_id, 99)
        sql_calls = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertTrue(any("INSERT INTO produtos" in sql for sql in sql_calls))
        self.assertFalse(any("DELETE" in sql.upper() for sql in sql_calls))
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        connection.close.assert_called_once()

    def test_update_product_commits_and_never_deletes(self):
        connection, cursor = self._connection()
        cursor.fetchone.return_value = {"id": 1}
        cursor.rowcount = 1

        with self.app.app_context(), patch(
            "src.copyminas.admin_catalog.open_database",
            return_value=connection,
        ):
            update_product(19, self._product_data())

        sql_calls = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertTrue(any("UPDATE produtos" in sql for sql in sql_calls))
        self.assertFalse(any("DELETE" in sql.upper() for sql in sql_calls))
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()

    def test_status_change_is_soft_publication_control(self):
        connection, cursor = self._connection()
        cursor.rowcount = 1

        with self.app.app_context(), patch(
            "src.copyminas.admin_catalog.open_database",
            return_value=connection,
        ):
            set_product_active(19, False)

        sql, params = cursor.execute.call_args.args
        self.assertIn("UPDATE produtos SET ativo", sql)
        self.assertEqual(params, (0, 19))
        connection.commit.assert_called_once()

    def test_failed_write_rolls_back(self):
        connection, cursor = self._connection()
        cursor.fetchone.return_value = {"id": 1}
        cursor.execute.side_effect = [None, RuntimeError("write failed")]

        with self.app.app_context(), patch(
            "src.copyminas.admin_catalog.open_database",
            return_value=connection,
        ):
            with self.assertRaises(Exception):
                create_product(self._product_data())

        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
