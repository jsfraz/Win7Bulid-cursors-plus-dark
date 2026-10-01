#!/usr/bin/env python3
"""Build a README preview sheet from rendered cursor PNGs (48×48, x1_5 scale)."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

BG_LIGHT = (235, 235, 235, 255)
# Slightly lighter than pure #202020 so dark arrow fill stays visible in README
BG_DARK = (56, 56, 56, 255)

# Same layout as the original preview.png (8×5 grid, 38 cursors).
GRID: list[list[str | None]] = [
    [
        "progress",
        "alias",
        "context-menu",
        "copy",
        "help",
        "no-drop",
        "all-scroll",
        "size_ver",
    ],
    [
        "fleur",
        "size_bdiag",
        "size_fdiag",
        "size_hor",
        "size_ver",
        "top_side",
        "bottom_side",
        "left_side",
    ],
    [
        "wait",
        "openhand",
        "dnd-move",
        "pointer",
        "dnd-no-drop",
        "not-allowed",
        "color-picker",
        "draft",
    ],
    [
        "default",
        "up-arrow",
        "crosshair",
        "vertical-text",
        "text",
        "zoom-in",
        "zoom-out",
        None,
    ],
    [
        "right_side",
        "right-arrow",
        "left-arrow",
        "down-arrow",
        "cell",
        "pencil",
        None,
        None,
    ],
]

COLS = 8
ROWS = 5
CELL = 150
ICON = 48


def build_sheet(png_dir: Path, background: tuple[int, int, int, int]) -> Image.Image:
    sheet = Image.new("RGBA", (COLS * CELL, ROWS * CELL), background)
    for row, names in enumerate(GRID):
        for col, name in enumerate(names):
            if not name:
                continue
            path = png_dir / f"{name}.png"
            if not path.is_file():
                raise FileNotFoundError(path)
            icon = Image.open(path).convert("RGBA")
            cell = Image.new("RGBA", (CELL, CELL), background)
            x = (CELL - ICON) // 2
            y = (CELL - ICON) // 2
            if icon.size != (ICON, ICON):
                icon = icon.resize((ICON, ICON), Image.Resampling.LANCZOS)
            cell.paste(icon, (x, y), icon)
            sheet.paste(cell, (col * CELL, row * CELL))
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("png_dir", type=Path, help="Directory with 48×48 PNGs (e.g. src/x1_5)")
    parser.add_argument("output", type=Path, help="Output PNG path")
    parser.add_argument(
        "--theme",
        choices=("light", "dark"),
        default="light",
        help="Background behind cursors (default: light)",
    )
    args = parser.parse_args()
    bg = BG_LIGHT if args.theme == "light" else BG_DARK
    sheet = build_sheet(args.png_dir, bg)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, optimize=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
