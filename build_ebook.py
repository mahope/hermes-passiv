#!/usr/bin/env python3
"""Build KDP-ready EPUB from ebook/nis2-for-agencies.md.

Self-contained: no external tools required (hand-rolled EPUB 3 via zipfile).
Run: .venv/bin/python3 build_ebook.py
Output: ebook/nis2-for-agencies.epub
"""
import hashlib
import html as html_mod
import os
import re
import zipfile

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "ebook", "nis2-for-agencies.md")
OUT = os.path.join(ROOT, "ebook", "nis2-for-agencies.epub")

TITLE = "NIS2 Compliance for Small Web Agencies"
SUBTITLE = "A Practical Guide to Meeting EU Cybersecurity Requirements Without a Compliance Team"
AUTHOR = "Mahope"
LANG = "en"
UUID = "urn:uuid:6f1c2a34-9b7e-4e2d-8a51-nis2agencies01"

CSS = """body { font-family: serif; line-height: 1.7; margin: 5%%; }
h1 { font-size: 1.6em; page-break-before: always; }
h1.title { text-align: center; page-break-before: avoid; margin-top: 30%%; }
h2 { font-size: 1.35em; border-bottom: 1px solid #ccc; padding-bottom: 0.2em; }
h3 { font-size: 1.15em; }
table { border-collapse: collapse; width: 100%%; margin: 1em 0; }
th, td { border: 1px solid #999; padding: 6px; text-align: left; }
th { background: #eee; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 1em; color: #444; }
.subtitle { text-align: center; font-style: italic; color: #555; }
"""


def md_to_body(md_text: str) -> str:
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    # Strip the leading H1 + subtitle H2 (they go on the title page instead)
    body_html = re.sub(r"^\s*<h1>.*?</h1>", "", body_html, count=1, flags=re.S)
    body_html = re.sub(r"^\s*<h2>A Practical Guide.*?</h2>", "", body_html, count=1, flags=re.S)
    return body_html


def split_chapters(body_html: str):
    """Split on top-level <h2>Chapter/Appendix headings into chapter files."""
    parts = re.split(r"(?=<h2>)", body_html)
    chapters = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r"<h2>(.*?)</h2>", p, flags=re.S)
        heading = html_mod.unescape(re.sub("<[^>]+>", "", m.group(1))).strip() if m else "Front Matter"
        chapters.append((heading, p))
    return chapters


def esc(s: str) -> str:
    return html_mod.escape(s, quote=True)


def main():
    with open(SRC, encoding="utf-8") as f:
        md_text = f.read()
    body_html = md_to_body(md_text)
    chapters = split_chapters(body_html)

    files = {}  # path in zip -> bytes
    manifest, spine = [], []

    def add(path, content, props=None):
        files[path] = content.encode("utf-8") if isinstance(content, str) else content
        return path

    add("mimetype", "application/epub+zip")  # must be first, stored uncompressed
    nav_items = "".join(
        f'<li><a href="ch{i}.xhtml">{esc(h)}</a></li>' for i, (h, _) in enumerate(chapters)
    )
    add(
        "nav.xhtml",
        f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Contents</title><link rel="stylesheet" href="style.css"/></head><body>
<nav epub:type="toc" id="toc"><h2>Contents</h2><ol>{nav_items}</ol></nav>
</body></html>""",
    )

    for i, (heading, frag) in enumerate(chapters):
        cls = ' class="title"' if i == 0 and "NIS2 Compliance" in heading else ""
        add(
            f"ch{i}.xhtml",
            f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><head><title>{esc(heading)}</title><link rel="stylesheet" href="style.css"/></head>
<body>{frag}</body></html>""",
        )
        manifest.append(f'<item id="c{i}" href="ch{i}.xhtml" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="c{i}"/>')

    add("style.css", CSS)

    manifest.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
    manifest.append('<item id="css" href="style.css" media-type="text/css"/>')

    add(
        "content.opf",
        f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">{UUID}</dc:identifier>
<dc:title>{esc(TITLE)}</dc:title>
<dc:creator>{esc(AUTHOR)}</dc:creator>
<dc:language>{LANG}</dc:language>
<dc:description>{esc(SUBTITLE)}</dc:description>
<meta property="dcterms:modified">2026-08-23T00:00:00Z</meta>
</metadata>
<manifest>{''.join(manifest)}</manifest>
<spine>{''.join(spine)}</spine>
</package>""",
    )

    container = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""
    add("META-INF/container.xml", container)

    with zipfile.ZipFile(OUT, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), files["mimetype"], compress_type=zipfile.ZIP_STORED)
        for path, data in files.items():
            if path == "mimetype":
                continue
            z.writestr(path, data, compress_type=zipfile.ZIP_DEFLATED)

    size = os.path.getsize(OUT)
    print(f"EPUB written: {OUT} ({size} bytes, {len(chapters)} chapters)")
    for i, (h, _) in enumerate(chapters):
        print(f"  ch{i}: {h}")


if __name__ == "__main__":
    main()
