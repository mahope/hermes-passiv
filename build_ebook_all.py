#!/usr/bin/env python3
"""Build KDP-ready EPUB for any ebook in ebook/ that has a .md source.

Generic version of build_ebook.py. Reads metadata from EBOOKS dict below.
Run: python3 build_ebook_all.py
Outputs: ebook/<slug>.epub for each book.
"""
import html as html_mod
import os
import re
import zipfile

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))

EBOOKS = [
    {
        "slug": "nis2-for-agencies",
        "title": "NIS2 Compliance for Small Web Agencies",
        "subtitle": "A Practical Guide to Meeting EU Cybersecurity Requirements Without a Compliance Team",
        "subtitle_prefix": "A Practical Guide",
        "uuid": "urn:uuid:6f1c2a34-9b7e-4e2d-8a51-nis2agencies01",
    },
    {
        "slug": "eaa-checklist",
        "title": "EAA Compliance Checklist for WordPress Sites",
        "subtitle": "A Practical Guide to Meeting EU Accessibility Requirements Under the European Accessibility Act",
        "subtitle_prefix": "A Practical Guide",
        "uuid": "urn:uuid:8d4e7b21-3c6a-4f95-b2e0-eaachecklist01",
    },
    {
        "slug": "gdpr-for-agencies",
        "title": "GDPR Compliance for Small Web Agencies",
        "subtitle": "A Practical Guide to Client Data Protection Without a Legal Department",
        "subtitle_prefix": "A Practical Guide",
        "uuid": "urn:uuid:2f7a9c45-5d81-4b3a-9e62-gdpragencies01",
    },
    {
        "slug": "eaa-shopify",
        "title": "EAA Compliance for Shopify Stores",
        "subtitle": "A Practical Guide to Meeting EU Accessibility Requirements Under the European Accessibility Act",
        "subtitle_prefix": "A Practical Guide",
        "uuid": "urn:uuid:8d4e7b21-3c6a-4f95-b2e0-eaashopify01",
    },
    {
        "slug": "cookie-consent-guide",
        "title": "Cookie Consent & Privacy Compliance for Small Websites",
        "subtitle": "A Practical Guide to Meeting GDPR, ePrivacy, and Cookie Requirements Without a Legal Team",
        "subtitle_prefix": "A Practical Guide",
        "uuid": "urn:uuid:2f7a9c45-5d81-4b3a-9e62-cookieconsent01",
    },
    {
        "slug": "build-your-first-chrome-extension",
        "title": "Build Your First Chrome Extension",
        "subtitle": "A Complete Practical Guide — From Blank Folder to the Chrome Web Store in 3 Hours",
        "subtitle_prefix": "A Complete Practical Guide",
        "uuid": "urn:uuid:4c8e1f77-2a95-4d63-b014-chromeextbook01",
    },
]

AUTHOR = "Mahope"
LANG = "en"
MODIFIED = "2026-08-24T00:00:00Z"

CSS = """body { font-family: serif; line-height: 1.7; margin: 5%; }
h1 { font-size: 1.6em; page-break-before: always; }
h1.title { text-align: center; page-break-before: avoid; margin-top: 30%; }
h2 { font-size: 1.35em; border-bottom: 1px solid #ccc; padding-bottom: 0.2em; }
h3 { font-size: 1.15em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #999; padding: 6px; text-align: left; }
th { background: #eee; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 1em; color: #444; }
.subtitle { text-align: center; font-style: italic; color: #555; }
pre { background: #f4f4f4; padding: 0.8em; font-size: 0.85em; overflow-x: hidden; white-space: pre-wrap; }
"""


def esc(s: str) -> str:
    return html_mod.escape(s, quote=True)


def md_to_body(md_text: str, subtitle_prefix: str) -> str:
    body_html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    body_html = re.sub(r"^\s*<h1>.*?</h1>", "", body_html, count=1, flags=re.S)
    body_html = re.sub(
        r"^\s*<h2>" + re.escape(subtitle_prefix) + r".*?</h2>", "", body_html, count=1, flags=re.S
    )
    return body_html


def split_chapters(body_html: str):
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


def build(book: dict) -> str:
    src = os.path.join(ROOT, "ebook", book["slug"] + ".md")
    out = os.path.join(ROOT, "ebook", book["slug"] + ".epub")
    with open(src, encoding="utf-8") as f:
        md_text = f.read()
    body_html = md_to_body(md_text, book["subtitle_prefix"])
    chapters = split_chapters(body_html)

    files = {}

    def add(path, content):
        files[path] = content.encode("utf-8") if isinstance(content, str) else content
        return path

    add("mimetype", "application/epub+zip")
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

    manifest, spine = [], []
    for i, (heading, frag) in enumerate(chapters):
        add(
            f"ch{i}.xhtml",
            f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><head><title>{esc(heading)}</title><link rel="stylesheet" href="style.css"/></head>
<body>{frag.replace("<hr>", "<hr/>").replace("<br>", "<br/>")}</body></html>""",
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
<dc:identifier id="bookid">{book['uuid']}</dc:identifier>
<dc:title>{esc(book['title'])}</dc:title>
<dc:creator>{esc(AUTHOR)}</dc:creator>
<dc:language>{LANG}</dc:language>
<dc:description>{esc(book['subtitle'])}</dc:description>
<meta property="dcterms:modified">{MODIFIED}</meta>
</metadata>
<manifest>{''.join(manifest)}</manifest>
<spine>{''.join(spine)}</spine>
</package>""",
    )

    add(
        "META-INF/container.xml",
        """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
    )

    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), files["mimetype"], compress_type=zipfile.ZIP_STORED)
        for path, data in files.items():
            if path == "mimetype":
                continue
            z.writestr(path, data, compress_type=zipfile.ZIP_DEFLATED)

    print(f"EPUB written: {out} ({os.path.getsize(out)} bytes, {len(chapters)} chapters)")
    for i, (h, _) in enumerate(chapters):
        print(f"  ch{i}: {h}")
    return out


def main():
    for book in EBOOKS:
        build(book)


if __name__ == "__main__":
    main()
