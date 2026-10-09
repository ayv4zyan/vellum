#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Accept input EPUB as first argument, default to book.epub
INPUT="${1:-book.epub}"

if [ ! -f "$INPUT" ]; then
  echo "Error: File '$INPUT' not found."
  echo "Usage: ./build.sh [path/to/book.epub] [output_folder]"
  exit 1
fi

BASENAME="$(basename "$INPUT")"
DEFAULT_OUT="${BASENAME%.*}"
OUTPUT="${2:-$DEFAULT_OUT}"

echo "==> Converting '$INPUT' -> '$OUTPUT'..."
rm -rf "$OUTPUT"

# --extract-media creates the output directory as it reads the book.
# chunkedhtml then refuses to unpack into that existing directory.
# Write a zip, unpack it, and point images at the copied files.
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
MEDIA="$WORKDIR/media"
ZIP="$WORKDIR/book.zip"

pandoc "$INPUT" \
  --template=template.html \
  --lua-filter=clean.lua \
  -t chunkedhtml \
  --split-level=2 \
  --extract-media="$MEDIA" \
  --css=book.css \
  --toc \
  -o "$ZIP"

mkdir -p "$OUTPUT"
unzip -q "$ZIP" -d "$OUTPUT"
python3 - "$OUTPUT" "$MEDIA" << 'PY'
import shutil
import sys
from pathlib import Path

out = Path(sys.argv[1])
media = Path(sys.argv[2]).resolve()
if media.is_dir():
    for src in media.rglob("*"):
        if not src.is_file():
            continue
        dest = out / src.relative_to(media)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(src, dest)

prefix = f"{media.as_posix()}/"
for html in out.rglob("*.html"):
    text = html.read_text(encoding="utf-8")
    updated = text.replace(prefix, "")
    if updated != text:
        html.write_text(updated, encoding="utf-8")
PY

cp book.css reader.js "$OUTPUT/"
python3 skip_empty_pages.py "$OUTPUT"

echo "==> Build complete! Open $OUTPUT/index.html to read."
