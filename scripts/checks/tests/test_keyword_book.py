import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "check_keyword_book.py"
SPEC = importlib.util.spec_from_file_location("check_keyword_book", TOOL)
kb = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(kb)


def entry(title: str, keywords: str, body: str = "본문") -> str:
    return f"## {title}\n- activation_setting: 전체 시작 설정\n- 키워드: {keywords}\n- 내용:\n{body}\n\n"


def run(project: Path) -> tuple[bool, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = kb.validate(project)
    return ok, buf.getvalue()


class KeywordBookTests(unittest.TestCase):
    def make(self, book: str, prompt: str = "") -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "build").mkdir()
        (root / "build/keyword-book-safe.md").write_text("# KB\n\n" + book, encoding="utf-8")
        (root / "build/integrated-prompt-safe.md").write_text(prompt, encoding="utf-8")
        return root

    def test_more_than_twenty_entries_fails(self):
        book = "".join(entry(f"항목{i}", f"단어{i}") for i in range(21))
        ok, out = run(self.make(book, " ".join(f"단어{i}" for i in range(21))))
        self.assertFalse(ok)
        self.assertIn("상한 20개", out)

    def test_twenty_entries_plus_shortcuts_passes(self):
        book = "".join(entry(f"항목{i}", f"단어{i}") for i in range(20))
        book += "## 요약\n- name: 요약\n- description: 요약한다\n- prompt:\n요약\n"
        ok, _ = run(self.make(book, " ".join(f"단어{i}" for i in range(20))))
        self.assertTrue(ok)

    def test_unreachable_keywords_warn(self):
        book = entry("최종장", "총공세, 복원의 제단") + entry("인물", "**서린**|, 암시장", "관련 없는 본문")
        _, out = run(self.make(book, "서린이 암시장을 안다"))
        self.assertIn("최종장: 도달 불가", out)
        self.assertNotIn("인물: 도달 불가", out)

    def test_keyword_seeded_by_other_entry_is_reachable(self):
        book = entry("최종장", "총공세") + entry("징후", "얼굴을 훑", "위치 특정 시 총공세")
        _, out = run(self.make(book, "레이가 얼굴을 훑는다"))
        self.assertNotIn("도달 불가", out)

    def test_signal_only_entry_is_not_reported(self):
        _, out = run(self.make(entry("교전", "⚔️")))
        self.assertNotIn("도달 불가", out)


if __name__ == "__main__":
    unittest.main()
