#!/usr/bin/env python3
"""Recolor monochrome cursor PNGs for dark theme (fallback when Inkscape is missing)."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

DARK_FILL = (0x2D, 0x2D, 0x2D)
LIGHT_STROKE = (0xE8, 0xE8, 0xE8)


def _is_wait_cursor(name: str) -> bool:
    if name == "wait":
        return True
    return name.startswith("wait-")


def _is_red_prohibition(r: int, g: int, b: int) -> bool:
    return r >= 90 and r >= g + 8 and r >= b + 8


def _in_not_allowed_white_disc(x: int, y: int, w: int, h: int) -> bool:
    bx = 16.075 * w / 32
    by = 15.925 * h / 32
    r = 10.0 * w / 32
    return (x - bx) ** 2 + (y - by) ** 2 <= r * r


def _in_dnd_badge_white_disc(x: int, y: int, w: int, h: int) -> bool:
    bx = 25.5 * w / 32
    by = 24.5 * h / 32
    r = 5.5 * w / 32
    return (x - bx) ** 2 + (y - by) ** 2 <= r * r


def _keep_accent(r: int, g: int, b: int) -> bool:
    mx, mn = max(r, g, b), min(r, g, b)
    sat = mx - mn
    if sat < 40:
        return False
    if b >= r + 25 and b >= g + 15 and mx > 90:
        return True
    if g >= r + 20 and g >= b + 10 and mx > 90:
        return True
    if r >= g + 25 and r >= b + 25 and mx > 100:
        return True
    return sat > 70 and mx > 120


def recolor_pixel(
    r: int,
    g: int,
    b: int,
    a: int,
    *,
    x: int = 0,
    y: int = 0,
    w: int = 1,
    h: int = 1,
    stem: str = "",
) -> tuple[int, int, int, int]:
    if a < 8:
        return r, g, b, a
    if _is_red_prohibition(r, g, b) or _keep_accent(r, g, b):
        return r, g, b, a
    lum = (r + g + b) / 3
    if stem == "not-allowed" and _in_not_allowed_white_disc(x, y, w, h) and lum >= 160:
        return r, g, b, a
    if stem == "dnd-no-drop" and _in_dnd_badge_white_disc(x, y, w, h) and lum >= 160:
        return r, g, b, a
    if lum >= 190:
        return (*DARK_FILL, a)
    if lum <= 50:
        return (*LIGHT_STROKE, a)
    if lum <= 130 and max(r, g, b) - min(r, g, b) < 35:
        v = max(0, int(lum * 0.55))
        return v, v, v, a
    return r, g, b, a


def recolor_image(path: Path) -> bool:
    img = Image.open(path).convert("RGBA")
    px = img.load()
    changed = False
    w, h = img.size
    stem = path.stem
    for y in range(h):
        for x in range(w):
            old = px[x, y]
            new = recolor_pixel(*old, x=x, y=y, w=w, h=h, stem=stem)
            if new != old:
                px[x, y] = new
                changed = True
    if changed:
        img.save(path, optimize=True)
    return changed


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <png-directory>", file=sys.stderr)
        return 2
    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        return 1
    touched = 0
    for path in sorted(directory.glob("*.png")):
        if _is_wait_cursor(path.stem):
            continue
        if recolor_image(path):
            touched += 1
    print(f"recolored {touched} cursor(s) in {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
