import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

TOOL = Path(__file__).resolve().parents[1] / "deploy.py"
SPEC = importlib.util.spec_from_file_location("crack_image_deploy", TOOL)
deploy = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(deploy)


class DeployTests(unittest.TestCase):
    def test_convert_preserves_source_and_refuses_existing_target(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "sample.png"
            Image.new("RGB", (32, 32), "white").save(source)

            self.assertEqual(deploy.convert_to_webp(root), 1)
            self.assertTrue(source.is_file())
            self.assertTrue((root / "sample.webp").is_file())
            with self.assertRaises(ValueError):
                deploy.convert_to_webp(root)

    def test_scaffold_gallery_is_opt_in_and_uses_slugs(self):
        cfg = {
            "characters": {"sera": {"ko": "세라", "group": "guild"}},
            "situations": {"normal": {"ko": "기본"}},
            "scenes": {"gate": {"ko": "관문"}},
        }
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "plain"
            root.mkdir()
            deploy.scaffold(cfg, root)
            self.assertTrue((root / "sera" / "README.md").is_file())
            self.assertTrue((root / "_배치표.md").is_file())
            self.assertFalse((root / "index.html").exists())
            self.assertFalse((root / "app.js").exists())
            with self.assertRaises(ValueError):
                deploy.scaffold(cfg, root)

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "gallery"
            (root / "sera").mkdir(parents=True)
            Image.new("RGB", (32, 32), "white").save(root / "sera" / "normal.webp")
            deploy.scaffold(cfg, root, asset_gallery=True)
            self.assertTrue((root / "index.html").is_file())
            app = (root / "app.js").read_text(encoding="utf-8")
            self.assertIn('"id": "sera"', app)
            self.assertIn('"group": "guild"', app)
            self.assertNotIn('"id": "01"', app)


if __name__ == "__main__":
    unittest.main()
