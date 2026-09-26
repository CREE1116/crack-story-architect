import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "check_character_prompts.py"
SPEC = importlib.util.spec_from_file_location("check_character_prompts", TOOL)
cp = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(cp)

GOOD = ("1girl, solo, 1.3::black hair, hime cut::, 1.3::purple eyes, tsurime::, "
        "tall female, medium breasts, long coat, turtleneck, "
        "A charcoal coat hung with a ring of old brass keys.,")


class CharacterPromptTests(unittest.TestCase):
    def run_on(self, chars: list[dict]) -> tuple[bool, str]:
        root = Path(tempfile.mkdtemp())
        (root / "build/assets").mkdir(parents=True)
        (root / "build/assets/characters.json").write_text(json.dumps(chars), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = cp.validate(root)
        return ok, buf.getvalue()

    def test_good_prompt_passes(self):
        ok, out = self.run_on([{"name": "가", "prompt": GOOD, "uc": "lowres, short hair"}])
        self.assertTrue(ok, out)

    def test_missing_file_skips(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertTrue(cp.validate(Path(tempfile.mkdtemp())))
        self.assertIn("SKIP", buf.getvalue())

    def test_extra_key_fails(self):
        ok, out = self.run_on([{"name": "가", "prompt": GOOD, "uc": "", "id": "01"}])
        self.assertFalse(ok)
        self.assertIn("name/prompt/uc", out)

    def test_sentence_with_comma_fails(self):
        bad = GOOD.replace("A charcoal coat hung with a ring of old brass keys.,",
                           "A charcoal coat, hung with keys.,")
        ok, out = self.run_on([{"name": "가", "prompt": bad, "uc": ""}])
        self.assertFalse(ok)
        self.assertIn("끊겼", out)

    def test_last_sentence_needs_period_comma(self):
        ok, out = self.run_on([{"name": "가", "prompt": GOOD.rstrip(","), "uc": ""}])
        self.assertFalse(ok)
        self.assertIn("'.,'", out)

    def test_expression_and_numbers_fail(self):
        bad = GOOD.replace("tall female", "tall female, smile, 24yo, 168cm")
        ok, out = self.run_on([{"name": "가", "prompt": bad, "uc": ""}])
        self.assertFalse(ok)
        self.assertIn("smile", out)
        self.assertIn("숫자", out)

    def test_prompt_uc_conflict_fails(self):
        ok, out = self.run_on([{"name": "가", "prompt": GOOD, "uc": "turtleneck"}])
        self.assertFalse(ok)
        self.assertIn("turtleneck", out)

    def test_too_long_fails(self):
        long = GOOD.replace("long coat", ", ".join(["long coat"] + [f"tag{i}" for i in range(80)]))
        ok, out = self.run_on([{"name": "가", "prompt": long, "uc": ""}])
        self.assertFalse(ok)
        self.assertIn("그림체", out)

    def test_duplicate_hair_group_fails(self):
        ok, out = self.run_on([{"name": "가", "prompt": GOOD, "uc": ""},
                               {"name": "나", "prompt": GOOD.replace("purple", "grey"), "uc": ""}])
        self.assertFalse(ok)
        self.assertIn("헤어 묶음", out)

    def test_secondary_cast_file_checked(self):
        root = Path(tempfile.mkdtemp())
        (root / "build/assets").mkdir(parents=True)
        (root / "build/assets/characters.json").write_text(json.dumps([{"name": "가", "prompt": GOOD, "uc": ""}]), encoding="utf-8")
        (root / "build/assets/characters-stars.json").write_text(json.dumps([{"name": "별", "prompt": GOOD + " smile,", "uc": ""}]), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = cp.validate(root)
        self.assertFalse(ok)
        self.assertIn("characters-stars.json", buf.getvalue())

    def test_uc_expression_warns_only(self):
        ok, out = self.run_on([{"name": "가", "prompt": GOOD, "uc": "smile"}])
        self.assertTrue(ok, out)
        self.assertIn("WARN", out)

    def test_duplicate_tag_warns(self):
        ok, out = self.run_on([{"name": "가", "prompt": GOOD.replace("long coat", "long coat, long coat"), "uc": ""}])
        self.assertTrue(ok, out)
        self.assertIn("두 번", out)


if __name__ == "__main__":
    unittest.main()
