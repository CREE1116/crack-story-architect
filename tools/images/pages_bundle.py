#!/usr/bin/env python3
"""이미지·배너·소개 사이트를 코드명으로 묶어 Cloudflare Pages에 올리고 전수 검증한다.

원본 파일은 건드리지 않는다. 설정 JSON이 정한 대로 한글 파일명을 코드로 바꿔
배포 폴더에 복사하고, 매핑표는 공개 폴더 밖에 남긴다.

    python3 pages_bundle.py build  --config build/assets/pages-bundle.json
    python3 pages_bundle.py deploy --config build/assets/pages-bundle.json --project my-story
    python3 pages_bundle.py verify --config build/assets/pages-bundle.json

코드 규약(기본값):
    <번호>/s00.webp   명함          <번호>/s01~.webp  전연령
    <번호>/a01~.webp  성인          bg/bgNN.webp      배경
    그 밖의 묶음(레이·몬스터 등)은 extras 에 원본 glob → 코드를 적는다.

설정 JSON 예시는 references/hosting-showcase-and-banner.md 참고.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # 변환이 필요할 때만 요구한다
    Image = None

IMAGE_EXT = {".webp", ".png", ".jpg", ".jpeg"}


def nfc(text: str) -> str:
    """macOS 파일명은 NFD로 저장된다. 비교 전에 반드시 NFC로 맞춘다."""
    return unicodedata.normalize("NFC", text)


def load_config(path: Path) -> tuple[dict, Path]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    root = (path.parent / cfg.get("root", ".")).resolve()
    # 설정이 build/assets/ 안에 있으면 프로젝트 루트를 기준으로 삼는다
    if "root" not in cfg and path.parent.name == "assets" and path.parent.parent.name == "build":
        root = path.parent.parent.parent.resolve()
    return cfg, root


def put_image(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".webp":
        shutil.copy2(src, dst)
        return
    if Image is None:
        raise SystemExit("Pillow 가 없어 PNG/JPEG 를 WebP 로 바꿀 수 없습니다: pip install Pillow")
    with Image.open(src) as im:
        im.save(dst, "WEBP", quality=88, method=6)


def build(cfg: dict, root: Path) -> dict:
    out = root / cfg.get("out", "deploy")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    site = cfg.get("site")
    if site and (root / site).is_dir():
        shutil.copytree(root / site, out, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".DS_Store"))
    for dest, src in cfg.get("files", {}).items():
        shutil.copy2(root / src, out / dest)

    mapping: dict = {"characters": {}, "situations": {}, "backgrounds": {}, "extras": {}}
    situations: dict[str, str] = {nfc(k): v for k, v in cfg.get("situations", {}).items()}
    aliases: dict[str, str] = {nfc(k): nfc(v) for k, v in cfg.get("aliases", {}).items()}
    for name, code in situations.items():
        mapping["situations"].setdefault(code, name)

    chars = cfg.get("characters")
    if chars:
        src_root = root / chars["source"]
        dirs = {nfc(p.name): p for p in src_root.iterdir() if p.is_dir()}
        for i, name in enumerate(chars["roster"], 1):
            num = f"{i:02d}"
            if nfc(name) not in dirs:
                raise SystemExit(f"인물 폴더 없음: {src_root / name}")
            have = []
            for f in sorted(dirs[nfc(name)].iterdir()):
                if f.suffix.lower() not in IMAGE_EXT:
                    continue
                stem = aliases.get(nfc(f.stem), nfc(f.stem))
                code = situations.get(stem)
                if code is None:
                    raise SystemExit(f"situations 에 없는 파일: {name}/{f.name} (aliases 로 묶거나 추가)")
                dst = out / num / f"{code}.webp"
                if dst.exists():
                    raise SystemExit(f"코드 충돌: {name}/{code} — 같은 코드로 가는 파일이 둘")
                put_image(f, dst)
                have.append(code)
            mapping["characters"][num] = {"name": name, "codes": sorted(have)}

    bgs = cfg.get("backgrounds")
    if bgs:
        dest = bgs.get("dest", "bg")
        for f in sorted((root / bgs["source"]).iterdir()):
            if f.suffix.lower() not in IMAGE_EXT:
                continue
            code, _, label = nfc(f.stem).partition("_")
            put_image(f, out / dest / f"{code}.webp")
            mapping["backgrounds"][code] = label or code

    for group in cfg.get("extras", []):
        dest = group["dest"]
        for code, spec in group["files"].items():
            pattern = spec["glob"] if isinstance(spec, dict) else spec
            hits = [p for p in root.glob(pattern) if p.suffix.lower() in IMAGE_EXT]
            if len(hits) != 1:
                raise SystemExit(f"extras {dest}/{code}: glob {pattern!r} 결과 {len(hits)}개 (정확히 1개여야 함)")
            put_image(hits[0], out / dest / f"{code}.webp")
            label = spec.get("label", code) if isinstance(spec, dict) else code
            mapping["extras"].setdefault(dest, {})[code] = label

    # 404.html 이 없으면 Pages 가 모든 경로에 index.html(200)을 돌려줘 깨진 코드가 숨는다
    if not (out / "404.html").exists():
        (out / "404.html").write_text("<!doctype html><title>404</title>", encoding="utf-8")
    (out / "_headers").write_text(
        "/*.webp\n  Cache-Control: public, max-age=86400\n  Access-Control-Allow-Origin: *\n",
        encoding="utf-8",
    )
    map_out = root / cfg.get("map_out", "build/assets/image-codes.json")
    map_out.parent.mkdir(parents=True, exist_ok=True)
    map_out.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"{out.relative_to(root)}/ 조립 완료: 파일 {n}개 · 매핑 {map_out.relative_to(root)}")
    return mapping


def mapped_paths(mapping: dict, cfg: dict) -> list[str]:
    paths = [f"{num}/{c}.webp" for num, v in mapping["characters"].items() for c in v["codes"]]
    bg_dest = (cfg.get("backgrounds") or {}).get("dest", "bg")
    paths += [f"{bg_dest}/{c}.webp" for c in mapping["backgrounds"]]
    paths += [f"{dest}/{c}.webp" for dest, codes in mapping["extras"].items() for c in codes]
    paths += list(cfg.get("files", {}))
    return paths


def head(url: str) -> tuple[int, str]:
    # 기본 UA(Python-urllib)는 Cloudflare 가 403 으로 막는다
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0 pages_bundle"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.status, res.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except OSError as exc:
        return 0, str(exc)


def verify(cfg: dict, root: Path) -> bool:
    """GET 이 아니라 HEAD 로 전수 확인한다. 수백 장을 내려받으면 몇 분이 걸린다."""
    base = cfg["base_url"].rstrip("/")
    map_out = root / cfg.get("map_out", "build/assets/image-codes.json")
    mapping = json.loads(map_out.read_text(encoding="utf-8"))
    paths = mapped_paths(mapping, cfg)

    def one(p: str) -> tuple[str, int, str]:
        return (p, *head(f"{base}/{urllib.parse.quote(p)}"))

    with ThreadPoolExecutor(24) as pool:
        results = list(pool.map(one, paths))
    bad = [(p, s, t) for p, s, t in results
           if s != 200 or not (t.startswith("image/") or not p.endswith(".webp"))]
    probe = f"{base}/__missing_probe__/s99.webp"
    status, ctype = head(probe)
    if status == 200:
        bad.append(("(없는 경로)", status, f"{ctype} — 404.html 이 없어 깨진 코드가 200으로 숨습니다"))
    for p, s, t in bad[:20]:
        print(f"FAIL {p}: {s} {t}")
    print(f"{'PASS' if not bad else 'FAIL'} {len(results)}개 확인, 실패 {len(bad)}개")
    return not bad


def deploy(cfg: dict, root: Path, project: str, branch: str) -> int:
    out = root / cfg.get("out", "deploy")
    cmd = ["wrangler", "pages", "deploy", str(out), "--project-name", project,
           "--branch", branch, "--commit-dirty=true"]
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("build", "deploy", "verify"))
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--project", help="deploy: Cloudflare Pages 프로젝트 이름")
    ap.add_argument("--branch", default="main")
    args = ap.parse_args()

    cfg, root = load_config(args.config)
    if args.command == "build":
        build(cfg, root)
        return 0
    if args.command == "deploy":
        if not args.project:
            ap.error("deploy 에는 --project 가 필요합니다")
        build(cfg, root)
        return deploy(cfg, root, args.project, args.branch)
    return 0 if verify(cfg, root) else 1


if __name__ == "__main__":
    sys.exit(main())
