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

pandoc "$INPUT" \
  --template=template.html \
  --lua-filter=clean.lua \
  -t chunkedhtml \
  --split-level=2 \
  --extract-media="$OUTPUT" \
  --css=book.css \
  --toc \
  -o "$OUTPUT"

cp book.css reader.js "$OUTPUT/"
python3 skip_empty_pages.py "$OUTPUT"

echo "==> Build complete! Open $OUTPUT/index.html to read."
