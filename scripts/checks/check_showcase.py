#!/usr/bin/env python3
"""작품 연장형 소개 사이트의 공개정보 계약과 정본 신선도를 검사한다."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

BRIEF = Path("build/assets/showcase-brief.md")
STAMP = Path("build/assets/showcase-stamp.json")
SITE = Path("site")

REQUIRED_FIELDS = (
    "작품명",
    "정본/시작 세트 경로와 기준 버전",
    "한 줄 경험",
    "문서 작성자 / 말투 / 편향",
    "문서 작성 시점 / 기록이 다루는 시점",
    "방문자의 기본 열람 권한",
    "플레이어 역할 / 미확정 범위",
    "시작 장소",
    "시작 상황",
    "첫 행동 후보",
    "실제 작품 링크 / 미정 여부",
)

PLACEHOLDERS = (
    "[방문자]",
    "[세계 속 매체]",
    "[공개 상황]",
    "[첫 행동]",
    "[정본 위치만]",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def source_snapshot(project: Path, brief: Path) -> dict[str, str]:
    paths = [project / "story.md", project / "characters.md", brief]
    start_root = project / "start-sets"
    if start_root.is_dir():
        paths.extend(sorted(start_root.rglob("*.md")))
    return {
        str(path.relative_to(project)): sha(path)
        for path in paths
        if path.is_file()
    }


def field_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^-\s+([^:]+):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def public_ledger_rows(text: str) -> list[list[str]]:
    match = re.search(r"^## 2\.[^\n]*\n(.*?)(?=^##\s)", text, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    rows: list[list[str]] = []
    for line in match.group(1).splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6 or cells[0] == "항목":
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def is_public(value: str) -> bool:
    low = re.sub(r"\s+", " ", value.casefold()).strip()
    if "비공개" in low or "불가능" in low or low in {"아니오", "no", "n", "x", "×"}:
        return False
    return low in {"예", "yes", "y", "o", "○", "가능", "공개", "공개 가능", "가능함"}


def validate_brief(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    values = field_values(text)
    for key in REQUIRED_FIELDS:
        value = values.get(key, "")
        if not value:
            errors.append(f"필수 항목이 비었습니다: {key}")
        elif any(token in value for token in PLACEHOLDERS):
            errors.append(f"템플릿 자리표시자가 남았습니다: {key}")

    rows = public_ledger_rows(text)
    public_rows = [row for row in rows if is_public(row[3])]
    if not public_rows:
        errors.append("공개 정보 장부에 방문자에게 공개 가능한 항목이 없습니다.")
    for row in public_rows:
        item, source, author_knows, _, evidence_type, wording = row
        missing = [name for name, value in (
            ("항목", item),
            ("정본 근거 위치", source),
            ("작성자 인지", author_knows),
            ("사실/관측/소문", evidence_type),
            ("공개 문구", wording),
        ) if not value]
        if missing:
            errors.append(f"공개 장부 행 `{item or '(이름 없음)'}` 누락: {', '.join(missing)}")
    return errors


def write_stamp(project: Path, brief: Path) -> int:
    errors = validate_brief(brief)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    path = project / STAMP
    path.write_text(
        json.dumps(source_snapshot(project, brief), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"쇼케이스 기준을 기록했습니다: {path}")
    return 0


def check(project: Path) -> int:
    brief = project / BRIEF
    site = project / SITE
    site_exists = site.is_dir() and any(site.iterdir())
    if not brief.is_file() and not site_exists:
        print("PASS 쇼케이스: 미사용")
        return 0
    if not brief.is_file():
        print(f"FAIL 사이트가 있지만 공개정보 설계안이 없습니다: {brief}")
        return 1

    errors = validate_brief(brief)
    if site_exists and not (site / "index.html").is_file():
        errors.append("site/가 있지만 index.html이 없습니다.")

    stamp = project / STAMP
    if stamp.is_file():
        try:
            before = json.loads(stamp.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"showcase-stamp.json을 읽을 수 없습니다: {exc}")
        else:
            after = source_snapshot(project, brief)
            changed = sorted(set(before) | set(after))
            changed = [name for name in changed if before.get(name) != after.get(name)]
            if changed:
                errors.append("쇼케이스 기준 이후 변경됨: " + ", ".join(changed))
    elif site_exists:
        errors.append("사이트가 있지만 showcase-stamp.json이 없습니다. 공개 범위를 확인한 뒤 --stamp 하세요.")
    else:
        print("WARN showcase-stamp.json 없음 — 사이트 구현 전 공개 범위를 확정할 때 --stamp 권장")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS 쇼케이스 공개정보 계약")
    return 0


def main() -> int:
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if len(args) != 1:
        print("usage: check_showcase.py PROJECT_DIR [--stamp]", file=sys.stderr)
        return 2
    project = Path(args[0])
    if not project.is_dir():
        print(f"FAIL {project}: 작품 폴더가 없습니다")
        return 1
    brief = project / BRIEF
    if "--stamp" in sys.argv[1:]:
        if not brief.is_file():
            print(f"FAIL {brief}: showcase-brief.md가 없습니다")
            return 1
        return write_stamp(project, brief)
    return check(project)


if __name__ == "__main__":
    raise SystemExit(main())
