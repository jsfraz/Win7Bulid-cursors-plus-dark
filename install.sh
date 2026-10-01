#!/bin/bash

ROOT_UID=0
DEST_DIR=

# Destination directory
if [ "$UID" -eq "$ROOT_UID" ]; then
  DEST_DIR="/usr/share/icons"
else
  DEST_DIR="$HOME/.local/share/icons"
fi

if [ -d "$DEST_DIR/Win7Bulid-cursors" ]; then
  rm -r "$DEST_DIR/Win7Bulid-cursors"
fi

if [ -d "$DEST_DIR/Win7Bulid-cursors-dark" ]; then
  rm -r "$DEST_DIR/Win7Bulid-cursors-dark"
fi

cp -pr dist "$DEST_DIR/Win7Bulid-cursors"
cp -pr dist-dark "$DEST_DIR/Win7Bulid-cursors-dark"

echo "Installed Win7Bulid-cursors and Win7Bulid-cursors-dark to $DEST_DIR"
echo "Finished..."
