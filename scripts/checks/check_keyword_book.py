#!/usr/bin/env python3
"""키워드북 항목의 플랫폼 한도를 검사한다.

크랙은 항목 본문을 UTF-16 코드 유닛 400자로 자른다. 이모지는 2단위를 차지하므로
파이썬 len() 만 보면 통과처럼 보이다가 플랫폼에서 조용히 잘린다.
키워드 개수(1~5개)와 마침표 상시 트리거 핵도 함께 막는다.

사용:
    check_keyword_book.py PROJECT_DIR
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):
    pass

MAX_BODY = 400          # UTF-16 코드 유닛
MAX_KEYWORDS = 5
MAX_SHORTCUT_NAME = 10
MAX_SHORTCUT_DESC = 30
ENTRY = re.compile(r"^##[ \t]+(?P<title>.+?)[ \t]*$", re.MULTILINE)


def measure(text: str) -> int:
    """플랫폼이 실제로 세는 길이. 코드포인트와 UTF-16 중 큰 쪽을 쓴다."""
    return max(len(text), len(text.encode("utf-16-le")) // 2)


def body_of(block: str) -> str:
    for marker in ("- 내용:", "- prompt:"):
        at = block.find(marker)
        if at >= 0:
            return block[at + len(marker):].strip()
    return ""


def check_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    marks = list(ENTRY.finditer(text))
    if not marks:
        print(f"WARN {path}: 등록 항목(## 제목)이 없습니다")
        return True

    ok = True
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        title = mark.group("title")
        block = text[mark.end():end]

        body = body_of(block)
        if not body:
            print(f"FAIL {path}:{title}: 본문(- 내용: / - prompt:)이 없습니다")
            ok = False
            continue
        size = measure(body)
        if size > MAX_BODY:
            print(f"FAIL {path}:{title}: 본문 {size}/{MAX_BODY}자 (UTF-16)")
            ok = False

        kw_line = re.search(r"^- 키워드:[ \t]*(.+)$", block, re.MULTILINE)
        if kw_line:
            keywords = [k.strip() for k in kw_line.group(1).split(",") if k.strip()]
            if not 1 <= len(keywords) <= MAX_KEYWORDS:
                print(f"FAIL {path}:{title}: 키워드 {len(keywords)}개 (1~{MAX_KEYWORDS}개)")
                ok = False
            for keyword in keywords:
                if keyword == "." or keyword.startswith("."):
                    print(f"FAIL {path}:{title}: 마침표 상시 트리거 핵 금지 — {keyword!r}")
                    ok = False

        name = re.search(r"^- name:[ \t]*(.+)$", block, re.MULTILINE)
        if name:
            value = name.group(1).strip()
            if value.startswith("/"):
                print(f"FAIL {path}:{title}: 단축어 이름에 슬래시 금지 — {value!r}")
                ok = False
            if measure(value) > MAX_SHORTCUT_NAME:
                print(f"FAIL {path}:{title}: 단축어 이름 {measure(value)}/{MAX_SHORTCUT_NAME}자")
                ok = False
        desc = re.search(r"^- description:[ \t]*(.+)$", block, re.MULTILINE)
        if desc and measure(desc.group(1).strip()) > MAX_SHORTCUT_DESC:
            print(f"FAIL {path}:{title}: 단축어 설명 "
                  f"{measure(desc.group(1).strip())}/{MAX_SHORTCUT_DESC}자")
            ok = False

    if ok:
        print(f"PASS {path}: 항목 {len(marks)}개, 모두 한도 내")
    return ok


def validate(project: Path) -> bool:
    books = sorted((project / "build").glob("keyword-book*.md"))
    if not books:
        print(f"SKIP {project}: 키워드북 없음")
        return True
    return all([check_file(book) for book in books])


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0 if len(sys.argv) == 2 else 2
    try:
        return 0 if validate(Path(sys.argv[1])) else 1
    except (OSError, UnicodeError) as exc:
        print(f"FAIL keyword book validation: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
