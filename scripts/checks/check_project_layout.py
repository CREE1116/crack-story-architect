#!/usr/bin/env python3
"""Validate the two-source Crack project layout and its optional five-file build."""

from __future__ import annotations

import sys
from pathlib import Path

from check_build import validate as validate_build

# 출력이 head 등으로 잘려도 트레이스백 없이 종료한다.
try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):  # Windows 등
    pass

SOURCES = {"story.md", "characters.md"}
BUILD = "build"


def visible_entries(root: Path) -> list[Path]:
    return [entry for entry in root.iterdir() if not entry.name.startswith(".")]


def bundle_sources(root: Path) -> set[str]:
    """build/assets/pages-bundle.json 이 참조하는 원본 폴더의 최상위 이름."""
    import json
    import unicodedata
    cfg_path = root / "build/assets/pages-bundle.json"
    if not cfg_path.exists():
        return set()
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    paths = [cfg.get("site") or "", (cfg.get("characters") or {}).get("source", ""),
             (cfg.get("backgrounds") or {}).get("source", "")]
    paths += list((cfg.get("files") or {}).values())
    for group in cfg.get("extras", []):
        for spec in group.get("files", {}).values():
            paths.append(spec["glob"] if isinstance(spec, dict) else spec)
    return {unicodedata.normalize("NFC", Path(p).parts[0]) for p in paths if p}


def validate(root: Path, require_build: bool = True) -> bool:
    if not root.is_dir():
        print(f"FAIL {root}: project directory not found")
        return False

    entries = visible_entries(root)
    names = {entry.name for entry in entries}
    missing = sorted(name for name in SOURCES if not (root / name).is_file())
    import unicodedata
    # start-sets/ 는 references/start-sets.md 가 정한 정본 위치다. 중간 산출물이
    # 아니라 작성자가 직접 쓰는 원본이므로 허용한다. build/start-sets/ 가 그 생성물이다.
    ALLOWED_ROOT_PREFIXES = tuple(unicodedata.normalize('NFC', p) for p in ("build", "final", "image", "img", "deploy", "output", "assets", "site", "start-sets", "departments", "썸네일", "여캐", "무제"))
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    # 프로젝트 전용 도구 폴더와, pages-bundle.json 이 원본으로 선언한 이미지 폴더는 작업 폴더로 인정한다.
    declared = {"tools"} | bundle_sources(root)
    extras = sorted(
        entry.name for entry in entries
        if entry.name not in SOURCES
        and unicodedata.normalize('NFC', entry.name) not in declared
        and not any(unicodedata.normalize('NFC', entry.name).startswith(p) for p in ALLOWED_ROOT_PREFIXES)
        and entry.suffix.lower() not in IMAGE_EXTS
    )
    ok = True
    if missing:
        print(f"FAIL {root}: missing authored source: {', '.join(missing)}")
        ok = False
    if extras:
        print(f"FAIL {root}: unexpected intermediate artifact: {', '.join(extras)}")
        ok = False

    build = root / BUILD
    if build.exists() and not build.is_dir():
        print(f"FAIL {root}: build must be a directory")
        ok = False
    if require_build and not build.is_dir():
        print(f"FAIL {root}: build directory not found")
        ok = False
    if not ok:
        return False

    print(f"PASS {root}: authored sources are exactly story.md + characters.md")
    if build.is_dir():
        return validate_build(build)
    print("PASS build: not required before first compilation")
    return True


def main() -> int:
    if "-h" in sys.argv or "--help" in sys.argv:
        print("usage: check_project_layout.py STORY_CHAT_DIR [--allow-unbuilt]")
        return 0
    args = sys.argv[1:]
    allow_unbuilt = False
    if "--allow-unbuilt" in args:
        args.remove("--allow-unbuilt")
        allow_unbuilt = True
    if len(args) != 1:
        print("usage: check_project_layout.py STORY_CHAT_DIR [--allow-unbuilt]", file=sys.stderr)
        return 2
    try:
        return 0 if validate(Path(args[0]), require_build=not allow_unbuilt) else 1
    except (OSError, UnicodeError) as exc:
        print(f"FAIL project layout validation: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
