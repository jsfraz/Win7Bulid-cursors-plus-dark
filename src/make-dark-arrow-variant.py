#!/usr/bin/env python3
"""Build svg-dark: dark monochrome cursors; keep wait* and badge accents on composites."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATH_TAG = re.compile(r"<path\s+.*?\/>", re.DOTALL | re.IGNORECASE)

ARROW_D = re.compile(r"6\.9356[^\"]*4[^\"]*v\s*14", re.IGNORECASE)
RIGHT_PTR_D = re.compile(r"m-12\.698 14\.644v14", re.IGNORECASE)

DARK_FILL = "#2d2d2d"
LIGHT_STROKE = "#e8e8e8"

# Arrow + colored badge: recolor only the main pointer path, not badge whites.
COMPOSITE_ARROW_BADGE = frozenset(
    {
        "context-menu.svg",
        "help.svg",
        "copy.svg",
        "alias.svg",
        "no-drop.svg",
    }
)


def _is_wait_cursor(name: str) -> bool:
    stem = name.removesuffix(".svg")
    if stem == "wait":
        return True
    return stem.startswith("wait-")


def _is_progress_cursor(name: str) -> bool:
    stem = name.removesuffix(".svg")
    if stem == "progress":
        return True
    return stem.startswith("progress-")


def _is_main_arrow_path(tag: str) -> bool:
    return bool(ARROW_D.search(tag) or RIGHT_PTR_D.search(tag))


def _patch_path_tag(tag: str) -> str:
    if 'fill="none"' in tag and "stroke=" in tag:
        return re.sub(r'stroke="#151515"', f'stroke="{LIGHT_STROKE}"', tag)
    if re.search(r'fill="#fff(?:fff)?"', tag):
        return re.sub(r'fill="#fff(?:fff)?"', f'fill="{DARK_FILL}"', tag)
    return tag


def patch_composite_arrow_only(content: str) -> str:
    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if not _is_main_arrow_path(tag):
            return tag
        return _patch_path_tag(tag)

    return PATH_TAG.sub(repl, content)


def patch_not_allowed(content: str) -> str:
    """Keep white disc and red gradient; lighten outer ring only."""
    return content.replace('stroke="#151515"', f'stroke="{LIGHT_STROKE}"')


def patch_dnd_no_drop(content: str) -> str:
    """Dark hand; keep prohibition badge interior (white + red gradient)."""
    content = content.replace('stroke="#151515"', f'stroke="{LIGHT_STROKE}"')
    content = content.replace(
        'fill="#151515"\n       id="path32"',
        f'fill="{LIGHT_STROKE}"\n       id="path32"',
    )
    content = content.replace(
        'fill="#fff"\n       id="path34"',
        f'fill="{DARK_FILL}"\n       id="path34"',
    )
    return content


def patch_monochrome(content: str) -> str:
    content = content.replace('stroke="#151515"', f'stroke="{LIGHT_STROKE}"')
    content = re.sub(r'fill="#151515"', f'fill="{LIGHT_STROKE}"', content)
    content = re.sub(r'fill="#ffffff"', f'fill="{DARK_FILL}"', content)
    content = re.sub(r'fill="#fff"', f'fill="{DARK_FILL}"', content)
    content = re.sub(
        r"fill:#ffffff\b", f"fill:{DARK_FILL}", content, flags=re.IGNORECASE
    )
    content = re.sub(r"fill:#fff\b", f"fill:{DARK_FILL}", content, flags=re.IGNORECASE)
    content = re.sub(
        r"fill:#151515\b", f"fill:{LIGHT_STROKE}", content, flags=re.IGNORECASE
    )
    content = re.sub(
        r"stroke:#151515\b", f"stroke:{LIGHT_STROKE}", content, flags=re.IGNORECASE
    )
    return content


def process_file(path: Path) -> None:
    name = path.name
    if _is_wait_cursor(name):
        return
    text = path.read_text(encoding="utf-8")
    if name == "not-allowed.svg":
        patched = patch_not_allowed(text)
    elif name == "dnd-no-drop.svg":
        patched = patch_dnd_no_drop(text)
    elif name in COMPOSITE_ARROW_BADGE or _is_progress_cursor(name):
        patched = patch_composite_arrow_only(text)
    else:
        patched = patch_monochrome(text)
    if patched != text:
        path.write_text(patched, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <svg-directory>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    for svg in sorted(root.glob("*.svg")):
        process_file(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
