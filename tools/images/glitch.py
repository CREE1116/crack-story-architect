#!/usr/bin/env python3
"""Glitch post-process for a finished cover/banner PNG.

    python glitch.py cover.png out.png --level 2 --protect 300:640 --tint "#3CC4B6"

Effects (deterministic with --seed):
    level 1  RGB split + scanlines + fine noise
    level 2  + displaced horizontal slices
    level 3  + tinted pixel blocks (--tint) and stronger split in the slices
--protect Y0:Y1 keeps a horizontal band (e.g. the face) free of slice displacement.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
from PIL import Image

TEAL = np.array([0x3C, 0xC4, 0xB6], dtype=np.float32)


def rgb_split(a: np.ndarray, dx: int) -> np.ndarray:
    out = a.copy()
    out[:, :, 0] = np.roll(a[:, :, 0], dx, axis=1)
    out[:, :, 2] = np.roll(a[:, :, 2], -dx, axis=1)
    return out


def glitch(img: Image.Image, level: int, seed: int, protect: tuple[int, int] | None) -> Image.Image:
    rnd = random.Random(seed)
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    h, w, _ = a.shape
    s = w / 1080  # scale effects with resolution

    # 1) global chromatic aberration, subtle
    a = rgb_split(a, max(1, round(2 * s)))

    # 2) displaced slices with a stronger local split
    if level >= 2:
        for _ in range(9 if level == 2 else 14):
            bh = rnd.randint(round(4 * s), round(38 * s))
            y = rnd.randint(0, h - bh)
            if protect and not (y + bh < protect[0] or y > protect[1]):
                continue
            dx = rnd.choice((-1, 1)) * rnd.randint(round(12 * s), round(70 * s))
            band = np.roll(a[y:y + bh], dx, axis=1)
            a[y:y + bh] = rgb_split(band, round(rnd.randint(4, 10) * s) * (1 if dx > 0 else -1))

    # 3) teal pixel blocks
    if level >= 3:
        for _ in range(10):
            bw_, bh_ = rnd.randint(round(20 * s), round(120 * s)), rnd.randint(round(3 * s), round(14 * s))
            x, y = rnd.randint(0, w - bw_), rnd.randint(0, h - bh_)
            if protect and protect[0] <= y <= protect[1]:
                continue
            a[y:y + bh_, x:x + bw_] = a[y:y + bh_, x:x + bw_] * 0.35 + TEAL * 0.65 * rnd.uniform(0.4, 1.0)

    # 4) scanlines + fine noise
    a[::3] *= 0.92
    a += np.random.default_rng(seed).normal(0, 3.0, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--level", type=int, default=2, choices=(1, 2, 3))
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--protect", default="", help="Y0:Y1 band kept free of slice displacement")
    ap.add_argument("--tint", default="#3CC4B6", help="pixel block colour (level 3)")
    args = ap.parse_args()
    protect = tuple(int(v) for v in args.protect.split(":")) if args.protect else None
    global TEAL
    h = args.tint.lstrip("#")
    TEAL = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)
    out = glitch(Image.open(args.src), args.level, args.seed, protect)
    out.save(args.out, optimize=True)
    out.save(args.out.with_suffix(".webp"), quality=92, method=6)
    print(f"{args.out} {out.size} {args.out.stat().st_size / 1e6:.2f}MB")


if __name__ == "__main__":
    main()
