#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10"]
# ///
"""시네마틱 명함: 배경째 쓴 인물 컷 위에 소속·이름·영문 이름·이능을 조판한다.

name_card.py(누끼형)와 달리 누끼를 뜨지 않는다. 장면 배경이 있는 차분 컷을
확대해 오른쪽에 두고, 왼쪽을 배경색으로 페이드시켜 그 위에 글자를 놓는다.

    uv run tools/images/name_card_cinematic.py img --meta cards.json --out img/명함

--meta 는 JSON 배열이다. 항목마다 name·source·affiliation·ability 가 필수이고
ability_label(기본 "이능")·roman·accent(기본 "#BCD0E4")·id 는 선택이다.
source 는 첫 인수 디렉터리 기준 상대 경로다.

    [{"name": "강연", "source": "강연/차분.png", "affiliation": "하운드 · 길드장",
      "ability": "마킹", "roman": "KANG YEON", "accent": "#E0304A"}]

글꼴(Noto Serif KR·IBM Plex Sans KR·Cinzel, 모두 OFL)은 첫 실행 때
~/.cache/crack-story-fonts 로 내려받는다.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 600
BG = (11, 11, 14)
FONT_CACHE = Path.home() / ".cache" / "crack-story-fonts"
FONTS = {
    "serif": ("NotoSerifKR-VF.ttf", "ofl/notoserifkr/NotoSerifKR%5Bwght%5D.ttf"),
    "sans-medium": ("IBMPlexSansKR-Medium.ttf", "ofl/ibmplexsanskr/IBMPlexSansKR-Medium.ttf"),
    "sans-semibold": ("IBMPlexSansKR-SemiBold.ttf", "ofl/ibmplexsanskr/IBMPlexSansKR-SemiBold.ttf"),
    "latin": ("Cinzel-VF.ttf", "ofl/cinzel/Cinzel%5Bwght%5D.ttf"),
}

# 조판 좌표. 이름 블록(소속~이능)이 카드 세로 중앙에 오도록 맞춘 값이다.
TEXT_X = 76
PORTRAIT_ZOOM = 1.18   # 카드 높이 대비 인물 컷 높이. 머리가 위쪽에 붙고 상반신이 채워진다.
PORTRAIT_CX = 800      # 인물 중심이 놓이는 x. 왼쪽 약 2/3 지점부터 글자 영역이 된다.
# (x, 배경 불투명도). 인물 중심(800) 직전에 0이 되어 얼굴에는 레이어가 닿지 않는다.
FADE = [(0, 255), (330, 250), (640, 60), (820, 0), (W, 0)]


def ensure_fonts() -> dict[str, Path]:
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, (fname, repo_path) in FONTS.items():
        path = FONT_CACHE / fname
        if not path.exists():
            url = f"https://github.com/google/fonts/raw/main/{repo_path}"
            print(f"글꼴 내려받는 중: {fname}", file=sys.stderr)
            urllib.request.urlretrieve(url, path)
        paths[key] = path
    return paths


def load_font(paths: dict[str, Path], key: str, size: int, weight: str | None = None):
    f = ImageFont.truetype(str(paths[key]), size)
    if weight:
        f.set_variation_by_name(weight)
    return f


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tracked(d: ImageDraw.ImageDraw, xy, text: str, font, fill, tracking: float) -> None:
    """자간을 벌려 한 글자씩 그린다. Pillow 는 자간 옵션이 없다."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def horizontal_mask(stops: list[tuple[int, int]]) -> Image.Image:
    row = Image.new("L", (W, 1))
    px = row.load()
    for x in range(W):
        for (x0, a0), (x1, a1) in zip(stops, stops[1:]):
            if x0 <= x <= x1:
                t = (x - x0) / max(1, x1 - x0)
                t = t * t * (3 - 2 * t)
                px[x, 0] = round(a0 + (a1 - a0) * t)
                break
    return row.resize((W, H))


def render(entry: dict, src_root: Path, fonts: dict[str, Path]) -> Image.Image:
    accent = hex_rgb(entry.get("accent", "#BCD0E4"))
    name = entry["name"]

    im = Image.open(src_root / entry["source"]).convert("RGB")
    h = round(H * PORTRAIT_ZOOM)
    im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    left = im.width // 2 - PORTRAIT_CX
    card = Image.new("RGB", (W, H), BG)
    card.paste(im.crop((left, 0, left + W, H)), (0, 0))

    solid = Image.new("RGB", (W, H), BG)
    card.paste(solid, (0, 0), horizontal_mask(FADE))
    vig = Image.new("L", (1, H))
    for y in range(H):
        t = abs(y - H / 2) / (H / 2)
        vig.putpixel((0, y), round(150 * max(0.0, t - 0.55) / 0.45))
    card.paste(solid, (0, 0), vig.resize((W, H)))

    card = card.convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((-260, 120, 360, 640), fill=(*accent, 46))
    card = Image.alpha_composite(card, glow.filter(ImageFilter.GaussianBlur(110)))

    noise = Image.effect_noise((W, H), 22).convert("L")
    card = Image.alpha_composite(card, Image.merge("RGBA", (noise, noise, noise, Image.new("L", (W, H), 14))))

    d = ImageDraw.Draw(card)
    x = TEXT_X
    d.rectangle((x, 176, x + 22, 178), fill=(*accent, 255))
    tracked(d, (x + 34, 162), entry["affiliation"], load_font(fonts, "sans-medium", 22), (206, 206, 214, 255), 1.5)

    name_font = load_font(fonts, "serif", 112 if len(name) <= 3 else 96, "Black")
    d.text((x - 4, 192), name, font=name_font, fill=(246, 244, 240, 255))

    if entry.get("roman"):
        tracked(d, (x, 358), entry["roman"], load_font(fonts, "latin", 24, "Bold"), (*accent, 255), 7)

    d.line((x, 414, x + 300, 414), fill=(255, 255, 255, 46), width=1)
    tracked(d, (x, 440), entry.get("ability_label", "이능"), load_font(fonts, "sans-semibold", 18), (*accent, 255), 3)
    d.text((x + 58, 430), entry["ability"], font=load_font(fonts, "serif", 34, "Bold"), fill=(240, 238, 234, 255))

    m, t = 18, 26
    d.rectangle((m, m, W - m, H - m), outline=(255, 255, 255, 26), width=1)
    for cx, cy, sx, sy in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.line((cx, cy, cx + sx * t, cy), fill=(*accent, 200), width=2)
        d.line((cx, cy, cx, cy + sy * t), fill=(*accent, 200), width=2)

    return card.convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path, help="source 경로의 기준 디렉터리")
    ap.add_argument("--meta", type=Path, required=True, help="카드 목록 JSON 배열")
    ap.add_argument("--out", type=Path, required=True, help="출력 디렉터리")
    ap.add_argument("--overwrite", action="store_true", help="기존 출력 덮어쓰기")
    args = ap.parse_args()

    entries = json.loads(args.meta.read_text(encoding="utf-8"))
    fonts = ensure_fonts()
    args.out.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        missing = [k for k in ("name", "source", "affiliation", "ability") if not entry.get(k)]
        if missing:
            sys.exit(f"필수 항목 누락 {missing}: {entry}")
        out = args.out / f"{entry.get('id') or entry['name']}.png"
        if out.exists() and not args.overwrite:
            print(f"건너뜀(이미 있음): {out}", file=sys.stderr)
            continue
        render(entry, args.src, fonts).save(out, optimize=True)
        print(out)


if __name__ == "__main__":
    main()
