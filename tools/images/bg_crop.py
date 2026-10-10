#!/usr/bin/env python3
"""배경 이미지 와이드 크롭 & 시네마틱 타이포그래피 배너 생성기.

배경/<지명>.png (또는 배경/<지명>/01.png) → 배경_크롭/<지명>.png (기본 1200x360).
작품 톤앤매너에 맞게 [작은 지역 구분] + [감성적인 명조 지명] + [영문 서브타이틀] 형태로 세련되게 렌더링합니다.

사용법:
  # 기본 실행 (프로젝트 루트에서 실행 시 '배경/' -> '배경_크롭/' 생성)
  python3 tools/images/bg_crop.py

  # 특정 경로 및 옵션 지정
  python3 tools/images/bg_crop.py --src /path/to/배경 --out /path/to/배경_크롭 --places places.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


DEFAULT_PLACES = {
    # 5대 기본 합성 배경
    "야외_낮": ("캠퍼스", "교정", "CAMPUS WALK", 0.5),
    "야외_밤": ("거리", "밤길", "NIGHT STREET", 0.5),
    "실내_낮": ("실내", "라운지", "DAYTIME INDOOR", 0.5),
    "실내_밤": ("실내", "심야", "LATE NIGHT INDOOR", 0.5),
    "수영장": ("휴양지", "수영장", "RESORT POOL", 0.5),
    # 개인 사적 공간
    "자취방": ("원룸", "자취방", "STUDIO ROOM", 0.5),
    # 캠퍼스 & 학원
    "캠퍼스": ("학원", "캠퍼스", "CAMPUS", 0.45),
    "강의실": ("학원", "강의실", "LECTURE ROOM", 0.5),
    "도서관": ("학원", "도서관", "CENTRAL LIBRARY", 0.5),
    # 일상 & 데이트
    "지하철역": ("역사", "지하철역", "METRO STATION", 0.5),
    "카페": ("거리", "카페", "COFFEE & DESSERT", 0.5),
    "스터디카페": ("거리", "스터디카페", "STUDY LOUNGE", 0.5),
    "식당": ("거리", "식당", "DINING TABLE", 0.5),
    "번화가": ("시내", "번화가", "DOWNTOWN", 0.5),
    "쇼핑몰": ("도심", "쇼핑몰", "SHOPPING ATRIUM", 0.5),
    "영화관": ("시네마", "영화관", "MOVIE THEATER", 0.5),
    "공원": ("도심", "공원", "CITY PARK", 0.5),
    "놀이공원": ("테마파크", "놀이공원", "AMUSEMENT PARK", 0.5),
    "한강": ("여의도", "한강공원", "HAN RIVER PARK", 0.5),
    "아쿠아리움": ("도심", "아쿠아리움", "AQUARIUM", 0.5),
    "오락실": ("번화가", "게임센터", "ARCADE", 0.5),
    "바닷가": ("해변", "바닷가", "COASTAL BEACH", 0.5),
    "골목": ("시내", "골목", "ALLEY", 0.5),
    "옥상": ("옥상", "루프탑", "ROOFTOP", 0.5),
    "대학가_술집": ("골목", "술집", "CAMPUS PUB", 0.5),
    "바": ("골목", "바", "COCKTAIL BAR", 0.5),
}


def get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    font_caches = [
        Path.home() / ".cache/crack-story-fonts" / name,
        Path(__file__).resolve().parent / "fonts" / name,
    ]
    for p in font_caches:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass

    # 시스템 폰트 대체
    sys_fonts = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for sp in sys_fonts:
        if os.path.exists(sp):
            try:
                return ImageFont.truetype(sp, size, index=0 if "ttc" in sp else None)
            except Exception:
                pass
    return ImageFont.load_default()


def tracked(d: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, f, fill, track: float) -> float:
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + track
    return x


def crop_wide(im: Image.Image, target_w: int, target_h: int, cy: float) -> Image.Image:
    iw, ih = im.size
    target_ratio = target_w / target_h
    current_ratio = iw / ih

    if current_ratio > target_ratio:
        nw = int(ih * target_ratio)
        nh = ih
        cx = iw // 2
        box = (cx - nw // 2, 0, cx + nw // 2, nh)
    else:
        nw = iw
        nh = int(iw / target_ratio)
        center_y = int(ih * cy)
        top = max(0, min(center_y - nh // 2, ih - nh))
        box = (0, top, nw, top + nh)

    cropped = im.crop(box)
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def add_label(
    img: Image.Image,
    region: str,
    name: str,
    latin: str,
    w: int,
    h: int,
) -> Image.Image:
    img = img.convert("RGBA")

    # 아래·왼쪽 감성 비네팅 (글자 자리만 자연스럽게 어둡게)
    shade = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(h):
        sd.line([(0, y), (w, y)], fill=int(210 * max(0, (y - h * 0.3) / (h * 0.7)) ** 1.3))
    left = Image.new("L", (w, h), 0)
    ImageDraw.Draw(left).ellipse((-int(w * 0.2), int(h * 0.2), int(w * 0.7), int(h * 1.6)), fill=170)
    left = left.filter(ImageFilter.GaussianBlur(int(h * 0.25)))
    mask = ImageChops.lighter(shade, left)
    img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (w, h), c) for c in (10, 12, 18)], mask)))

    d = ImageDraw.Draw(img)
    x = int(w * 0.04)

    # 반응형 폰트 크기 계산
    font_name_size = max(36, int(h * 0.20))
    font_region_size = max(14, int(h * 0.055))
    font_latin_size = max(12, int(h * 0.05))

    f_region = get_font("IBMPlexSansKR-Medium.ttf", font_region_size)
    f_name = get_font("NotoSerifKR-VF.ttf", font_name_size)
    f_latin = get_font("Cinzel-VF.ttf", font_latin_size)

    y_latin = h - int(h * 0.12)
    y_name = y_latin - int(h * 0.06) - font_name_size
    y_region = y_name - int(h * 0.09)

    # 포인트 레드/코랄 라인 + 지역 구분
    d.line([(x, y_region + 11), (x + 24, y_region + 11)], fill=(235, 75, 75, 255), width=3)
    tracked(d, (x + 34, y_region), region, f_region, (225, 225, 230, 255), 2.5)

    # 메인 지명 (대형 명조 지명, 존재감 극대화)
    d.text((x, y_name), name, font=f_name, fill=(255, 255, 255, 255))

    # 영문 서브타이틀
    tracked(d, (x, y_latin), latin, f_latin, (180, 185, 195, 255), 5.0)

    # 얇은 영화풍 외곽 프레임
    m = max(8, int(h * 0.033))
    d.rectangle((m, m, w - m, h - m), outline=(255, 255, 255, 30), width=1)

    return img.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="배경 이미지 와이드 크롭 및 시네마틱 라벨 타이포그래피 생성기")
    parser.add_argument("--src", default="배경", help="소스 배경 폴더 (기본: 배경)")
    parser.add_argument("--out", default="배경_크롭", help="출력 폴더 (기본: 배경_크롭)")
    parser.add_argument("--width", type=int, default=1200, help="출력 너비 (기본: 1200)")
    parser.add_argument("--height", type=int, default=360, help="출력 높이 (기본: 360)")
    parser.add_argument("--places", help="장소 메타데이터 JSON 파일 경로 (옵션)")
    parser.add_argument("--no-label", action="store_true", help="라벨 오버레이 없이 와이드 비율 크롭만 수행")
    args = parser.parse_args()

    src_dir = Path(args.src).resolve()
    out_dir = Path(args.out).resolve()
    w, h = args.width, args.height

    places = dict(DEFAULT_PLACES)
    if args.places and Path(args.places).exists():
        try:
            with open(args.places, "r", encoding="utf-8") as f:
                user_places = json.load(f)
                for k, v in user_places.items():
                    # tuple 형식으로 변환
                    if isinstance(v, list) and len(v) >= 4:
                        places[nfc(k)] = (v[0], v[1], v[2], float(v[3]))
        except Exception as e:
            print(f"⚠️ 장소 메타 JSON 로드 오류 ({e})", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    if not src_dir.exists():
        print(f"소스 폴더 없음: {src_dir}", file=sys.stderr)
        return

    processed = 0
    for item in sorted(src_dir.iterdir()):
        if item.name.startswith("."):
            continue
        stem = nfc(item.stem)
        img_path = None
        if item.is_file() and item.suffix.lower() in [".png", ".jpg", ".webp"]:
            img_path = item
        elif item.is_dir():
            for sub in sorted(item.iterdir()):
                if sub.suffix.lower() in [".png", ".jpg", ".webp"]:
                    img_path = sub
                    break

        if not img_path:
            continue

        meta = places.get(stem, ("장소", stem, stem.replace("_", " ").upper(), 0.5))
        region, name, latin, cy = meta

        try:
            with Image.open(img_path) as im:
                cropped = crop_wide(im, w, h, cy)
                if not args.no_label:
                    result = add_label(cropped, region, name, latin, w, h)
                else:
                    result = cropped.convert("RGB")
                out_path = out_dir / f"{stem}.png"
                result.save(out_path, quality=95)
                processed += 1
                if not args.no_label:
                    print(f"배너 생성 완료: {stem} -> [{region}] {name} ({latin})")
                else:
                    print(f"크롭 완료: {stem}")
        except Exception as e:
            print(f"에러 ({stem}): {e}", file=sys.stderr)

    print(f"\n총 {processed}개 장소 배너 생성 완료: {out_dir}")


if __name__ == "__main__":
    main()
