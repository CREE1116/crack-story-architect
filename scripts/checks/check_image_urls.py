#!/usr/bin/env python3
"""프롤로그·시작 상황·프롬프트·상세설명·댓글에 박힌 이미지 URL이 실제 배포 파일을 가리키는지 본다.

크랙은 깨진 이미지를 아무 표시 없이 빈칸으로 둔다. 코드를 잘못 적거나(엑스에게 없는 s12),
번호를 밀리게 적어도 플레이 전에는 알 수 없다. 네트워크 없이 매핑표로만 대조한다.

필요한 파일 (tools/images/pages_bundle.py 가 만든다):
    build/assets/pages-bundle.json   base_url
    build/assets/image-codes.json    배포된 코드 목록

둘 중 하나라도 없으면 SKIP. `{IMG}/번호/코드` 같은 틀 표기는 검사하지 않는다.

사용:
    check_image_urls.py PROJECT_DIR
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

IMG = re.compile(r"!\[[^\]]*\]\((?P<url>[^)\s]+)\)")
SCAN = ("build/*.md", "build/start-sets/*/*.md", "start-sets/*/*.md",
        "build/assets/story-description.md", "build/assets/summary-comment.md")


def known_paths(project: Path) -> tuple[str, set[str]] | None:
    cfg_path = project / "build/assets/pages-bundle.json"
    map_path = project / "build/assets/image-codes.json"
    if not cfg_path.exists() or not map_path.exists():
        return None
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    base = cfg["base_url"].rstrip("/")
    paths = {f"{n}/{c}.webp" for n, v in mapping.get("characters", {}).items() for c in v["codes"]}
    bg = (cfg.get("backgrounds") or {}).get("dest", "bg")
    paths |= {f"{bg}/{c}.webp" for c in mapping.get("backgrounds", {})}
    paths |= {f"{d}/{c}.webp" for d, codes in mapping.get("extras", {}).items() for c in codes}
    paths |= set(cfg.get("files", {}))
    return base, paths


def validate(project: Path) -> bool:
    known = known_paths(project)
    if known is None:
        print(f"SKIP {project}: pages-bundle.json / image-codes.json 없음")
        return True
    base, paths = known
    ok, seen = True, 0
    files = sorted({p for pattern in SCAN for p in project.glob(pattern)})
    for f in files:
        for line_no, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in IMG.finditer(line):
                url = m.group("url")
                if not url.startswith(base + "/"):
                    continue
                rel = url[len(base) + 1:]
                if not re.fullmatch(r"[\w./-]+", rel, re.ASCII):
                    continue  # 식별번호/코드 같은 틀 표기
                seen += 1
                if rel not in paths:
                    print(f"FAIL {f.relative_to(project)}:{line_no}: 배포에 없는 이미지 — {rel}")
                    ok = False
    if ok:
        print(f"PASS {project}: 이미지 URL {seen}개 모두 배포 목록에 있음")
    return ok


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0 if len(sys.argv) == 2 else 2
    return 0 if validate(Path(sys.argv[1])) else 1


if __name__ == "__main__":
    raise SystemExit(main())
