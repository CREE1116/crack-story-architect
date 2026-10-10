#!/usr/bin/env python3
"""정밀 스프라이트 누끼(Matte Cutout) 및 시네마틱 광학 배경 합성 파이프라인.

NovelAI 등에서 검정(또는 단색) 배경으로 생성된 캐릭터 스프라이트에서
머리카락 한 올까지 보존하며 잔선과 노이즈를 제거하고, 배경과 자연스럽게 광학 합성합니다.

[파이프라인 단계]
1. 세그멘테이션 마스크 캐싱 (rembg: birefnet-general, isnet-anime)
2. 고해상도 매팅 모델 추론 (BiRefNet_HR-matting, 2048px, MPS/CUDA/CPU)
3. Trimap 생성 + Closed-Form Alpha Matting (pymatting)
   - AI 모션라인/잔선(Stray Stroke) LAB 색차 기반 억제
   - 비네팅/백드롭 노이즈 인페인팅 억제
   - 림 글로우/스모크 억제
   - 화면 경계에서 잘린 손/파트너 등 부주제 복원 (_restore_dropped)
   - 잔털(Wisp) 전경색 체색 보정
4. 시네마틱 광학 배경 합성 (Composite)
   - 선형 광학 디스크 보케 블러 (Linear light gamma 2.2 + 하이라이트 볼 부스트)
   - 노출 보정 (Exposure Lift: 배경 밝기에 맞춘 암부/중간톤 리프팅)
   - 환경색 반영 (Ambient Tint: 씬의 색온도/컬러 캐스트 미세 주입)
   - 라이트 랩 (Light Wrap: 배경 빛이 캐릭터 외곽선으로 번지는 스크린 블렌딩)

사용법:
  # 프로젝트 전체 증분 빌드 (변경된 스프라이트만)
  python3 tools/images/matte_cutout.py --project /path/to/project

  # 강제 전체 빌드
  python3 tools/images/matte_cutout.py --force

  # 특정 캐릭터만 빌드
  python3 tools/images/matte_cutout.py --chars 서유진 한나리

  # HR 모델 생략 (CPU 등 저사양 환경 고속 모드)
  python3 tools/images/matte_cutout.py --no-hr

  # 단일 이미지 단일 배경 합성 CLI
  python3 tools/images/matte_cutout.py composite --fg cutout.png --bg bg.png --out result.png
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import unicodedata
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np


def nfc(t: str) -> str:
    return unicodedata.normalize('NFC', t)


def K(r: int) -> np.ndarray:
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def matte(raw: np.ndarray, u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Closed-form alpha matting with stray/glow suppression and foreground estimation."""
    from pymatting import estimate_alpha_cf, estimate_foreground_ml

    img = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB).astype(np.float64) / 255.0
    core = cv2.morphologyEx((u > 0.9).astype(np.uint8), cv2.MORPH_CLOSE, K(6))
    fg = cv2.erode(core, K(8))
    near = cv2.dilate((u > 0.05).astype(np.uint8), K(14))
    tri = np.full(u.shape, 0.5)
    tri[near == 0] = 0
    tri[fg == 1] = 1

    # Stray strokes: chromatic pixels in unknown band whose colour doesn't match nearby body
    lab = cv2.cvtColor(raw, cv2.COLOR_BGR2LAB).astype(np.float32)
    w = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 12) + 1e-4
    loc_ab = np.dstack([cv2.GaussianBlur(lab[..., i] * fg, (0, 0), 12) / w for i in (1, 2)])
    ab_dist = np.linalg.norm(lab[..., 1:] - loc_ab, axis=2)
    chroma = np.linalg.norm(lab[..., 1:] - 128, axis=2)
    loc_chroma = np.linalg.norm(loc_ab - 128, axis=2)
    stray = (tri == 0.5) & (u < 0.5) & (ab_dist > 14) & ((chroma > 14) | (loc_chroma > 14))
    stray = cv2.dilate(stray.astype(np.uint8), K(2)).astype(bool) & (tri == 0.5)
    tri[stray] = 0

    # Backdrop plate inpainting difference suppression
    q = 0.25
    small = cv2.resize(raw, None, fx=q, fy=q, interpolation=cv2.INTER_AREA)
    hole = cv2.resize(
        (tri > 0).astype(np.uint8) * 255,
        (small.shape[1], small.shape[0]),
        interpolation=cv2.INTER_NEAREST,
    )
    plate = cv2.inpaint(small, cv2.dilate(hole, K(2)), 9, cv2.INPAINT_TELEA)
    plate = cv2.GaussianBlur(cv2.resize(plate, (raw.shape[1], raw.shape[0])), (0, 0), 6)
    diff = np.linalg.norm(raw.astype(np.float32) - plate.astype(np.float32), axis=2)
    tri[(tri == 0.5) & (u < 0.5) & (diff < 12)] = 0

    # Baked-in rim glow / smoke suppression
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY).astype(np.float32)
    detail = cv2.GaussianBlur(np.abs(gray - cv2.GaussianBlur(gray, (0, 0), 2.5)), (0, 0), 1.5)
    dist_fg = cv2.distanceTransform((u < 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    tri[(tri == 0.5) & (u < 0.5) & (detail < 4.0) & (dist_fg > 3)] = 0

    a = np.clip(estimate_alpha_cf(img, tri), 0, 1)
    a = np.clip((a - 0.03) / 0.97, 0, 1)  # faint haze removal

    # Connected components: drop floating specks not attached to main body
    n, lbl, st, _ = cv2.connectedComponentsWithStats((a > 0.08).astype(np.uint8))
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 800]
    a[~np.isin(lbl, keep)] = 0
    F = estimate_foreground_ml(img, a)

    # Edge wisps colour lifting
    solid = cv2.erode((a > 0.97).astype(np.float32), K(2))
    wsum = cv2.GaussianBlur(solid, (0, 0), 10) + 1e-4
    local = np.dstack([cv2.GaussianBlur(F[..., i] * solid, (0, 0), 10) / wsum for i in range(3)])
    weight = (np.clip((0.95 - a) / 0.95, 0, 1) * 0.85 * (wsum > 0.02))[..., None]
    F = F * (1 - weight) + local * weight
    return a, F


def _restore_dropped(raw: np.ndarray, a: np.ndarray) -> np.ndarray:
    """Restore secondary subjects entering from frame edge (e.g., partner's hand) dropped by matting."""
    q = 0.25
    small = cv2.resize(raw, None, fx=q, fy=q, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    not_bg = (a > 0.02) | (gray > 75)
    hole = cv2.resize((not_bg * 255).astype(np.uint8), (small.shape[1], small.shape[0]))
    plate = cv2.inpaint(small, cv2.dilate(hole, K(3)), 9, cv2.INPAINT_TELEA)
    plate = cv2.GaussianBlur(cv2.resize(plate, (raw.shape[1], raw.shape[0])), (0, 0), 6)
    diff = np.linalg.norm(raw.astype(np.float32) - plate.astype(np.float32), axis=2)

    missing = cv2.morphologyEx(((diff > 45) & (a < 0.3)).astype(np.uint8), cv2.MORPH_OPEN, K(3))
    n, lbl, st, _ = cv2.connectedComponentsWithStats(missing)
    h, w = a.shape
    out = a.copy()
    soft = np.clip((diff - 12) / 40, 0, 1)
    body = a > 0.5
    g = gray.astype(np.float32)
    detail = np.abs(g - cv2.GaussianBlur(g, (0, 0), 2.5))
    for i in range(1, n):
        x, y, bw, bh, area = st[i]
        if area < 5000:
            continue
        comp = lbl == i
        touches = x == 0 or y == 0 or x + bw >= w or y + bh >= h
        near = (cv2.dilate(comp.astype(np.uint8), K(6)).astype(bool) & body).any()
        if not (touches and near):
            continue
        if detail[comp].mean() < 3.0:
            continue
        if y > 0.45 * h and y + bh >= h and bw > 1.5 * bh:
            continue
        region = cv2.dilate(comp.astype(np.uint8), K(4)).astype(bool)
        out[region] = np.maximum(out[region], soft[region])
    return out


def _stray_and_lift(raw: np.ndarray, u: np.ndarray, a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Shared post-pass for predicted HR alpha: drop stray strokes, restore dropped subjects, lift wisps."""
    from pymatting import estimate_foreground_ml

    img = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB).astype(np.float64) / 255.0
    fg = cv2.erode((u > 0.9).astype(np.uint8), K(8))
    lab = cv2.cvtColor(raw, cv2.COLOR_BGR2LAB).astype(np.float32)
    w = cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 12) + 1e-4
    loc_ab = np.dstack([cv2.GaussianBlur(lab[..., i] * fg, (0, 0), 12) / w for i in (1, 2)])
    ab_dist = np.linalg.norm(lab[..., 1:] - loc_ab, axis=2)
    chroma = np.linalg.norm(lab[..., 1:] - 128, axis=2)
    loc_chroma = np.linalg.norm(loc_ab - 128, axis=2)
    stray = (u < 0.5) & (a < 0.8) & (ab_dist > 14) & ((chroma > 14) | (loc_chroma > 14))
    a = a.copy()
    a[cv2.dilate(stray.astype(np.uint8), K(2)).astype(bool) & (u < 0.5)] = 0
    a = np.clip((a - 0.02) / 0.98, 0, 1)
    a = _restore_dropped(raw, a)
    n, lbl, st, _ = cv2.connectedComponentsWithStats((a > 0.08).astype(np.uint8))
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 800]
    a[~np.isin(lbl, keep)] = 0
    F = estimate_foreground_ml(img, a)
    solid = cv2.erode((a > 0.97).astype(np.float32), K(2))
    wsum = cv2.GaussianBlur(solid, (0, 0), 10) + 1e-4
    local = np.dstack([cv2.GaussianBlur(F[..., i] * solid, (0, 0), 10) / wsum for i in range(3)])
    wt = (np.clip((0.95 - a) / 0.95, 0, 1) * 0.6 * (wsum > 0.02))[..., None]
    return a, F * (1 - wt) + local * wt


def _stale(dst: Path, *srcs: Path) -> bool:
    return not dst.exists() or any(s.exists() and s.stat().st_mtime > dst.stat().st_mtime for s in srcs)


def update_seg_caches(sprites: list[tuple[str, Path]], seg_caches: dict[str, Path]):
    """Update rembg segmentation caches (birefnet-general & isnet-anime)."""
    for model, cache in seg_caches.items():
        todo = [(src, cache / c / src.name) for c, src in sprites if _stale(cache / c / src.name, src)]
        if not todo:
            continue
        try:
            from rembg import new_session, remove
            from PIL import Image, ImageOps
        except ImportError:
            sys.exit(f'{model}: {len(todo)}장 마스크 갱신에 rembg 필요 (pip install rembg)')
        print(f'[{model}] {len(todo)}장 마스크 추출 시작...', flush=True)
        session = new_session(model)
        for src, dst in todo:
            dst.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(src) as im:
                remove(ImageOps.exif_transpose(im).convert('RGBA'), session=session).save(dst)
        print(f'[{model}] 마스크 추출 완료.', flush=True)


def update_hr_alpha(sprites: list[tuple[str, Path]], hr_cache: Path, hr_model: str = 'ZhengPeng7/BiRefNet_HR-matting'):
    """Run BiRefNet_HR-matting (2048px, MPS/CUDA/CPU) for changed sprites."""
    todo = [(c, f) for c, f in sprites if _stale(hr_cache / c / f.name, f)]
    if not todo:
        return
    try:
        import torch
        from transformers import AutoModelForImageSegmentation
    except ImportError:
        print('⚠️ torch/transformers 미설치: HR 매팅을 건너뛰고 기본 pymatting으로 진행합니다.')
        return

    dev = 'mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'[HR 매팅] {len(todo)}장 정밀 추론 시작 ({dev}, {hr_model})...', flush=True)
    try:
        model = AutoModelForImageSegmentation.from_pretrained(hr_model, trust_remote_code=True).to(dev).eval().float()
    except Exception as e:
        print(f'⚠️ HR 매팅 모델 로드 실패 ({e}): 기본 pymatting으로 대체합니다.')
        return

    mean, std = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])
    t0 = time.time()
    for i, (c, f) in enumerate(todo, 1):
        raw = cv2.imread(str(f))
        if raw is None:
            continue
        h, w = raw.shape[:2]
        x = cv2.resize(cv2.cvtColor(raw, cv2.COLOR_BGR2RGB), (2048, 2048), interpolation=cv2.INTER_CUBIC) / 255.0
        x = torch.from_numpy(((x - mean) / std).transpose(2, 0, 1)).float()[None].to(dev)
        with torch.inference_mode():
            pred = model(x)[-1].sigmoid().cpu().numpy()[0, 0]
        if dev == 'mps':
            torch.mps.synchronize()
            torch.mps.empty_cache()
        elif dev == 'cuda':
            torch.cuda.empty_cache()
        a = cv2.resize(pred, (w, h), interpolation=cv2.INTER_AREA).clip(0, 1)
        dst = hr_cache / c / f.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(dst), (a * 65535).round().astype(np.uint16))
        if i % 10 == 0 or i == len(todo):
            el = time.time() - t0
            rem = el / i * (len(todo) - i)
            print(f'  [{i}/{len(todo)}] 경과 {el:.0f}s, 남은시간 {rem:.0f}s', flush=True)


_GLOBAL_MATTE_CFG = {}

def _process_task(args: tuple[str, Path]) -> tuple[bool, str]:
    cdir, raw_f = args
    cfg = _GLOBAL_MATTE_CFG
    out_dir = cfg['out_dir']
    img_dir = cfg['img_dir']
    hr_cache = cfg['hr_cache']
    seg_caches = cfg['seg_caches']

    try:
        out_f = out_dir / cdir / raw_f.name
        raw = cv2.imread(str(raw_f))
        masks = []
        for cache_path in seg_caches.values():
            seg_f = cache_path / cdir / raw_f.name
            if seg_f.exists():
                m = cv2.imread(str(seg_f), cv2.IMREAD_UNCHANGED)
                if m is not None and m.ndim == 3 and m.shape[2] == 4:
                    masks.append(m[:, :, 3] / 255.0)

        if raw is None:
            return False, f'원본 읽기 실패: {raw_f}'
        if not masks:
            # fallback mask from non-black pixels
            gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
            masks = [(gray > 20).astype(np.float32)]

        u = np.maximum.reduce(masks)
        hr = hr_cache / cdir / raw_f.name
        if hr.exists():
            hr_img = cv2.imread(str(hr), cv2.IMREAD_UNCHANGED)
            if hr_img is not None:
                a, F = _stray_and_lift(raw, u, hr_img / 65535.0)
            else:
                a, F = matte(raw, u)
        else:
            a, F = matte(raw, u)

        bgr = cv2.cvtColor((np.clip(F, 0, 1) * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR)
        a8 = (a * 255).round().astype(np.uint8)
        bgr[a8 == 0] = 0
        out_f.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_f), np.dstack([bgr, a8]))
        return True, f'{cdir}/{raw_f.name}'
    except Exception as e:
        return False, f'{cdir}/{raw_f.name}: {e}'


_BG_CACHE: dict[tuple[str, tuple[int, int]], tuple[np.ndarray, np.ndarray, np.ndarray]] = {}

def bokeh_plate(bg_path: Path, size: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Lens-style bokeh: disc blur in linear light with highlight boost. Returns (plate, ambient, mean)."""
    key = (str(bg_path), size)
    if key in _BG_CACHE:
        return _BG_CACHE[key]
    bg = cv2.imread(str(bg_path))
    if bg is None:
        raise FileNotFoundError(f'배경 이미지를 찾을 수 없습니다: {bg_path}')
    bg = cv2.resize(bg, size, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    lin = bg ** 2.2
    lum = lin @ np.array([0.0722, 0.7152, 0.2126], np.float32)
    boost = 1 + 5 * np.clip((lum - 0.55) / 0.45, 0, 1) ** 2
    r = 9
    disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)).astype(np.float32)
    disc = cv2.GaussianBlur(disc, (3, 3), 0.8)
    disc /= disc.sum()
    blurred = cv2.filter2D(lin * boost[..., None], -1, disc) / cv2.filter2D(boost, -1, disc)[..., None]
    plate = np.clip(blurred, 0, 1) ** (1 / 2.2)
    ambient = cv2.GaussianBlur(plate, (0, 0), 40)
    mean = plate.reshape(-1, 3).mean(0)
    _BG_CACHE[key] = (plate, ambient, mean)
    return _BG_CACHE[key]


def composite_image(fg_rgba: np.ndarray, bg_path: Path) -> np.ndarray:
    """광학 시네마틱 배경 합성 (보케 블러 + exposure lift + ambient tint + light wrap)."""
    h, w = fg_rgba.shape[:2]
    plate, ambient, mean = bokeh_plate(bg_path, (w, h))
    fg = fg_rgba[:, :, :3].astype(np.float32) / 255.0
    a = fg_rgba[:, :, 3].astype(np.float32) / 255.0

    # 1. 노출 리프팅: 배경 밝기에 맞춰 암부/중간톤 부드럽게 상승
    scene_l = float(mean @ np.array([0.114, 0.587, 0.299], np.float32))
    lift = 0.12 + 0.30 * scene_l
    fg = 1.0 - (1.0 - fg) ** (1.0 + lift)

    # 2. 환경색 반영: 배경 평균 색온도/컬러 캐스트 미세 주입
    tint = mean / (mean.mean() + 1e-6)
    fg = fg * (1.0 + 0.10 * (tint - 1.0))

    # 3. 라이트 랩: 배경 빛이 가장자리 실루엣을 타고 스며드는 스크린 블렌딩
    inner = cv2.distanceTransform((a > 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    wrap = (np.clip(1.0 - inner / 4.0, 0, 1) * 0.35 * a)[..., None]
    screen = 1.0 - (1.0 - fg) * (1.0 - ambient)
    fg = fg + wrap * (screen - fg)

    a3 = a[..., None]
    comp = np.clip(fg, 0, 1) * a3 + plate * (1.0 - a3)
    return (comp * 255.0).round().astype(np.uint8)


def _composite_task(args: tuple[Path, Path, Path]) -> tuple[bool, str]:
    fg_f, bg_f, dst = args
    try:
        rgba = cv2.imread(str(fg_f), cv2.IMREAD_UNCHANGED)
        if rgba is None:
            return False, f'전경 읽기 실패: {fg_f}'
        res = composite_image(rgba, bg_f)
        dst.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(dst), res)
        return True, str(dst)
    except Exception as e:
        return False, f'{dst}: {e}'


def scan_sprites(img_dir: Path, chars_filter: list[str] | None = None) -> list[tuple[str, Path]]:
    """Scan character sprites in img_dir: looks for img/<char>/검정/*.png or img/<char>/*.png."""
    sprites = []
    if not img_dir.exists():
        return sprites

    for char_path in sorted(img_dir.iterdir()):
        if not char_path.is_dir() or char_path.name.startswith('.'):
            continue
        cname = nfc(char_path.name)
        if chars_filter and cname not in chars_filter and char_path.name not in chars_filter:
            continue

        black_dir = char_path / '검정'
        target_dir = black_dir if black_dir.exists() else char_path
        for f in sorted(target_dir.glob('*.png')):
            if f.name.startswith('.'):
                continue
            sprites.append((cname, f))
    return sprites


def scan_backgrounds(bg_dir: Path, bg_filter: list[str] | None = None) -> dict[str, Path]:
    """Scan available backgrounds."""
    bgs = {}
    if not bg_dir.exists():
        return bgs

    for p in sorted(bg_dir.iterdir()):
        if p.name.startswith('.'):
            continue
        stem = nfc(p.stem)
        if bg_filter and stem not in bg_filter and p.stem not in bg_filter:
            continue
        if p.is_file() and p.suffix.lower() in ('.png', '.jpg', '.webp'):
            bgs[stem] = p
        elif p.is_dir():
            for sub in sorted(p.iterdir()):
                if sub.suffix.lower() in ('.png', '.jpg', '.webp'):
                    bgs[stem] = sub
                    break
    return bgs


def build_pipeline(args):
    project_root = Path(args.project).resolve()
    img_dir = Path(args.img_dir) if args.img_dir else (project_root / 'img')
    bg_dir = Path(args.bg_dir) if args.bg_dir else (project_root / '배경')
    out_dir = Path(args.out_dir) if args.out_dir else (img_dir / '.cutouts_matte_cache')
    comp_dir = Path(args.comp_dir) if args.comp_dir else (img_dir / '합성_배경')
    hr_cache = img_dir / '.alpha_hr_cache'
    seg_caches = {
        'birefnet-general': img_dir / '.cutouts_cache',
        'isnet-anime': img_dir / '.cutouts_isnet_cache',
    }

    print(f'=== [정밀 누끼 & 광학 배경 합성 파이프라인] ===')
    print(f'프로젝트: {project_root}')
    print(f'스프라이트 경로: {img_dir}')
    print(f'배경 경로: {bg_dir}')
    print(f'누끼 출력 캐시: {out_dir}')
    print(f'합성 출력 경로: {comp_dir}')

    sprites = scan_sprites(img_dir, args.chars)
    if not sprites:
        print(f'⚠️ 처리할 스프라이트가 없습니다. (탐색 경로: {img_dir})')
        return

    print(f'발견된 스프라이트: 총 {len(sprites)}장')

    # 1. rembg 세그멘테이션 마스크 캐싱
    update_seg_caches(sprites, seg_caches)

    # 2. HR 매팅 추론 (MPS/CUDA 가속)
    if not args.no_hr:
        update_hr_alpha(sprites, hr_cache)

    # 3. Trimap + Closed-Form Alpha Matting
    global _GLOBAL_MATTE_CFG
    _GLOBAL_MATTE_CFG = {
        'out_dir': out_dir,
        'img_dir': img_dir,
        'hr_cache': hr_cache,
        'seg_caches': seg_caches,
    }

    tasks = [
        (c, f) for c, f in sprites
        if args.force or _stale(out_dir / c / f.name, f, hr_cache / c / f.name,
                                *(cache / c / f.name for cache in seg_caches.values()))
    ]

    t0 = time.time()
    if tasks:
        print(f'\n▶ [1단계] 매팅 작업 실행: {len(tasks)}장 (워커: {args.workers})')
        with Pool(args.workers) as pool:
            results = pool.map(_process_task, tasks)
        fails = [msg for ok, msg in results if not ok]
        print(f'매팅 완료: {len(tasks) - len(fails)}/{len(tasks)} ({time.time() - t0:.1f}s)')
        for err in fails:
            print(f'  ❌ 오류: {err}')
    else:
        print('\n▶ [1단계] 매팅 캐시가 최신 상태입니다. (생략)')

    # 4. 배경 합성 작업
    backgrounds = scan_backgrounds(bg_dir, args.bg_names)
    if not backgrounds:
        print(f'⚠️ 배경 폴더에 배경 이미지가 없어 합성을 건너뜁니다. ({bg_dir})')
        return

    print(f'\n▶ [2단계] 시네마틱 광학 배경 합성 (사용 배경: {list(backgrounds.keys())})')
    ctasks = []
    for c, f in sprites:
        fg_path = out_dir / c / f.name
        if not fg_path.exists():
            continue
        for bg_name, bg_file in backgrounds.items():
            dst = comp_dir / bg_name / c / f.name
            if args.force or _stale(dst, fg_path, bg_file):
                ctasks.append((fg_path, bg_file, dst))

    if ctasks:
        print(f'합성 대상: {len(ctasks)}장 (워커: {args.workers})')
        with Pool(args.workers) as pool:
            cresults = pool.map(_composite_task, ctasks)
        cfails = [msg for ok, msg in cresults if not ok]
        print(f'합성 완료: {len(ctasks) - len(cfails)}/{len(ctasks)} ({time.time() - t0:.1f}s)')
        for err in cfails:
            print(f'  ❌ 합성 오류: {err}')
    else:
        print('합성 결과가 이미 최신 상태입니다.')

    print(f'\n✨ 전체 작업 완료!')


def main():
    parser = argparse.ArgumentParser(description='정밀 스프라이트 누끼 & 광학 배경 합성 도구')
    subparsers = parser.add_subparsers(dest='command', help='실행 모드')

    # 기본 파이프라인 모드
    p_build = subparsers.add_parser('build', help='프로젝트 일괄 누끼 및 배경 합성 (기본값)')
    p_build.add_argument('--project', default='.', help='프로젝트 루트 경로 (기본: 현재 폴더)')
    p_build.add_argument('--img-dir', help='스프라이트 폴더 (기본: <project>/img)')
    p_build.add_argument('--bg-dir', help='배경 폴더 (기본: <project>/배경)')
    p_build.add_argument('--out-dir', help='누끼 출력 폴더 (기본: <img-dir>/.cutouts_matte_cache)')
    p_build.add_argument('--comp-dir', help='합성 출력 폴더 (기본: <img-dir>/합성_배경)')
    p_build.add_argument('--chars', nargs='*', help='처리할 특정 캐릭터 디렉토리 목록')
    p_build.add_argument('--bg-names', nargs='*', help='합성할 특정 배경 목록')
    p_build.add_argument('--force', action='store_true', help='캐시를 무시하고 전체 강제 재생성')
    p_build.add_argument('--no-hr', action='store_true', help='HR 매팅 모델을 건너뛰고 빠른 기본 매팅만 수행')
    p_build.add_argument('--workers', type=int, default=6, help='병렬 워커 수 (기본: 6)')

    # 단일 이미지 합성 모드
    p_comp = subparsers.add_parser('composite', help='단일 전경(RGBA)과 배경(RGB) 시네마틱 합성')
    p_comp.add_argument('--fg', required=True, help='전경 RGBA 이미지 경로')
    p_comp.add_argument('--bg', required=True, help='배경 이미지 경로')
    p_comp.add_argument('--out', required=True, help='결과 저장 경로')

    args = parser.parse_args()

    if args.command == 'composite':
        fg_rgba = cv2.imread(args.fg, cv2.IMREAD_UNCHANGED)
        if fg_rgba is None or fg_rgba.ndim != 3 or fg_rgba.shape[2] != 4:
            sys.exit(f'전경 이미지는 알파 채널이 있는 4채널 RGBA여야 합니다: {args.fg}')
        res = composite_image(fg_rgba, Path(args.bg))
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(args.out, res)
        print(f'✅ 합성 완료: {args.out}')
        return

    # subparser 없이 바로 옵션들이 들어온 경우 기본 빌드로 전달
    if args.command is None:
        # build 모드 인자로 재파싱
        build_parser = argparse.ArgumentParser()
        build_parser.add_argument('--project', default='.')
        build_parser.add_argument('--img-dir')
        build_parser.add_argument('--bg-dir')
        build_parser.add_argument('--out-dir')
        build_parser.add_argument('--comp-dir')
        build_parser.add_argument('--chars', nargs='*')
        build_parser.add_argument('--bg-names', nargs='*')
        build_parser.add_argument('--force', action='store_true')
        build_parser.add_argument('--no-hr', action='store_true')
        build_parser.add_argument('--workers', type=int, default=6)
        bargs = build_parser.parse_args()
        build_pipeline(bargs)
    else:
        build_pipeline(args)


if __name__ == '__main__':
    main()
