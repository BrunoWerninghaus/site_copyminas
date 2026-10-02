import unittest
from unittest.mock import MagicMock, patch

from src.copyminas import create_app
from src.copyminas.catalog import (
    _parse_specifications,
    get_product_by_slug,
    get_public_categories,
    get_public_products,
)
from src.copyminas.db import DatabaseUnavailable


class CatalogDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, CATALOG_SOURCE="database")

    def _connection_for(self, rows):
        connection = MagicMock()
        cursor = MagicMock()
        cursor.__enter__.return_value = cursor
        cursor.__exit__.return_value = False
        cursor.fetchall.return_value = rows
        connection.cursor.return_value = cursor
        return connection, cursor

    def test_database_catalog_reads_existing_main_bd_tables(self):
        rows = [
            {
                "id": 19,
                "nome": "Brother DCP-8157DN — Multifuncional Laser Monocromática Duplex com Rede",
                "descricao": "Multifuncional para escritórios.",
                "imagem1": "images/products/brother.webp",
                "imagem2": "",
                "imagem3": None,
                "imagem4": None,
                "imagem5": None,
                "espec": '["Tipo: Laser monocromática", "Duplex: Automático"]',
                "qtd": 2,
                "categoria_id": 1,
                "categoria": "Impressoras",
            }
        ]
        connection, cursor = self._connection_for(rows)

        with self.app.app_context(), patch(
            "src.copyminas.catalog.open_database",
            return_value=connection,
        ):
            products = get_public_products()
            categories = get_public_categories(products)

        self.assertEqual(len(products), 1)
        product = products[0]
        self.assertEqual(product["id"], 19)
        self.assertEqual(product["category"], "Impressoras")
        self.assertEqual(product["source_quantity"], 2)
        self.assertEqual(product["image_url"], "images/products/brother.webp")
        self.assertEqual(
            product["specifications"],
            ["Tipo: Laser monocromática", "Duplex: Automático"],
        )
        self.assertEqual(product["slug"], "brother-dcp-8157dn")
        self.assertTrue(product["featured"])
        self.assertEqual(categories, [{"id": 1, "name": "Impressoras", "active": True}])

        sql = cursor.execute.call_args.args[0]
        self.assertIn("FROM produtos AS p", sql)
        self.assertIn("INNER JOIN categorias AS c", sql)
        self.assertIn("p.ativo = 1", sql)
        self.assertIn("c.ativo = 1", sql)
        connection.close.assert_called_once()

    def test_product_slug_lookup_uses_database_content(self):
        rows = [
            {
                "id": 19,
                "nome": "Brother DCP-8157DN — Multifuncional Laser Monocromática Duplex com Rede",
                "descricao": "Descrição atualizada no banco.",
                "imagem1": "",
                "imagem2": "",
                "imagem3": "",
                "imagem4": "",
                "imagem5": "",
                "espec": "Velocidade: 40 ppm\nDuplex: Sim",
                "qtd": None,
                "categoria_id": 1,
                "categoria": "Impressoras",
            }
        ]
        connection, _cursor = self._connection_for(rows)

        with self.app.app_context(), patch(
            "src.copyminas.catalog.open_database",
            return_value=connection,
        ):
            product = get_product_by_slug("brother-dcp-8157dn")

        self.assertIsNotNone(product)
        self.assertEqual(product["description"], "Descrição atualizada no banco.")
        self.assertEqual(
            product["specifications"],
            ["Velocidade: 40 ppm", "Duplex: Sim"],
        )

    def test_specification_parser_accepts_json_dict_and_plain_lines(self):
        self.assertEqual(
            _parse_specifications('{"Memória": "8 GB", "Disco": "SSD"}'),
            ["Memória: 8 GB", "Disco: SSD"],
        )
        self.assertEqual(
            _parse_specifications("Memória: 8 GB\nDisco: SSD"),
            ["Memória: 8 GB", "Disco: SSD"],
        )

    def test_database_failure_is_not_silently_replaced_by_fixture(self):
        with self.app.app_context(), patch(
            "src.copyminas.catalog.open_database",
            side_effect=DatabaseUnavailable("offline"),
        ):
            with self.assertRaises(DatabaseUnavailable):
                get_public_products()


if __name__ == "__main__":
    unittest.main()
