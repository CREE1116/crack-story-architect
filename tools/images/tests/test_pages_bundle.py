import importlib.util
import json
from pathlib import Path
import tempfile
import unicodedata
import unittest

from PIL import Image

TOOL = Path(__file__).resolve().parents[1] / "pages_bundle.py"
SPEC = importlib.util.spec_from_file_location("pages_bundle", TOOL)
pb = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(pb)


def png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), "white").save(path)


class PagesBundleTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        nfd = unicodedata.normalize("NFD", "가나")  # macOS 가 돌려주는 형태
        png(self.root / "img" / nfd / unicodedata.normalize("NFD", "차분.png"))
        png(self.root / "img" / nfd / "명함.png")
        png(self.root / "img" / nfd / "전투2.png")
        png(self.root / "img/배경/bg01_로비.png")
        png(self.root / "mob/늑대/늑대_출현.png")
        (self.root / "site").mkdir()
        (self.root / "site/index.html").write_text("<h1>hi</h1>", encoding="utf-8")
        png(self.root / "banner.png")
        self.cfg = {
            "base_url": "https://x.pages.dev",
            "site": "site",
            "files": {"banner.png": "banner.png"},
            "characters": {"source": "img", "roster": ["가나"]},
            "situations": {"명함": "s00", "차분": "s01", "전투1": "s11"},
            "aliases": {"전투2": "전투1"},
            "backgrounds": {"source": "img/배경"},
            "extras": [{"dest": "mob", "files": {"m01e": "mob/늑대/*_출현.png"}}],
        }

    def test_build_renames_to_codes(self):
        mapping = pb.build(self.cfg, self.root)
        out = self.root / "deploy"
        for rel in ("01/s00.webp", "01/s01.webp", "01/s11.webp", "bg/bg01.webp",
                    "mob/m01e.webp", "index.html", "banner.png", "404.html", "_headers"):
            self.assertTrue((out / rel).exists(), rel)
        self.assertEqual(mapping["characters"]["01"]["codes"], ["s00", "s01", "s11"])
        saved = json.loads((self.root / "build/assets/image-codes.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["backgrounds"], {"bg01": "로비"})
        self.assertIn("m01e", pb.mapped_paths(mapping, self.cfg)[-2] + "".join(pb.mapped_paths(mapping, self.cfg)))

    def test_unknown_situation_stops(self):
        png(self.root / "img/가나/미등록.png")
        with self.assertRaises(SystemExit):
            pb.build(self.cfg, self.root)

    def test_two_files_same_code_stops(self):
        png(self.root / "img/가나/전투1.png")
        with self.assertRaises(SystemExit):
            pb.build(self.cfg, self.root)


if __name__ == "__main__":
    unittest.main()
