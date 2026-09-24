#!/usr/bin/env python3
"""Cut out a character render and compose the Crack cover or the site banner.

    python make_cover.py SRC.png --out output/cover --title "작품명"
    python make_cover.py SRC.png --out output/banner --kind banner --title "작품명" --direct --dpr 2
    ... --vector            vector-trace the cutout instead of embedding the raster
    ... --accent "#3CC4B6"  palette (accent / --bg / --paper) and --cta for the banner button

Needs: pip install "rembg[cpu]" (isnet-anime cutout, skip with --direct), vtracer (--vector only),
Google Chrome or Chromium for rendering (CHROME_PATH to override). Fonts are optional:
put the files listed in fonts/README.md into tools/images/fonts (or CRACK_FONT_DIR).
Render the character on a plain white or flat dark background; chroma screens leave fringes.

Kinds:
    cover   1080x1620 portrait. Crack's cover slot (portrait only, under 5MB) and the site thumbnail.
    banner  1200x400 landscape (--size to change). Clickable banner in the story description
            that links to the worldbuilding site, so it carries the call-to-action line.

Outputs in --out: cutout.png, cutout.svg (--vector), <kind>.svg (editable), <kind>.png, <kind>.webp

The cutout model downloads on first run. Rendering uses headless Chrome.
"""

from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

COVER_SIZE = (1080, 1620)
BANNER_SIZE = (1200, 400)
FONT_DIR = Path(os.environ.get("CRACK_FONT_DIR", Path(__file__).resolve().parent / "fonts"))
CHROME_CANDIDATES = (
    os.environ.get("CHROME_PATH", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "", shutil.which("chromium-browser") or "",
)

BEZEL, TERM, TEAL, PAPER = "#0B0F12", "#11171B", "#3CC4B6", "#EFEBE2"
CTA = "세계관 소개 웹사이트"
DECO_MARK, DECO_CODE = "X", "X  000000  000001"


def cutout(src: Path) -> Image.Image:
    from rembg import new_session, remove

    session = new_session("isnet-anime")
    out = remove(Image.open(src).convert("RGB"), session=session, post_process_mask=True)
    return out.crop(out.getbbox())


def cutout_alpha(img: Image.Image) -> Image.Image:
    """Character silhouette only (L mode), same size as img."""
    from rembg import new_session, remove

    return remove(img.convert("RGB"), session=new_session("isnet-anime"), only_mask=True).convert("L")


def trace(png: Path, svg: Path) -> None:
    import vtracer

    vtracer.convert_image_to_svg_py(
        str(png), str(svg), colormode="color", hierarchical="stacked", mode="spline",
        filter_speckle=4, color_precision=7, layer_difference=12,
        corner_threshold=60, length_threshold=4.0, splice_threshold=45, path_precision=3,
    )


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _defs(w: int, h: int, glow_cx: float, glow_cy: float) -> str:
    faces = (("Cinzel", "", "Cinzel-VF.ttf"), ("Noto Serif KR", "", "NotoSerifKR-VF.ttf"),
             ("IBM Plex Sans KR", "font-weight:600;", "IBMPlexSansKR-SemiBold.ttf"))
    # 없는 폰트는 건너뛰고 시스템 폰트로 대체된다
    fonts = "".join(f"@font-face{{font-family:'{fam}';{wt}src:url('{(FONT_DIR / fn).as_uri()}');}}"
                    for fam, wt, fn in faces if (FONT_DIR / fn).exists())
    return f"""<defs>
    <style>{fonts}</style>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BEZEL}"/><stop offset="1" stop-color="{TERM}"/>
    </linearGradient>
    <radialGradient id="glow" cx="{glow_cx}" cy="{glow_cy}" r="0.55">
      <stop offset="0" stop-color="{TEAL}" stop-opacity="0.42"/>
      <stop offset="0.55" stop-color="{TEAL}" stop-opacity="0.10"/>
      <stop offset="1" stop-color="{TEAL}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">
      <path d="M36 0H0V36" fill="none" stroke="{TEAL}" stroke-opacity="0.07" stroke-width="1"/>
    </pattern>
    <linearGradient id="titlefade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BEZEL}" stop-opacity="0"/><stop offset="0.5" stop-color="{BEZEL}" stop-opacity="0.35"/><stop offset="1" stop-color="{BEZEL}" stop-opacity="0"/>
    </linearGradient>
    <filter id="sparkblur" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="1.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="logoshadow" x="-5%" y="-10%" width="110%" height="130%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="{BEZEL}" flood-opacity="0.9"/>
    </filter>
    <filter id="rim" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="0" stdDeviation="14" flood-color="{TEAL}" flood-opacity="0.55"/>
    </filter>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <rect width="{w}" height="{h}" fill="url(#grid)"/>
  <rect width="{w}" height="{h}" fill="url(#glow)"/>"""


def _frame(w: int, h: int, inset: int, arm: int, labels: tuple[str, str, str, str]) -> str:
    """Terminal-style border: thin inset line, teal corner brackets, tiny status labels."""
    x0, y0, x1, y1 = inset, inset, w - inset, h - inset
    corners = "".join(
        f'<path d="M{x} {y + dy * arm}V{y}H{x + dx * arm}" />'
        for x, y, dx, dy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1))
    )
    tl, tr, bl, br = labels
    fs = max(14, round(w * 0.016))
    pad = inset + fs * 0.9
    return f"""<g id="frame">
    <rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="none" stroke="{PAPER}" stroke-opacity="0.18" stroke-width="1.5"/>
    <g fill="none" stroke="{TEAL}" stroke-width="4" stroke-linecap="square">{corners}</g>
    <g font-family="Cinzel" font-weight="700" font-size="{fs}" fill="{TEAL}" fill-opacity="0.85" letter-spacing="3">
      <text x="{pad:.0f}" y="{y0 + fs * 1.9:.0f}">{tl}</text>
      <text x="{w - pad:.0f}" y="{y0 + fs * 1.9:.0f}" text-anchor="end">{tr}</text>
      <text x="{pad:.0f}" y="{y1 - fs:.0f}">{bl}</text>
      <text x="{w - pad:.0f}" y="{y1 - fs:.0f}" text-anchor="end">{br}</text>
    </g>
  </g>"""


def _logo_or_title(logo: tuple[str, int, int] | None, title: str, x: float, baseline: float,
                   max_w: float, font_size: float, anchor: str) -> str:
    """Place the logo PNG so its bottom sits on the title baseline; fall back to text."""
    if not logo:
        return (f'<text x="{x:.0f}" y="{baseline:.0f}" text-anchor="{anchor}" font-family="Cinzel" font-weight="900" '
                f'font-size="{font_size:.0f}" fill="{PAPER}" letter-spacing="6" stroke="{BEZEL}" stroke-width="10" '
                f'paint-order="stroke">{title}</text>')
    href, lw, lh = logo
    dh = min(font_size * 1.25, max_w * lh / lw)
    dw = dh * lw / lh
    lx = x - dw / 2 if anchor == "middle" else x
    return (f'<image id="logo" href="{href}" x="{lx:.1f}" y="{baseline - dh:.1f}" width="{dw:.1f}" height="{dh:.1f}" '
            f'filter="url(#logoshadow)"/>')


FRAME_LABELS = ("CASE · X", "GRADE —", "MEASURE : NULL", "Lv.0 → 1")


def cover_svg(art_href: str, art_w: int, art_h: int, title: str, line1: str, line2: str,
              logo: tuple[str, int, int] | None = None) -> str:
    w, h = COVER_SIZE
    # Character as large as the frame allows: fill the width, crop at the bottom edge,
    # leave the top ~22% for the title block.
    scale = max(w * 1.02 / art_w, h * 0.80 / art_h)
    cw, ch = art_w * scale, art_h * scale
    cx, cy = (w - cw) / 2, max(h * 0.20, h - ch)
    sub = f'font-family="Noto Serif KR" font-weight="700" letter-spacing="4" stroke="{BEZEL}" paint-order="stroke"'
    if logo:
        # Logo carries the title; the logline sits under it as one line.
        title_block = f"""
    {_logo_or_title(logo, title, w / 2, 352, w * 0.76, 230, "middle")}
    <text x="{w / 2}" y="418" {sub} font-size="38" fill="{PAPER}" stroke-width="8">{line1} {line2}</text>"""
    else:
        title_block = f"""
    <text x="{w / 2}" y="150" {sub} font-size="34" fill="{TEAL}" stroke-width="6">{line1}</text>
    {_logo_or_title(None, title, w / 2, 318, w * 0.80, 170, "middle")}
    <text x="{w / 2}" y="386" {sub} font-size="40" fill="{PAPER}" stroke-width="8">{line2}</text>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  {_defs(w, h, 0.5, 0.58)}
  <clipPath id="inner"><rect x="28" y="28" width="{w - 56}" height="{h - 56}"/></clipPath>
  <image id="character" href="{art_href}" x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" filter="url(#rim)" clip-path="url(#inner)"/>
  <rect x="0" y="{h * 0.14:.0f}" width="{w}" height="{h * 0.16:.0f}" fill="url(#titlefade)"/>
  <g id="title" text-anchor="middle">{title_block}
  </g>
  {_frame(w, h, 28, 90, FRAME_LABELS)}
</svg>
"""


def banner_svg(art_href: str, art_w: int, art_h: int, title: str, line2: str, size: tuple[int, int],
               logo: tuple[str, int, int] | None = None) -> str:
    w, h = size
    # Character on the right, cropped at the bottom edge; text block on the left.
    scale = (h * 1.05) / min(art_h, art_w * 1.1)
    cw, ch = art_w * scale, art_h * scale
    cx, cy = w - cw - w * 0.04, h * 0.06
    tx = w * 0.07
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  {_defs(w, h, 0.78, 0.55)}
  <image id="character" href="{art_href}" x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" filter="url(#rim)"/>
  <g id="title">
    {_logo_or_title(logo, title, tx, h * 0.42, w * 0.46, h * 0.26, "start")}
    <text x="{tx:.0f}" y="{h * 0.56:.0f}" font-family="Noto Serif KR" font-weight="700" font-size="{h * 0.07:.0f}" fill="{PAPER}" fill-opacity="0.8" letter-spacing="2">{line2}</text>
  </g>
  <g id="cta">
    <rect x="{tx:.0f}" y="{h * 0.66:.0f}" width="{h * 0.95:.0f}" height="{h * 0.15:.0f}" rx="{h * 0.075:.0f}" fill="none" stroke="{TEAL}" stroke-width="3"/>
    <text x="{tx + h * 0.475:.0f}" y="{h * 0.765:.0f}" text-anchor="middle" font-family="Noto Serif KR" font-weight="700" font-size="{h * 0.06:.0f}" fill="{TEAL}" letter-spacing="2">{CTA} →</text>
  </g>
  {_frame(w, h, 16, 48, ("", "", "", ""))}
</svg>
"""


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % rgb


def edge_color(img: Image.Image) -> tuple[int, int, int]:
    """Median colour of the image border — the flat background the render was made on."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    px = [rgb.getpixel((x, y)) for x in range(0, w, 8) for y in (0, h - 1)]
    px += [rgb.getpixel((x, y)) for y in range(0, h, 8) for x in (0, w - 1)]
    return tuple(sorted(c[i] for c in px)[len(px) // 2] for i in range(3))


def _fade_mask(mid: str, x: float, y: float, w: float, h: float, sides: str, frac: float = 0.08,
               side_frac: dict[str, float] | None = None) -> str:
    """Soft-edge mask so the render melts into a canvas of the same colour (no cut line)."""
    grads, rects = [], []
    for side in sides:
        gid = f"{mid}_{side}"
        x1, y1, x2, y2 = {"l": (0, 0, 1, 0), "r": (1, 0, 0, 0), "t": (0, 0, 0, 1), "b": (0, 1, 0, 0)}[side]
        grads.append(f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
                     f'<stop offset="0" stop-color="black"/><stop offset="{(side_frac or {}).get(side, frac)}" stop-color="black" stop-opacity="0"/></linearGradient>')
        rects.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{gid})"/>')
    return (f'{"".join(grads)}<mask id="{mid}" maskUnits="userSpaceOnUse">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/>{"".join(rects)}</mask>')


def _deco_back(w: int, h: int, level: int, shift: float, matte: str | None,
               box: tuple[float, float, float, float]) -> str:
    """Background decor drawn over the render but masked out of the character by a soft,
    blurred silhouette — the character itself stays the untouched original."""
    if not level:
        return ""
    bx, by, bw, bh = box
    hole = (f'<image href="{matte}" x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
            f'preserveAspectRatio="none"/>' if matte else "")
    import random
    rnd = random.Random(7)
    sparks = []
    for _ in range(34):
        x, y = rnd.uniform(40, w - 40), rnd.uniform(60, h * 0.78)
        r = rnd.uniform(3, 9)
        op = rnd.uniform(0.25, 0.8)
        sparks.append(f'<rect x="{x - r:.0f}" y="{y - r:.0f}" width="{2 * r:.1f}" height="{2 * r:.1f}" '
                      f'transform="rotate(45 {x:.0f} {y:.0f})" fill="{TEAL}" fill-opacity="{op:.2f}"/>')
    big_x = ""
    if level >= 2:
        big_x = (f'<text x="{w / 2}" y="{h * 0.66 + shift:.0f}" text-anchor="middle" font-family="Cinzel" font-weight="900" '
                 f'font-size="{h * 0.62:.0f}" fill="none" stroke="{TEAL}" stroke-opacity="0.30" stroke-width="4">{DECO_MARK}</text>')
    return f"""<mask id="decohole" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">
    <rect width="{w}" height="{h}" fill="white"/>{hole}
  </mask>
  <g id="deco-back" mask="url(#decohole)">
    <radialGradient id="cacheglow" cx="0.5" cy="{0.36 + shift / h:.3f}" r="0.5">
      <stop offset="0" stop-color="{TEAL}" stop-opacity="0.30"/>
      <stop offset="0.6" stop-color="{TEAL}" stop-opacity="0.06"/>
      <stop offset="1" stop-color="{TEAL}" stop-opacity="0"/>
    </radialGradient>
    <rect width="{w}" height="{h}" fill="url(#cacheglow)"/>
    <rect width="{w}" height="{h}" fill="url(#grid)"/>
    {big_x}
    <g filter="url(#sparkblur)">{"".join(sparks)}</g>
  </g>"""


def _deco_front(w: int, h: int, level: int, shift: float) -> str:
    """Human-readable line under the barcode logo, like a real barcode."""
    if not level:
        return ""
    y = h * 0.925 + shift + 44
    return (f'<text x="{w / 2}" y="{y:.0f}" text-anchor="middle" font-family="IBM Plex Sans KR" font-weight="600" '
            f'font-size="26" fill="{PAPER}" fill-opacity="0.72" letter-spacing="14">{DECO_CODE}</text>')


def direct_cover_svg(art_href: str, art_w: int, art_h: int, canvas: str,
                     logo: tuple[str, int, int] | None, title: str, layout: str = "top",
                     logo_width: float = 0.80, shift: float = 0.0, deco: int = 0,
                     matte: str | None = None) -> str:
    w, h = COVER_SIZE
    if layout == "bottom":
        # Character pushed up and filling the width; lower body melts into black under the logo.
        scale = max(w * 1.08 / art_w, h * 0.86 / art_h)
        cw, ch = art_w * scale, art_h * scale
        cx, cy = (w - cw) / 2, -h * 0.02 + shift
        mask = _fade_mask("fade", cx, cy, cw, ch, "lrb", 0.10, {"b": 0.34})
        title_block = _logo_or_title(logo, title, w / 2, h * 0.925 + shift, w * logo_width, 400, "middle")
    else:
        scale = max(w / art_w, h * 0.78 / art_h)
        cw, ch = art_w * scale, art_h * scale
        cx, cy = (w - cw) / 2, h - ch
        mask = _fade_mask("fade", cx, cy, cw, ch, "lrt", 0.10)
        title_block = _logo_or_title(logo, title, w / 2, 400, w * 0.78, 240, "middle")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>{_defs(w, h, 0.5, 0.5).split("</defs>")[0].split("<defs>")[1]}
    {mask}
    <radialGradient id="vignette" cx="0.5" cy="0.45" r="0.75">
      <stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.45"/>
    </radialGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="{canvas}"/>
  <image id="character" href="{art_href}" x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" mask="url(#fade)"/>
  {_deco_back(w, h, deco, shift, matte, (cx, cy, cw, ch))}
  <rect width="{w}" height="{h}" fill="url(#vignette)"/>
  <g id="title">{title_block}</g>
  {_deco_front(w, h, deco, shift) if layout == "bottom" else ""}
  {_frame(w, h, 28, 90, ("", "", "", ""))}
</svg>
"""


def direct_banner_svg(art_href: str, art_w: int, art_h: int, canvas: str, size: tuple[int, int],
                      logo: tuple[str, int, int] | None, title: str, art_scale: float = 1.0,
                      art_y: float = 0.0) -> str:
    w, h = size
    # art_scale: character height as a multiple of the banner height (>1 crops it); art_y: top offset in banner heights.
    scale = h * art_scale / art_h
    cw, ch = art_w * scale, art_h * scale
    cx, cy = w - cw - w * 0.02, h * art_y
    tx = w * 0.07
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>{_defs(w, h, 0.5, 0.5).split("</defs>")[0].split("<defs>")[1]}
    {_fade_mask("fade", cx, cy, cw, ch, "lr", 0.16)}
  </defs>
  <rect width="{w}" height="{h}" fill="{canvas}"/>
  <image id="character" href="{art_href}" x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" mask="url(#fade)"/>
  <g id="title">{_logo_or_title(logo, title, tx, h * 0.52, w * 0.46, h * 0.30, "start")}</g>
  <g id="cta">
    <rect x="{tx:.0f}" y="{h * 0.64:.0f}" width="{h * 0.95:.0f}" height="{h * 0.15:.0f}" rx="{h * 0.075:.0f}" fill="none" stroke="{TEAL}" stroke-width="3"/>
    <text x="{tx + h * 0.475:.0f}" y="{h * 0.745:.0f}" text-anchor="middle" font-family="Noto Serif KR" font-weight="700" font-size="{h * 0.06:.0f}" fill="{TEAL}" letter-spacing="2">{CTA} →</text>
  </g>
  {_frame(w, h, 16, 48, ("", "", "", ""))}
</svg>
"""


def render(svg: Path, png: Path, size: tuple[int, int], dpr: int = 1) -> None:
    w, h = size
    png.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        # headless Chrome writes the screenshot but may not exit; poll and stop it.
        chrome = next((c for c in CHROME_CANDIDATES if c and Path(c).exists()), None)
        if not chrome:
            raise RuntimeError("Chrome/Chromium not found; set CHROME_PATH")
        proc = subprocess.Popen(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={dpr}",
             f"--user-data-dir={tmp}/profile", f"--window-size={w},{h}", "--virtual-time-budget=5000",
             f"--screenshot={png.resolve()}", svg.resolve().as_uri()],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 60
        last = -1
        while time.monotonic() < deadline:
            if png.exists() and png.stat().st_size == last > 0:
                break
            last = png.stat().st_size if png.exists() else -1
            if proc.poll() is not None and png.exists():
                break
            time.sleep(0.5)
        proc.kill()
        proc.wait()
    if not png.exists():
        raise RuntimeError("Chrome did not produce a screenshot")
    img = Image.open(png).convert("RGB")
    if img.size != (w * dpr, h * dpr):
        img = img.crop((0, 0, w * dpr, h * dpr))
    img.save(png, optimize=True)


def _load_logo(path: Path | None, out: Path) -> tuple[str, int, int] | None:
    if not path:
        return None
    lg = Image.open(path)
    lg = lg.crop(lg.getchannel("A").getbbox()) if lg.mode == "RGBA" else lg
    lg_png = out / "logo.png"
    lg.save(lg_png, optimize=True)
    return (data_uri(lg_png, "image/png"), *lg.size)


def direct_main(args: argparse.Namespace) -> int:
    src = Image.open(args.src).convert("RGB")
    canvas = _hex(edge_color(src))
    if args.keep < 1.0:
        src = src.crop((0, 0, src.width, round(src.height * args.keep)))
    if args.kind == "banner":
        # Trim empty background on the sides so the character reads large in a short banner.
        from PIL import ImageChops
        bg = Image.new("RGB", src.size, edge_color(src))
        box = ImageChops.difference(src, bg).convert("L").point(lambda v: 255 if v > 28 else 0).getbbox()
        if box:
            pad = round(src.width * 0.04)
            src = src.crop((max(0, box[0] - pad), 0, min(src.width, box[2] + pad), src.height))
    if args.dpr > 1:
        src = src.resize((src.width * args.dpr, src.height * args.dpr), Image.LANCZOS)
    art_png = args.out / "art.png"
    src.save(art_png, optimize=True)
    href = data_uri(art_png, "image/png")
    matte = None
    if args.kind == "cover" and args.deco:
        # Inverted, dilated, blurred silhouette: black over the character, white elsewhere.
        from PIL import ImageFilter, ImageOps
        alpha = cutout_alpha(src)
        alpha = alpha.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(src.width / 60))
        matte_png = args.out / "matte.png"
        ImageOps.invert(alpha).save(matte_png, optimize=True)
        matte = data_uri(matte_png, "image/png")
    logo = _load_logo(args.logo, args.out)
    if args.kind == "cover":
        size = COVER_SIZE
        text = direct_cover_svg(href, *src.size, canvas, logo, args.title, args.layout, args.logo_width, args.shift, args.deco, matte)
    else:
        size = tuple(int(v) for v in args.size.lower().split("x")) if args.size else BANNER_SIZE
        text = direct_banner_svg(href, *src.size, canvas, size, logo, args.title, args.art_scale, args.art_y)
    svg = args.out / f"{args.kind}.svg"
    svg.write_text(text, encoding="utf-8")
    png = args.out / f"{args.kind}.png"
    render(svg, png, size, args.dpr)
    Image.open(png).save(args.out / f"{args.kind}.webp", quality=92, method=6)
    mb = png.stat().st_size / 1e6
    print(f"{args.kind} {Image.open(png).size} {mb:.2f}MB canvas {canvas} -> {png}")
    return 1 if args.kind == "cover" and mb >= 5 else 0


def main() -> int:
    global TEAL, BEZEL, PAPER, CTA, DECO_MARK, DECO_CODE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path, help="character render (any background)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--kind", choices=("cover", "banner"), default="cover")
    ap.add_argument("--size", default="", help="banner size WxH (default 1200x400)")
    ap.add_argument("--vector", action="store_true", help="use a vector trace instead of the raster cutout")
    ap.add_argument("--layout", choices=("top", "bottom"), default="top",
                    help="cover: logo on top (character at the bottom) or logo at the bottom (character pushed up)")
    ap.add_argument("--logo-width", type=float, default=0.80, help="bottom layout: logo width as a fraction of the cover")
    ap.add_argument("--shift", type=float, default=0.0, help="bottom layout: move character and logo down by N px")
    ap.add_argument("--art-scale", type=float, default=1.0, help="banner: character height / banner height (>1 crops)")
    ap.add_argument("--art-y", type=float, default=0.0, help="banner: character top offset in banner heights (negative crops the top)")
    ap.add_argument("--dpr", type=int, default=1, help="render at N x resolution (2 = 2400x800 banner)")
    ap.add_argument("--deco", type=int, default=0, choices=(0, 1, 2),
                    help="cover decor: 1 = cache glow, grid, sparks, barcode digits; 2 = also a giant outline X")
    ap.add_argument("--direct", action="store_true",
                    help="no cutout: place the render as-is on a canvas of its own background colour "
                         "(best for renders made on a flat black background; no pasted-on look)")
    ap.add_argument("--title", default="", help="text title (required unless --logo)")
    ap.add_argument("--logo", type=Path, help="transparent logo PNG used instead of the text title")
    ap.add_argument("--keep", type=float, default=1.0,
                    help="keep the top fraction of the cutout (e.g. 0.6 crops a full-body render at the hips)")
    ap.add_argument("--line1", default="", help="cover subtitle line 1 (e.g. first half of the logline)")
    ap.add_argument("--line2", default="", help="cover subtitle line 2 / banner subtitle")
    ap.add_argument("--accent", default=TEAL, help="accent colour (frame, glow, CTA)")
    ap.add_argument("--bg", default=BEZEL, help="background colour")
    ap.add_argument("--paper", default=PAPER, help="text colour")
    ap.add_argument("--cta", default=CTA, help="banner button text")
    ap.add_argument("--deco-mark", default=DECO_MARK, help="--deco 2: giant outline glyph")
    ap.add_argument("--deco-code", default=DECO_CODE, help="--deco: barcode-style digits line")
    args = ap.parse_args()
    if not args.title and not args.logo:
        ap.error("--title or --logo is required")

    TEAL, BEZEL, PAPER, CTA = args.accent, args.bg, args.paper, args.cta
    DECO_MARK, DECO_CODE = args.deco_mark, args.deco_code

    args.out.mkdir(parents=True, exist_ok=True)
    if args.direct:
        return direct_main(args)
    cut = cutout(args.src)
    if args.keep < 1.0:
        cut = cut.crop((0, 0, cut.width, round(cut.height * args.keep)))
        cut = cut.crop(cut.getbbox())
    cut_png = args.out / "cutout.png"
    cut.save(cut_png, optimize=True)

    if args.vector:
        cut_svg = args.out / "cutout.svg"
        trace(cut_png, cut_svg)
        href = data_uri(cut_svg, "image/svg+xml")
    else:
        href = data_uri(cut_png, "image/png")

    logo = None
    if args.logo:
        lg = Image.open(args.logo)
        lg = lg.crop(lg.getchannel("A").getbbox()) if lg.mode == "RGBA" else lg
        lg_png = args.out / "logo.png"
        lg.save(lg_png, optimize=True)
        logo = (data_uri(lg_png, "image/png"), *lg.size)

    if args.kind == "cover":
        size = COVER_SIZE
        text = cover_svg(href, *cut.size, args.title, args.line1, args.line2, logo)
    else:
        size = tuple(int(v) for v in args.size.lower().split("x")) if args.size else BANNER_SIZE
        text = banner_svg(href, *cut.size, args.title, args.line2, size, logo)

    svg = args.out / f"{args.kind}.svg"
    svg.write_text(text, encoding="utf-8")
    png = args.out / f"{args.kind}.png"
    render(svg, png, size)
    Image.open(png).save(args.out / f"{args.kind}.webp", quality=90, method=6)

    mb = png.stat().st_size / 1e6
    print(f"cutout {cut.size} -> {svg}\n{args.kind} {Image.open(png).size} {mb:.2f}MB -> {png}")
    if args.kind == "cover" and mb >= 5:
        print("warning: cover.png is 5MB or larger; Crack will reject it", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
