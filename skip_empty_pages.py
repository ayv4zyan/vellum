#!/usr/bin/env python3
"""Drop heading-only chapter cards so Prev/Next and the TOC skip to real sections."""

from __future__ import annotations

import json
import re
import sys
from html import escape, unescape
from pathlib import Path

ARTICLE_RE = re.compile(
    r'<article class="chapter-content">(.*?)</article>',
    re.S | re.I,
)
HEADING_RE = re.compile(r"<h[1-6]\b[^>]*>.*?</h[1-6]>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
ANCHOR_RE = re.compile(r"<a\b[^>]*>", re.I)


def basename(href: str) -> str:
    path, _, _hash = href.partition("#")
    return Path(path).name or path


def is_heading_only(html: str) -> bool:
    match = ARTICLE_RE.search(html)
    if not match:
        return False
    leftover = HEADING_RE.sub("", match.group(1))
    leftover = TAG_RE.sub("", leftover)
    leftover = unescape(leftover)
    leftover = leftover.replace("\xa0", " ")
    leftover = leftover.replace("&nbsp;", " ")
    return leftover.strip() == ""


def page_title(html: str) -> str:
    match = TITLE_RE.search(html)
    if not match:
        return ""
    return re.sub(r"\s+", " ", unescape(match.group(1))).strip()


def rel_href(html: str, rel: str) -> str | None:
    for tag in ANCHOR_RE.findall(html):
        if re.search(rf'rel=["\']{rel}["\']', tag, re.I):
            href = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
            if href:
                return href.group(1)
    return None


def set_rel_href(html: str, rel: str, new_href: str) -> str:
    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if not re.search(rf'rel=["\']{rel}["\']', tag, re.I):
            return tag
        if re.search(r"href=", tag, re.I):
            return re.sub(r'href=["\'][^"\']*["\']', f'href="{new_href}"', tag, count=1)
        return tag[:-1] + f' href="{new_href}">'

    return ANCHOR_RE.sub(repl, html)


def set_card_title(html: str, card_class: str, title: str) -> str:
    pattern = re.compile(
        rf'(<a class="nav-card {card_class}"[^>]*>.*?<span class="card-title">)(.*?)(</span>)',
        re.S | re.I,
    )
    return pattern.sub(rf"\1{escape(title)}\3", html, count=1)


def follow(start: str, step: dict[str, str | None], empty: set[str]) -> str | None:
    seen: set[str] = set()
    current = step.get(start)
    while current and current in empty and current not in seen:
        seen.add(current)
        current = step.get(current)
    return current


def rewrite_toc_hrefs(html: str, skip_to: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        href = match.group(1)
        name = basename(href)
        if name in skip_to:
            return f'href="{skip_to[name]}"'
        return match.group(0)

    return re.sub(r'href="([^"]+)"', repl, html)


def rewrite_sitemap(node: object, skip_to: dict[str, str]) -> None:
    if isinstance(node, dict):
        path = node.get("path")
        if isinstance(path, str):
            name = basename(path)
            if name in skip_to:
                node["path"] = skip_to[name]
        for value in node.values():
            rewrite_sitemap(value, skip_to)
    elif isinstance(node, list):
        for item in node:
            rewrite_sitemap(item, skip_to)


def skip_empty_pages(out_dir: Path) -> list[str]:
    pages = {
        path.name: path.read_text(encoding="utf-8")
        for path in out_dir.glob("*.html")
    }
    empty = {name for name, html in pages.items() if name != "index.html" and is_heading_only(html)}
    if not empty:
        return []

    nxt = {name: (basename(rel_href(html, "next") or "") or None) for name, html in pages.items()}
    prv = {name: (basename(rel_href(html, "previous") or "") or None) for name, html in pages.items()}
    skip_to = {name: follow(name, nxt, empty) or "index.html" for name in empty}
    skip_back = {name: follow(name, prv, empty) or "index.html" for name in empty}

    for name, html in list(pages.items()):
        if name in empty:
            continue
        next_href = rel_href(html, "next")
        if next_href and basename(next_href) in empty:
            dest = skip_to[basename(next_href)]
            html = set_rel_href(html, "next", dest)
            dest_title = page_title(pages[dest]) if dest in pages else dest
            if dest_title:
                html = set_card_title(html, "next-card", dest_title)
        prev_href = rel_href(html, "previous")
        if prev_href and basename(prev_href) in empty:
            dest = skip_back[basename(prev_href)]
            html = set_rel_href(html, "previous", dest)
            dest_title = page_title(pages[dest]) if dest in pages else dest
            if dest_title:
                html = set_card_title(html, "prev-card", dest_title)
        html = rewrite_toc_hrefs(html, skip_to)
        pages[name] = html
        (out_dir / name).write_text(html, encoding="utf-8")

    sitemap_path = out_dir / "sitemap.json"
    if sitemap_path.exists():
        data = json.loads(sitemap_path.read_text(encoding="utf-8"))
        rewrite_sitemap(data, skip_to)
        sitemap_path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")

    removed = sorted(empty)
    for name in removed:
        dest = skip_to[name]
        title = page_title(pages.get(dest, "")) or dest
        dest_js = json.dumps(dest)
        (out_dir / name).write_text(
            (
                "<!DOCTYPE html>\n<html lang=\"en\"><head>"
                '<meta charset="utf-8" />'
                f'<meta http-equiv="refresh" content="0;url={escape(dest)}" />'
                f'<link rel="canonical" href="{escape(dest)}" />'
                f"<title>{escape(title)}</title>"
                f"<script>location.replace({dest_js});</script>"
                f'</head><body><p><a href="{escape(dest)}">{escape(title)}</a></p>'
                "</body></html>\n"
            ),
            encoding="utf-8",
        )
    return removed


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: skip_empty_pages.py OUTPUT_DIR", file=sys.stderr)
        return 2
    out_dir = Path(sys.argv[1])
    removed = skip_empty_pages(out_dir)
    if removed:
        print("Skipped empty pages:", ", ".join(removed))
    else:
        print("No empty pages to skip.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
