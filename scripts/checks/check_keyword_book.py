#!/usr/bin/env python3
"""키워드북 항목의 플랫폼 한도를 검사한다.

크랙은 항목 본문을 UTF-16 코드 유닛 400자로 자른다. 이모지는 2단위를 차지하므로
파이썬 len() 만 보면 통과처럼 보이다가 플랫폼에서 조용히 잘린다.
키워드 개수(1~5개)와 마침표 상시 트리거 핵도 함께 막는다.

크랙 키워드북은 20항목이 상한이다(단축어 제외). 넘친 뒤쪽 항목은 동기화 때 조용히 빠진다.

키워드북은 직전 모델 발화·현재 유저 발화에 키워드가 보여야 켜진다. 항목의 키워드가 통합
프롬프트·시작 세트·다른 항목 본문 어디에도 없으면 모델이 그 말을 먼저 꺼낼 계기가 없어,
유저가 스포일러를 읽고 직접 쳐야만 켜진다(예: 최종장 '총공세'). 이 경우를 경고한다.
일상어라 모델이 자연히 쓸 말이면 무시해도 된다.

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
MAX_ENTRIES = 20        # 크랙 키워드북 항목 상한 (단축어 제외)
SPEAKER = re.compile(r"^\*\*(.+?)\*\*\|?$")
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


def corpus_for(path: Path) -> str:
    """이 키워드북과 함께 쓰이는 프롬프트·시작 세트 텍스트."""
    build = path.parent
    project = build.parent
    variant = path.stem.replace("keyword-book", "").strip("-")
    prompts = ([build / f"integrated-prompt-{variant}.md"] if variant
               else sorted(build.glob("integrated-prompt*.md")))
    parts = [p.read_text(encoding="utf-8") for p in prompts if p.exists()]
    for name in ("prologue.md", "start-prompt.md"):
        parts += [p.read_text(encoding="utf-8") for p in sorted(project.glob(f"start-sets/*/{name}"))]
        if (build / name).exists():
            parts.append((build / name).read_text(encoding="utf-8"))
    return "\n".join(parts)


def plain_keyword(keyword: str) -> str | None:
    """발화 표기(**이름**|)는 이름으로, 이모지·기호 신호는 None(검사 제외)."""
    m = SPEAKER.match(keyword)
    if m:
        return m.group(1)
    if not re.search(r"[0-9A-Za-z가-힣]", keyword):
        return None
    return keyword


def reach_warnings(path: Path, entries: list[tuple[str, list[str], str]]) -> None:
    corpus = corpus_for(path)
    if not corpus:
        return
    for title, keywords, _ in entries:
        others = "\n".join(body for t, _, body in entries if t != title)
        words = [w for w in (plain_keyword(k) for k in keywords) if w]
        if words and not any(w in corpus or w in others for w in words):
            print(f"WARN {path}:{title}: 도달 불가 — 키워드 {words} 가 프롬프트·시작 세트·"
                  f"다른 항목 어디에도 없어 모델이 먼저 꺼낼 계기가 없습니다 (일상어면 무시)")


def check_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    marks = list(ENTRY.finditer(text))
    if not marks:
        print(f"WARN {path}: 등록 항목(## 제목)이 없습니다")
        return True

    ok = True
    entries: list[tuple[str, list[str], str]] = []
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
            entries.append((title, keywords, body))

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

    if len(entries) > MAX_ENTRIES:
        print(f"FAIL {path}: 키워드북 {len(entries)}개 — 크랙 상한 {MAX_ENTRIES}개. "
              f"뒤쪽 {len(entries) - MAX_ENTRIES}개는 등록되지 않습니다 (항목을 합치세요)")
        ok = False
    reach_warnings(path, entries)

    if ok:
        print(f"PASS {path}: 키워드북 {len(entries)}/{MAX_ENTRIES}개·단축어 포함 {len(marks)}항목, 모두 한도 내")
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
