#!/usr/bin/env python3
"""Verify light/dark cursor sources and rendered PNGs."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SVG = SRC / "svg"
SVG_DARK = SRC / "svg-dark"
PIX_LIGHT = SRC / "pixmaps" / "light" / "x1_5"
PIX_DARK = SRC / "pixmaps" / "dark" / "x1_5"

COMPOSITE = frozenset(
    {"context-menu.svg", "help.svg", "copy.svg", "alias.svg", "no-drop.svg"}
)
ARROW_D = re.compile(r"6\.9356[^\"]*4[^\"]*v\s*14", re.I)
PATH_TAG = re.compile(r"<path\s+.*?\/>", re.DOTALL | re.I)


def _prepare_svg_dark() -> None:
    if SVG_DARK.exists():
        shutil.rmtree(SVG_DARK)
    shutil.copytree(SVG, SVG_DARK)
    subprocess.run(
        [sys.executable, str(SRC / "make-dark-arrow-variant.py"), str(SVG_DARK)],
        check=True,
    )


def test_svg_dark_monochrome() -> None:
    _prepare_svg_dark()
    size_hor = (SVG_DARK / "size_hor.svg").read_text(encoding="utf-8")
    assert "#2d2d2d" in size_hor, "size_hor.svg should use dark fill"
    assert "#151515" not in size_hor, "size_hor.svg should not keep light-theme stroke"

    pointer = (SVG_DARK / "pointer.svg").read_text(encoding="utf-8")
    assert "#2d2d2d" in pointer, "pointer.svg hand fill should be dark"
    assert "#e8e8e8" in pointer, "pointer.svg outline should be light"

    pencil = (SVG_DARK / "pencil.svg").read_text(encoding="utf-8")
    assert "fill:#151515" not in pencil.lower(), "pencil.svg outline should not stay #151515"
    assert "fill:#e8e8e8" in pencil.lower(), "pencil.svg outline should be light in style"
    assert "fill:#2d2d2d" in pencil.lower(), "pencil.svg body should be dark in style"

    prog = (SVG_DARK / "progress.svg").read_text(encoding="utf-8")
    prog_arrow = [t for t in PATH_TAG.findall(prog) if ARROW_D.search(t)]
    assert any("#2d2d2d" in t for t in prog_arrow), "progress.svg arrow should be dark"
    assert "url(#" in prog or "#3296" in prog.lower() or "stop-color" in prog, (
        "progress.svg spinner colors should remain"
    )
    wait = (SVG_DARK / "wait.svg").read_text(encoding="utf-8")
    assert wait == (SVG / "wait.svg").read_text(encoding="utf-8"), (
        "wait.svg must be unchanged"
    )

    not_allowed = (SVG_DARK / "not-allowed.svg").read_text(encoding="utf-8")
    assert "fill:#ffffff" in not_allowed.lower() or 'fill="#ffffff"' in not_allowed, (
        "not-allowed.svg white disc should stay white"
    )
    assert "linearGradient874" in not_allowed, "not-allowed.svg red fill should stay gradient"

    dnd = (SVG_DARK / "dnd-no-drop.svg").read_text(encoding="utf-8")
    assert "fill:#ffffff" in dnd.lower(), "dnd-no-drop badge disc should stay white"
    assert "#2d2d2d" in dnd.lower(), "dnd-no-drop hand fill should be dark"
    assert "linearGradient874" in dnd, "dnd-no-drop red fill should stay gradient"

    help_text = (SVG_DARK / "help.svg").read_text(encoding="utf-8")
    assert "#ffffff" in help_text or 'fill="#fff"' in help_text, (
        "help.svg badge whites should remain"
    )
    arrow_tags = [t for t in PATH_TAG.findall(help_text) if ARROW_D.search(t)]
    assert any("#2d2d2d" in t for t in arrow_tags), "help.svg arrow should be dark"


def _arrow_region_mean(path: Path) -> float:
    img = Image.open(path).convert("RGBA")
    region = img.crop((4, 4, 22, 22))
    total = n = 0
    for r, g, b, a in region.getdata():
        if a < 40:
            continue
        total += (r + g + b) / 3
        n += 1
    return total / max(n, 1)


def _png_pair_diff(name: str) -> float:
    light = Image.open(PIX_LIGHT / name).convert("RGBA")
    dark = Image.open(PIX_DARK / name).convert("RGBA")
    diff = ImageChops.difference(light, dark)
    return sum(diff.convert("L").getdata()) / (light.size[0] * light.size[1])


def test_png_dark_differs_from_light() -> None:
    if not PIX_LIGHT.is_dir() or not PIX_DARK.is_dir():
        raise AssertionError("Run ./build.sh first (missing src/pixmaps/light or dark)")

    light_default = _arrow_region_mean(PIX_LIGHT / "default.png")
    dark_default = _arrow_region_mean(PIX_DARK / "default.png")
    assert dark_default < light_default - 25, (
        f"default: dark ({dark_default:.1f}) should be darker than light ({light_default:.1f})"
    )

    assert _png_pair_diff("size_hor.png") > 8.0, "size_hor.png should differ between themes"
    assert _png_pair_diff("pointer.png") > 8.0, "pointer.png should differ between themes"

    prog_light = _arrow_region_mean(PIX_LIGHT / "progress.png")
    prog_dark = _arrow_region_mean(PIX_DARK / "progress.png")
    assert prog_dark < prog_light - 20, (
        f"progress arrow should be darker (light={prog_light:.1f}, dark={prog_dark:.1f})"
    )
    assert _png_pair_diff("progress.png") > 5.0, "progress.png should differ between themes"


def main() -> int:
    for test in (test_svg_dark_monochrome, test_png_dark_differs_from_light):
        try:
            test()
            print(f"ok  {test.__name__}")
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}", file=sys.stderr)
            return 1
    print("all tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
