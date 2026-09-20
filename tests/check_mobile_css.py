#!/usr/bin/env python3
"""Fail if the mobile @media block is nested inside .card-title (unclosed rule)."""

from pathlib import Path
import re
import sys

CSS = Path(__file__).resolve().parents[1] / "book.css"
text = CSS.read_text(encoding="utf-8")

# Strip comments so they cannot hide a missing brace.
stripped = re.sub(r"/\*.*?\*/", "", text, flags=re.S)

depth = 0
in_card_title = False
card_title_depth = None

tokens = re.finditer(r"\.card-title\b|@media|[{}]", stripped)
for match in tokens:
    token = match.group(0)
    if token == ".card-title":
        in_card_title = True
    elif token == "{":
        depth += 1
        if in_card_title and card_title_depth is None:
            card_title_depth = depth
        in_card_title = False
    elif token == "}":
        if card_title_depth is not None and depth == card_title_depth:
            card_title_depth = None
        depth -= 1
        in_card_title = False
    elif token == "@media":
        in_card_title = False
        if card_title_depth is not None:
            print("FAIL: @media is nested inside .card-title — mobile drawer CSS will not apply")
            sys.exit(1)

if depth != 0:
    print(f"FAIL: unmatched braces (depth={depth})")
    sys.exit(1)

if ".card-title" in stripped and "@media (max-width: 959px)" not in stripped:
    print("FAIL: missing mobile @media block")
    sys.exit(1)

print("PASS: mobile @media is not nested inside .card-title")
