import json
import unittest
from unittest.mock import MagicMock, patch

from src.copyminas import create_app
from src.copyminas.home_content import (
    create_home_news,
    initialize_home_schema,
    set_home_news_active,
    update_home_config,
)


class HomeContentStoreTestCase(unittest.TestCase):
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

    def test_initialize_home_schema_creates_only_home_tables(self):
        connection, cursor = self._connection()
        cursor.fetchone.return_value = None
        default = {
            "hero_kicker": "Copy Minas",
            "hero_title": "Título",
            "hero_summary": "Resumo",
            "primary_cta_label": "Soluções",
            "primary_cta_url": "/solucoes",
            "secondary_cta_label": "Produtos",
            "secondary_cta_url": "/produtos",
        }

        with self.app.app_context(), patch(
            "src.copyminas.home_content.open_database",
            return_value=connection,
        ):
            initialize_home_schema(default, featured_product_ids=[21, 19, 25])

        sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertIn("CREATE TABLE IF NOT EXISTS site_home_config", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS site_home_news", sql)
        self.assertNotIn("ALTER TABLE produtos", sql)
        self.assertNotIn("ALTER TABLE categorias", sql)
        self.assertNotIn("ALTER TABLE contatos", sql)
        connection.commit.assert_called_once()

    def test_update_home_config_serializes_featured_order(self):
        connection, cursor = self._connection()
        cursor.rowcount = 1
        data = {
            "announcement_active": True,
            "announcement_label": "AVISO",
            "announcement_text": "Mensagem",
            "announcement_link_label": "Abrir",
            "announcement_link_url": "/produtos",
            "hero_kicker": "Copy Minas",
            "hero_title": "Título",
            "hero_summary": "Resumo",
            "primary_cta_label": "Soluções",
            "primary_cta_url": "/solucoes",
            "secondary_cta_label": "Produtos",
            "secondary_cta_url": "/produtos",
            "featured_product_ids": [25, 21, 19],
            "show_solutions": True,
            "show_company": False,
            "show_location": True,
        }

        with self.app.app_context(), patch(
            "src.copyminas.home_content.open_database",
            return_value=connection,
        ):
            update_home_config(data)

        sql, params = cursor.execute.call_args.args
        self.assertIn("UPDATE site_home_config", sql)
        self.assertEqual(json.loads(params[12]), [25, 21, 19])
        self.assertEqual(params[13:], (1, 0, 1))
        connection.commit.assert_called_once()

    def test_news_is_archived_by_status_not_deleted(self):
        connection, cursor = self._connection()
        cursor.rowcount = 1

        with self.app.app_context(), patch(
            "src.copyminas.home_content.open_database",
            return_value=connection,
        ):
            set_home_news_active(4, False)

        sql, params = cursor.execute.call_args.args
        self.assertIn("UPDATE site_home_news SET active", sql)
        self.assertNotIn("DELETE", sql.upper())
        self.assertEqual(params, (0, 4))

    def test_create_news_persists_editorial_fields(self):
        connection, cursor = self._connection()
        cursor.lastrowid = 8
        data = {
            "label": "NOVIDADE",
            "title": "Novo serviço",
            "body": "Conteúdo",
            "link_label": "Saiba mais",
            "link_url": "/solucoes",
            "active": True,
            "sort_order": 2,
        }

        with self.app.app_context(), patch(
            "src.copyminas.home_content.open_database",
            return_value=connection,
        ):
            news_id = create_home_news(data)

        self.assertEqual(news_id, 8)
        sql, params = cursor.execute.call_args.args
        self.assertIn("INSERT INTO site_home_news", sql)
        self.assertEqual(params[-2:], (1, 2))


if __name__ == "__main__":
    unittest.main()
