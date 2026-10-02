import io
import tempfile
import unittest
from pathlib import Path

from werkzeug.datastructures import FileStorage

from src.copyminas import create_app
from src.copyminas.admin_assets import (
    AdminAssetError,
    normalize_static_path,
    save_product_image,
    static_asset_exists,
)


class AdminAssetsTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.app.static_folder = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upload_saves_safe_product_image(self):
        upload = FileStorage(
            stream=io.BytesIO(b"webp-bytes"),
            filename="Produto Teste.webp",
            content_type="image/webp",
        )

        with self.app.app_context():
            relative = save_product_image(upload)
            self.assertTrue(relative.startswith("images/products/"))
            self.assertTrue(relative.endswith(".webp"))
            self.assertTrue(static_asset_exists(relative))

        self.assertTrue((Path(self.temp_dir.name) / relative).is_file())

    def test_path_traversal_is_rejected(self):
        with self.app.app_context():
            with self.assertRaises(AdminAssetError):
                normalize_static_path("../segredo.txt")

    def test_non_image_extension_is_rejected(self):
        upload = FileStorage(
            stream=io.BytesIO(b"not-an-image"),
            filename="arquivo.exe",
            content_type="application/octet-stream",
        )

        with self.app.app_context():
            with self.assertRaises(AdminAssetError):
                save_product_image(upload)


if __name__ == "__main__":
    unittest.main()
