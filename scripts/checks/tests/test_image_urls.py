import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "check_image_urls.py"
SPEC = importlib.util.spec_from_file_location("check_image_urls", TOOL)
urls = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(urls)

BASE = "https://example.pages.dev"


class ImageUrlTests(unittest.TestCase):
    def make(self, prologue: str) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "build/assets").mkdir(parents=True)
        (root / "start-sets/01_default").mkdir(parents=True)
        (root / "build/assets/pages-bundle.json").write_text(
            json.dumps({"base_url": BASE, "files": {"banner.webp": "banner.webp"}}), encoding="utf-8")
        (root / "build/assets/image-codes.json").write_text(json.dumps({
            "characters": {"01": {"name": "가", "codes": ["s00", "s01"]}},
            "backgrounds": {"bg01": "로비"},
            "extras": {"ray": {"r01e": "출현"}},
        }), encoding="utf-8")
        (root / "start-sets/01_default/prologue.md").write_text(prologue, encoding="utf-8")
        return root

    def run_check(self, root: Path) -> tuple[bool, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = urls.validate(root)
        return ok, buf.getvalue()

    def test_known_paths_pass(self):
        text = (f"![a]({BASE}/bg/bg01.webp)\n![b]({BASE}/01/s01.webp)\n"
                f"![c]({BASE}/ray/r01e.webp)\n[![d]({BASE}/banner.webp)]({BASE})")
        ok, out = self.run_check(self.make(text))
        self.assertTrue(ok, out)
        self.assertIn("4개", out)

    def test_missing_code_fails(self):
        ok, out = self.run_check(self.make(f"![x]({BASE}/01/s12.webp)"))
        self.assertFalse(ok)
        self.assertIn("01/s12.webp", out)

    def test_template_placeholders_are_skipped(self):
        ok, _ = self.run_check(self.make(f"![img]({BASE}/식별번호/코드.webp)"))
        self.assertTrue(ok)

    def test_skip_without_bundle(self):
        root = Path(tempfile.mkdtemp())
        ok, out = self.run_check(root)
        self.assertTrue(ok)
        self.assertIn("SKIP", out)


if __name__ == "__main__":
    unittest.main()
