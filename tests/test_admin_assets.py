import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from werkzeug.datastructures import FileStorage

from src.copyminas import create_app
from src.copyminas.admin_assets import (
    AdminAssetError,
    normalize_static_path,
    cleanup_editor_output,
    resolve_editor_source,
    save_edited_product_image,
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

    def test_editor_preserves_original_and_writes_edited_version(self):
        source_relative = "images/products/source.png"
        source_path = Path(self.temp_dir.name) / source_relative
        source_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (64, 64), (255, 255, 255, 255)).save(source_path)

        buffer = io.BytesIO()
        Image.new("RGBA", (1200, 1200), (10, 20, 30, 0)).save(
            buffer,
            format="PNG",
        )
        buffer.seek(0)
        edited_upload = FileStorage(
            stream=buffer,
            filename="produto-editado-1200x1200.png",
            content_type="image/png",
        )

        with self.app.app_context():
            edited, original = save_edited_product_image(
                edited_upload,
                source_relative,
                21,
                1,
            )

            self.assertTrue(edited.startswith("images/products/edited/"))
            self.assertTrue(original.startswith("images/products/originals/"))
            self.assertTrue(static_asset_exists(edited))
            self.assertTrue(static_asset_exists(original))
            self.assertEqual(resolve_editor_source(edited), original)

            edited_path = Path(self.temp_dir.name) / edited
            metadata_path = edited_path.with_suffix(edited_path.suffix + ".json")
            self.assertTrue(metadata_path.is_file())

            cleanup_editor_output(edited)
            self.assertFalse(edited_path.exists())
            self.assertFalse(metadata_path.exists())
            self.assertTrue((Path(self.temp_dir.name) / original).exists())

    def test_editor_rejects_non_square_export(self):
        source_relative = "images/products/source.png"
        source_path = Path(self.temp_dir.name) / source_relative
        source_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (64, 64), (255, 255, 255, 255)).save(source_path)

        buffer = io.BytesIO()
        Image.new("RGBA", (800, 600), (10, 20, 30, 255)).save(
            buffer,
            format="PNG",
        )
        buffer.seek(0)
        edited_upload = FileStorage(
            stream=buffer,
            filename="produto-editado.png",
            content_type="image/png",
        )

        with self.app.app_context():
            with self.assertRaises(AdminAssetError):
                save_edited_product_image(
                    edited_upload,
                    source_relative,
                    21,
                    1,
                )


if __name__ == "__main__":
    unittest.main()
