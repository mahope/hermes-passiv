#!/usr/bin/env python3
"""Build a combined ComplianceDocs HTML bundle for Gumroad.

Combines all 4 product templates into a single printable HTML file.
Run: .venv/bin/python3 build_bundle.py
Output: products/compliance-bundle.html
"""
import os
import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "products")
OUT = os.path.join(ROOT, "products", "compliance-bundle.html")

FILES = [
    ("NIS2 Contract Clause Pack", "nis2-contract-clauses.md"),
    ("Vendor Security Assessment Checklist", "vendor-assessment-checklist.md"),
    ("Data Processing Agreement — Small Agency Template", "dpa-template.md"),
    ("EAA Accessibility Statement Template", "eaa-statement-template.md"),
]

PAGE_CSS = """
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.7;
  color: #1a1a1a;
  max-width: 750px;
  margin: 0 auto;
  padding: 60px 40px;
  background: #fafafa;
}
h1 { font-size: 2em; margin: 2em 0 0.3em; text-align: center; }
h2 { font-size: 1.5em; margin: 2em 0 0.5em; border-bottom: 2px solid #2c5282; padding-bottom: 0.2em; color: #2c5282; }
h3 { font-size: 1.2em; margin: 1.5em 0 0.5em; color: #333; }
p { margin: 0.8em 0; }
hr { border: none; border-top: 2px solid #ccc; margin: 3em 0; }
pre, code { background: #f0f0f0; padding: 0.1em 0.3em; border-radius: 3px; font-family: "SF Mono", monospace; font-size: 0.92em; }
pre { padding: 1em; overflow-x: auto; margin: 1em 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.92em; }
th, td { border: 1px solid #aaa; padding: 8px 10px; text-align: left; }
th { background: #e8ecf2; font-weight: 600; }
blockquote {
  border-left: 4px solid #2c5282;
  margin: 1em 0;
  padding: 0.8em 1.2em;
  background: #f0f4fa;
  font-style: italic;
}
ul, ol { margin: 0.8em 0; padding-left: 1.5em; }
li { margin: 0.4em 0; }
.cover {
  page-break-after: always;
  text-align: center;
  padding: 120px 0;
}
.cover h1 { font-size: 2.8em; margin-top: 0; }
.cover .sub { color: #555; font-size: 1.2em; font-style: italic; margin: 1em 0 2em; }
.cover .meta { color: #888; font-size: 0.95em; }
.cover .meta span { display: inline-block; margin: 0 1em; }
.toc { background: #f4f6f8; padding: 1.5em 2em; border-radius: 8px; margin: 2em 0; }
.toc a { color: #2c5282; text-decoration: none; }
.toc a:hover { text-decoration: underline; }
.footer { margin-top: 3em; padding: 1.5em; background: #f4f6f8; border-radius: 8px; font-size: 0.92em; }
.footer h3 { margin-top: 0; }
@media print {
  body { padding: 20px; max-width: none; background: white; }
  .cover { padding: 60px 0; }
}
</style>
"""


def md2html(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )


def strip_frontmatter(md_text: str, name: str) -> str:
    """Remove the delivery/price section at the bottom (after ## Delivery)."""
    idx = md_text.find("\n## Delivery\n")
    if idx != -1:
        md_text = md_text[:idx].rstrip()
    # Remove leading h1 (we'll use our own)
    lines = md_text.split("\n")
    cleaned = []
    skip_h1 = True
    for line in lines:
        if skip_h1 and line.startswith("# ") and "About This" not in line and "ComplianceDocs" not in line:
            skip_h1 = False
            continue
        # Remove the "Part of ComplianceDocs" line
        if "Part of ComplianceDocs" in line:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def main():
    parts = []
    toc_items = []

    # Front cover
    parts.append(f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ComplianceDocs Bundle — NIS2 · GDPR · EAA</title>
{PAGE_CSS}
</head>
<body>
<div class="cover">
<h1>ComplianceDocs Bundle</h1>
<p class="sub">For Small Web Agencies in the EU</p>
<p class="meta"><span>📋 4 templates</span><span>⚡ Fill &amp; deploy</span><span>📄 NIS2 · GDPR · EAA</span></p>
</div>

<div class="toc">
<h2>Contents</h2>
<ol>
""")
    for i, (name, fn) in enumerate(FILES, 1):
        parts.append(f'<li><a href="#ch{i}">{name}</a></li>\n')
        toc_items.append((i, name, fn))
    parts.append('</ol></div>\n')

    # Chapters
    for i, name, fn in toc_items:
        path = os.path.join(SRC_DIR, fn)
        with open(path, encoding="utf-8") as f:
            md = f.read()
        body = strip_frontmatter(md, name)
        body_html = md2html(body)
        parts.append(f'<hr id="ch{i}">\n<h1 style="text-align:center;margin-top:0;">{name}</h1>\n{body_html}\n')

    # Footer
    parts.append(f"""\
<div class="footer">
<h3>About ComplianceDocs</h3>
<p>ComplianceDocs is a series of practical templates, contract clauses, and guides built specifically for small web agencies in the EU. Each document is designed to be used directly — fill in your details and deliver to your clients.</p>
<p><strong>Price:</strong> $29.99 for the full bundle (save $22+ vs. individual purchases)</p>
<p><strong>Format:</strong> Downloadable HTML (print to PDF for client delivery)</p>
<p><em>Disclaimer: These documents provide templates based on publicly available regulatory requirements. They do not constitute legal advice. Have your legal counsel review before use.</em></p>
</div>
</body></html>""")

    html = "".join(parts)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(OUT)
    print(f"Bundle written: {OUT} ({size:,} bytes, {len(FILES)} templates)")


if __name__ == "__main__":
    main()