# Vellum

Convert any EPUB book into a distraction-free, elegant web reader with classic typography and a collapsible Table of Contents sidebar.

Powered by [Pandoc](https://pandoc.org/) and custom Lua filters.

---

## Features

- **Collapsible Sidebar Table of Contents**: Persistent navigation on desktop (collapsible with `≡ Contents`) and a smooth slide-out drawer on mobile and tablets.
- **Classic Warm Typography**: Styled with `Georgia, serif` at `20px` / `1.7` line-height, justified reading flow, and a soft warm parchment background (`#f7f1e3`).
- **Semantic Pandoc Lua Filter**:
  - Automatically cleans up empty paragraphs (`<p><br /></p>`) left by export tools like Apple Pages / Cocoa Writer.
  - Strips broken inline styles and phantom EPUB slice IDs from headings.
  - Formats callouts (*Rule of thumb: ...*) and dialogues cleanly.
- **Media & Image Extraction**: Automatically extracts images and figures into the output directory and formats them responsively.
- **Section Pages**: Pandoc splits at both chapter (`h1`) and section (`h2`) headings, so TOC entries like “The Mom Test” under Chapter One are their own pages. Heading-only chapter cards (no body) are skipped: TOC and Prev/Next go to the first real section. Each section page repeats the chapter name as a small kicker.
- **Keyboard Navigation**: Jump between pages using the `←` and `→` arrow keys.
- **Zero Dependencies**: Generated output is standard HTML and CSS—no web server, build toolchains, or JavaScript frameworks required. Works directly with `file://` in any browser.

---

## Prerequisites

- [Pandoc](https://pandoc.org/) (version 3.0 or later recommended)

Install via Homebrew on macOS:
```bash
brew install pandoc
```

---

## Quick Start

1. Place your `.epub` file in the folder (or provide the path).
2. Run `./build.sh`:

```bash
# Convert a specific EPUB file
./build.sh path/to/mybook.epub

# Or specify a custom output directory name
./build.sh path/to/mybook.epub my_output_folder
```

3. Open `mybook/index.html` in your browser.

---

## Project Structure

```
vellum/
├── build.sh         # Main build script
├── clean.lua        # Pandoc Lua filter for AST cleanup
├── template.html    # Chunked HTML reader template
├── book.css         # Typography & layout stylesheet
├── Makefile         # Optional make shortcuts
├── .gitignore       # Ignores generated folders and epub files
└── README.md
```

---

## License

MIT
