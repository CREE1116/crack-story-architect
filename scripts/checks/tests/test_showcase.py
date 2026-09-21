import importlib.util
from pathlib import Path
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "check_showcase.py"
SPEC = importlib.util.spec_from_file_location("check_showcase", TOOL)
showcase = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(showcase)


def brief_text() -> str:
    return """# 작품 연장형 사이트 설계안

## 1. 작품과 열람 계약
- 작품명: 테스트
- 정본/시작 세트 경로와 기준 버전: story.md / start-sets/01_default
- 한 줄 경험: 방문자가 현장 기록으로 봉쇄 상황을 확인하고 조사 방향을 고른다.
- 문서 작성자 / 말투 / 편향: 현장 기록관 / 건조함 / 기관 관점
- 문서 작성 시점 / 기록이 다루는 시점: Day 1 오전 / Day 1 오전
- 방문자의 기본 열람 권한: 공개 기록 열람 가능
- 플레이어 역할 / 미확정 범위: 신규 조사자 / 이름과 과거는 미확정
- 시작 장소: 북문 검문소
- 시작 상황: 봉쇄 직후 현장 대기
- 첫 행동 후보: 경비에게 질문하거나 주변 흔적을 조사한다.
- 사이트가 확정하지 않는 플레이어 설정: 이름, 성별, 과거
- 열람 후 이해해야 할 시작 상황과 가능한 첫 행동: 봉쇄 원인을 조사할 수 있다.
- 실제 작품 링크 / 미정 여부: 미정

## 2. 공개 정보 장부 — 화면 설계보다 먼저
| 항목 | 정본 근거 위치 | 작성자가 알 수 있는가 | 방문자에게 공개 가능한가 | 사실/관측/소문 | 공개 문구 또는 제외 이유 |
|---|---|---|---|---|---|
| 시작 갈등 | story.md#Opening | 예 | 예 | 관측 | 북문이 봉쇄되어 있다. |

## 3. 형식 선택
"""


class ShowcaseTests(unittest.TestCase):
    def make_project(self, root: Path) -> Path:
        project = root / "project"
        (project / "build" / "assets").mkdir(parents=True)
        (project / "start-sets" / "01_default").mkdir(parents=True)
        (project / "story.md").write_text("# Story\n\n## Opening\n봉쇄", encoding="utf-8")
        (project / "characters.md").write_text("# Characters\n", encoding="utf-8")
        (project / "start-sets" / "01_default" / "start-prompt.md").write_text("시작", encoding="utf-8")
        (project / showcase.BRIEF).write_text(brief_text(), encoding="utf-8")
        return project

    def test_site_requires_stamp_and_detects_source_change(self):
        with tempfile.TemporaryDirectory() as folder:
            project = self.make_project(Path(folder))
            site = project / "site"
            site.mkdir()
            (site / "index.html").write_text("ok", encoding="utf-8")

            self.assertEqual(showcase.check(project), 1)
            self.assertEqual(showcase.write_stamp(project, project / showcase.BRIEF), 0)
            self.assertEqual(showcase.check(project), 0)

            (project / "story.md").write_text("# Story\n\n## Opening\n봉쇄 변경", encoding="utf-8")
            self.assertEqual(showcase.check(project), 1)

    def test_placeholder_and_empty_public_ledger_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            project = self.make_project(Path(folder))
            brief = project / showcase.BRIEF
            text = brief.read_text(encoding="utf-8")
            text = text.replace("방문자가 현장 기록으로 봉쇄 상황을 확인하고 조사 방향을 고른다.", "[방문자]가 [세계 속 매체]를 통해 [공개 상황]을 접하고 [첫 행동]을 고민한다.")
            text = text.replace("| 시작 갈등 | story.md#Opening | 예 | 예 | 관측 | 북문이 봉쇄되어 있다. |", "| 시작 갈등 | story.md#Opening | 예 | 아니오 | 관측 | 제외 |")
            brief.write_text(text, encoding="utf-8")
            errors = showcase.validate_brief(brief)
            self.assertTrue(any("자리표시자" in error for error in errors))
            self.assertTrue(any("공개 가능한 항목" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
