#!/usr/bin/env python3
"""H1 chapters and H2 sections must become separate chunkedhtml pages."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from skip_empty_pages import skip_empty_pages  # noqa: E402
MD_FIXTURE = """---
title: Test Book
author: Tester
---

# CHAPTER ONE

## The Mom Test

First section body.

## Good question / bad question

Second section body.
"""

# EPUBs nest headings inside section Divs; the kicker must still splice in.
HTML_FIXTURE = """<div>
<h1>CHAPTER ONE</h1>
<h2>The Mom Test</h2>
<p>First section body.</p>
<h2>Good question / bad question</h2>
<p>Second section body.</p>
</div>
"""

# The Mom Test EPUB uses h2 for chapters and h3 for sections.
EPUB_LIKE_FIXTURE = """<div>
<h2>CHAPTER ONE</h2>
<h3>The Mom Test</h3>
<p>First section body.</p>
<h3>Good question / bad question</h3>
<p>Second section body.</p>
</div>
"""


def convert(src: Path, out: Path, extra: list[str] | None = None) -> None:
    cmd = ["pandoc"]
    if extra:
        cmd.extend(extra)
    cmd.extend(
        [
            str(src),
            f"--template={ROOT / 'template.html'}",
            f"--lua-filter={ROOT / 'clean.lua'}",
            "-t",
            "chunkedhtml",
            "--split-level=2",
            "--toc",
            "-o",
            str(out),
        ]
    )
    subprocess.run(cmd, check=True)


def assert_split_book(out: Path) -> None:
    chapter = (out / "1-chapter-one.html").read_text(encoding="utf-8")
    section1 = (out / "1.1-the-mom-test.html").read_text(encoding="utf-8")
    section2 = (out / "1.2-good-question-bad-question.html").read_text(encoding="utf-8")
    toc = (out / "index.html").read_text(encoding="utf-8")

    assert "location.replace" in chapter
    assert "First section body" not in chapter
    assert "chapter-content" not in chapter

    assert "First section body" in section1
    assert "Second section body" not in section1
    assert 'class="chapter-kicker"' in section1
    assert "CHAPTER ONE" in section1
    assert 'rel="previous"' in section1
    assert "1-chapter-one.html" not in section1

    assert "Second section body" in section2
    assert "First section body" not in section2
    assert 'class="chapter-kicker"' in section2

    assert "1.1-the-mom-test.html" in toc
    assert "1.2-good-question-bad-question.html" in toc
    assert "href=\"1-chapter-one.html" not in toc


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        md_src = tmp_path / "book.md"
        md_out = tmp_path / "md-out"
        md_src.write_text(MD_FIXTURE, encoding="utf-8")
        convert(md_src, md_out)
        skip_empty_pages(md_out)
        assert_split_book(md_out)

        html_src = tmp_path / "book.html"
        html_out = tmp_path / "html-out"
        html_src.write_text(HTML_FIXTURE, encoding="utf-8")
        convert(html_src, html_out, extra=["-f", "html", "-M", "title=Test Book"])
        skip_empty_pages(html_out)
        assert_split_book(html_out)

        epub_src = tmp_path / "epub-like.html"
        epub_out = tmp_path / "epub-out"
        epub_src.write_text(EPUB_LIKE_FIXTURE, encoding="utf-8")
        convert(epub_src, epub_out, extra=["-f", "html", "-M", "title=Test Book"])
        skip_empty_pages(epub_out)
        section_files = list(epub_out.glob("*the-mom-test.html"))
        chapter_files = list(epub_out.glob("*chapter-one.html"))
        assert section_files, f"missing section page in {list(epub_out.glob('*.html'))}"
        assert chapter_files, f"missing chapter redirect in {list(epub_out.glob('*.html'))}"
        section_html = section_files[0].read_text(encoding="utf-8")
        chapter_html = chapter_files[0].read_text(encoding="utf-8")
        assert "First section body" in section_html
        assert 'class="chapter-kicker"' in section_html
        assert "CHAPTER ONE" in section_html
        assert "location.replace" in chapter_html
        assert "First section body" not in chapter_html

    print("PASS: h2 sections are separate pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
