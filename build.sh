#!/bin/bash
set -euo pipefail

SRC=$PWD/src
SCALES=(x1 x1_25 x1_5 x2)

function render_pixmaps_from_svg {
	local SVG_SUBDIR=$1
	local DEST_ROOT=$2

	if ! command -v inkscape >/dev/null 2>&1; then
		return 1
	fi

	mkdir -p "$DEST_ROOT"/{x1,x1_25,x1_5,x2}
	cd "$SRC"/"$SVG_SUBDIR"
	find . -name "*.svg" -type f -exec sh -c \
		'inkscape -o "'"$DEST_ROOT"'/x1/${0%.svg}.png" -w 32 -h 32 $0' {} \;
	find . -name "*.svg" -type f -exec sh -c \
		'inkscape -o "'"$DEST_ROOT"'/x1_25/${0%.svg}.png" -w 40 -h 40 $0' {} \;
	find . -name "*.svg" -type f -exec sh -c \
		'inkscape -o "'"$DEST_ROOT"'/x1_5/${0%.svg}.png" -w 48 -h 48 $0' {} \;
	find . -name "*.svg" -type f -exec sh -c \
		'inkscape -o "'"$DEST_ROOT"'/x2/${0%.svg}.png" -w 64 -h 64 $0' {} \;
	cd "$SRC"
	return 0
}

function use_pixmap_root {
	local ROOT=$1
	for scale in "${SCALES[@]}"; do
		rm -rf "$SRC/$scale"
		cp -a "$ROOT/$scale" "$SRC/$scale"
	done
}

function snapshot_working_pixmaps {
	local DEST=$1
	mkdir -p "$DEST"
	for scale in "${SCALES[@]}"; do
		rm -rf "$DEST/$scale"
		cp -a "$SRC/$scale" "$DEST/$scale"
	done
}

function create_theme {
	local BUILD_NAME=$1
	local THEME_NAME=$2

	if ! command -v xcursorgen >/dev/null 2>&1; then
		echo "Skipping $BUILD_NAME — xcursorgen not installed (install xcursor-tools)."
		return 0
	fi

	local BUILD="$SRC"/../"$BUILD_NAME"
	local OUTPUT="$BUILD"/cursors
	local ALIASES="$SRC"/cursorList

	rm -rf "$BUILD"
	mkdir -p "$OUTPUT"

	cd "$SRC"
	echo -ne "Generating cursor theme ($THEME_NAME)...\\r"
	for CUR in config/*.cursor; do
		BASENAME="${CUR##*/}"
		BASENAME="${BASENAME%.*}"
		xcursorgen "$CUR" "$OUTPUT/$BASENAME"
	done
	echo -e "Generating cursor theme ($THEME_NAME)... DONE"

	cd "$OUTPUT"
	echo -ne "Generating shortcuts...\\r"
	while read -r ALIAS; do
		FROM="${ALIAS#* }"
		TO="${ALIAS% *}"
		if [ -e "$TO" ]; then
			continue
		fi
		ln -sr "$FROM" "$TO"
	done < "$ALIASES"
	echo -e "Generating shortcuts... DONE"

	echo -ne "Generating Theme Index...\\r"
	echo -e "[Icon Theme]\nName=$THEME_NAME\n" > "$BUILD/index.theme"
	echo -e "Generating Theme Index... DONE"
}

PIX_LIGHT="$SRC/pixmaps/light"
PIX_DARK="$SRC/pixmaps/dark"

# --- Light variant (committed PNGs, or Inkscape from src/svg) ---
if render_pixmaps_from_svg svg "$PIX_LIGHT"; then
	echo "Rendered light pixmaps from SVG (inkscape)."
else
	echo "Inkscape not found — using committed PNGs in src/x1* for light variant."
	mkdir -p "$PIX_LIGHT"
	snapshot_working_pixmaps "$PIX_LIGHT"
fi

use_pixmap_root "$PIX_LIGHT"
create_theme dist "Win7Bulid Cursors"
python3 "$SRC/generate-preview.py" "$PIX_LIGHT/x1_5" "$SRC/../preview-light.png" --theme light
cp "$SRC/../preview-light.png" "$SRC/../preview.png"

# --- Dark variant: patched SVG + recolored PNG fallback ---
rm -rf "$SRC/svg-dark"
cp -a "$SRC/svg" "$SRC/svg-dark"
python3 "$SRC/make-dark-arrow-variant.py" "$SRC/svg-dark"

mkdir -p "$PIX_DARK"
if render_pixmaps_from_svg svg-dark "$PIX_DARK"; then
	echo "Rendered dark pixmaps from svg-dark (inkscape)."
else
	echo "Applying dark arrow recolor to PNGs (no inkscape)."
	for scale in "${SCALES[@]}"; do
		rm -rf "$PIX_DARK/$scale"
		cp -a "$PIX_LIGHT/$scale" "$PIX_DARK/$scale"
		python3 "$SRC/make-dark-arrow-png.py" "$PIX_DARK/$scale"
	done
fi

use_pixmap_root "$PIX_DARK"
create_theme dist-dark "Win7Bulid Cursors Dark"
python3 "$SRC/generate-preview.py" "$PIX_DARK/x1_5" "$SRC/../preview-dark.png" --theme dark

# Restore working tree pixmaps to light (matches committed assets)
use_pixmap_root "$PIX_LIGHT"
