#!/usr/bin/env python3
"""Iteration 277: English blogpost "HTML table to CSV converter" — the
larger-market sibling of iter 276's Danish post. Article + FAQPage JSON-LD,
canonical, FAQ, comparison table, CTA to /clean-copy-tool. Adds entry to
sitemap.xml, cross-links from EN siblings + tool page, links back to DA post."""

import json, re

SLUG = "html-table-to-csv-converter"
URL = f"https://hermes-passiv.pages.dev/blog/{SLUG}"

ARTICLE_LD = {
    "@context": "https://schema.org", "@type": "Article",
    "headline": "HTML Table to CSV Converter — Turn Any Web Table into a Clean CSV (Free)",
    "description": "Paste HTML table markup and get RFC 4180-compliant CSV ready for Excel or Google Sheets. Runs entirely in your browser — nothing is uploaded.",
    "url": URL, "datePublished": "2026-08-25", "dateModified": "2026-08-25",
    "author": {"@type": "Organization", "name": "Hermes Compliance"},
    "publisher": {"@type": "Organization", "name": "Hermes Compliance"},
}

FAQS = [
    ("How do I convert an HTML table to CSV?",
     "Open the free web tool at /clean-copy-tool, copy the table's HTML from the page (right-click → Inspect → copy outerHTML, or press Ctrl+U and locate the <table> block), paste it into the input field and choose CSV as the output format. You instantly get RFC 4180-compliant CSV you can save as a .csv file."),
    ("What is RFC 4180?",
     "RFC 4180 is the standard for CSV files: rows separated by line breaks, cells separated by commas, and quotation marks around any cell that itself contains commas, quotes or line breaks. Clean Copy follows the standard, so your file opens correctly in Excel, Google Sheets, Numbers and every programming tool."),
    ("Are cells containing commas or line breaks preserved?",
     "Yes. Cells that contain commas, quotation marks or line breaks are automatically wrapped in double quotes, and inner quotes are escaped — exactly as the standard requires. No values get cut short."),
    ("What about colspan and nested tables?",
     "Clean Copy handles colspan/rowspan by repeating the value across the covered columns, flattens nested markup to plain text, and drops prose outside the table when a table is present — so you only get rows and columns."),
    ("Is my data sent to a server?",
     "No. The conversion runs 100% locally in your browser with JavaScript. Nothing you paste ever leaves your machine."),
    ("Can I also get Markdown instead of CSV?",
     "Yes. The same tool outputs Markdown tables (for Notion, Obsidian, GitHub) and WikiLinks format — just switch the output mode."),
]

FAQPAGE_LD = {
    "@context": "https://schema.org", "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in FAQS
    ],
}

def ld(obj):
    return json.dumps(obj, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HTML Table to CSV Converter — Free, Local, RFC 4180-Safe (2026)</title>
<meta name="description" content="Convert any HTML table to clean CSV right in your browser: RFC 4180-compliant, ready for Excel and Google Sheets, nothing sent to a server.">
<meta property="og:type" content="article">
<meta property="og:title" content="HTML Table to CSV Converter — free online">
<meta property="og:description" content="Paste HTML, get RFC 4180-compliant CSV ready for Excel and Google Sheets. Runs 100% in your browser.">
<meta property="og:image" content="https://hermes-passiv.pages.dev/clean-copy/og-preview.png">
<meta property="og:url" content="__URL__">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="__URL__">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
__ARTICLE__
</script>
<script type="application/ld+json">
__FAQ__
</script>
<script defer src="/track.js"></script>
<style>
  .compare { width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }
  .compare th, .compare td { text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }
  .compare th { border-bottom:2px solid var(--color-border); }
  pre.cmd {
    background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px;
    overflow-x:auto; font-size:0.85rem; line-height:1.6; margin:0.8rem 0;
  }
  pre.cmd code { font-family:'SF Mono','Monaco','Fira Code',monospace; }
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">CSV &middot; TABLES &middot; FREE TOOL</div>
    <h1>HTML table to CSV<br>in two clicks</h1>
    <p class="subtitle">Need the table from a web page inside Excel or Google Sheets? Paste the HTML and get RFC 4180-compliant CSV — every cell in its place, nothing sent to any server.</p>
    <div class="hero-cta">
      <a href="/clean-copy-tool" class="btn-primary">Open the free converter &rarr;</a>
      <a href="#how" class="btn-secondary">How it works</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 4 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Why HTML-to-CSV is hard by hand</h2>
    <p>An HTML table is not just text — and CSV does not tolerate sloppy text either. Three things almost always go wrong when converting manually:</p>
    <div class="problem-cards">
      <div class="card"><h3>&#9123; Commas inside cells</h3><p>A cell like &bdquo;1,234.56&ldquo; or &bdquo;Springfield, IL&ldquo; breaks the column structure — unless the cell is correctly wrapped in quotes.</p></div>
      <div class="card"><h3>&#8629; Line breaks in cells</h3><p>Cells with line breaks snap rows apart if they aren't escaped per RFC 4180. The file looks fine in a text editor and is broken in your spreadsheet.</p></div>
      <div class="card"><h3>&#129536; colspan and nested markup</h3><p>Headers spanning multiple columns, bold text, links and nested elements produce extra columns or empty fields when treated as plain text.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>How to do it</h2>
    <p>The free <a href="/clean-copy-tool" style="color:var(--color-accent);">Clean Copy web tool</a> converts HTML tables to correct CSV directly in your browser.</p>

    <h3 style="margin-top:24px;">1. Get the table's HTML</h3>
    <pre class="cmd"><code>Right-click the table &rarr; Inspect
&rarr; right-click the &lt;table&gt; element &rarr; Copy &rarr; Copy outerHTML.
(Alternatively: Ctrl+U and find the &lt;table&gt; block.)</code></pre>

    <h3 style="margin-top:24px;">2. Paste and pick CSV</h3>
    <pre class="cmd"><code>Go to /clean-copy-tool, paste the HTML,
and click "CSV" as the output format.</code></pre>

    <h3 style="margin-top:24px;">3. Save as .csv</h3>
    <pre class="cmd"><code>Copy the result into a text editor and save it as
competitor-prices.csv. Or paste straight into Excel /
Google Sheets — Data &rarr; From text/CSV reads it automatically.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>&#9989; RFC 4180-compliant</h3><p>Cells with commas, quotes or line breaks are quoted and escaped automatically — the file opens cleanly in any spreadsheet.</p></div>
      <div class="card"><h3>&#129529; Just the table</h3><p>Prose, menus and ads outside the table are dropped whenever a table is present in what you paste.</p></div>
      <div class="card"><h3>&#128274; 100% local</h3><p>The conversion runs in your browser. Your data never leaves your machine.</p></div>
    </div>
  </div>
</section>

<section class="products" id="options">
  <div class="container">
    <h2>Your options compared</h2>
    <table class="compare">
      <thead>
        <tr><th>Method</th><th>RFC 4180-safe?</th><th>Catch</th></tr>
      </thead>
      <tbody>
        <tr><td>Manual copy-paste</td><td>No</td><td>Commas and line breaks wreck the columns</td></tr>
        <tr><td>The site's own export button</td><td>Sometimes</td><td>Rarely exists; often locked behind a paid plan</td></tr>
        <tr><td>Python script (BeautifulSoup)</td><td>Yes</td><td>Requires coding and environment setup</td></tr>
        <tr>
          <td><a href="/clean-copy-tool" style="color:var(--color-accent);">Clean Copy web tool — CSV mode</a></td>
          <td>Yes</td>
          <td>None — free, no install, runs locally</td>
        </tr>
      </tbody>
    </table>
    <p>Use it often? There's also a <a href="/clean-copy" style="color:var(--color-accent);">browser extension</a>, a CLI tool and an Obsidian plugin powered by the same CSV engine.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
__FAQCARDS__
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy-tool" class="btn-primary">Try the converter now — free &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/copy-table-from-website-to-excel" style="color:var(--color-accent);">Web table &rarr; Excel</a> &middot; <a href="/blog/copy-table-website-to-notion" style="color:var(--color-accent);">Web table &rarr; Notion</a> &middot; <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Table &rarr; Google Sheets</a> &middot; <a href="/blog/html-to-markdown-converter" style="color:var(--color-accent);">HTML &rarr; Markdown converter</a> &middot; <a href="/blog/html-tabel-til-csv" style="color:var(--color-accent);">HTML-tabel til CSV (DA)</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Free tools</a></p>
</footer>
<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});}catch(e){}})();
</script>
</body>
</html>
"""

faqcards = "\n".join(
    f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS
)
html = (html.replace("__ARTICLE__", ld(ARTICLE_LD))
            .replace("__FAQ__", ld(FAQPAGE_LD))
            .replace("__FAQCARDS__", faqcards)
            .replace("__URL__", URL))

out = f"site/blog/{SLUG}.html"
with open(out, "w") as f:
    f.write(html)
print(f"Wrote {out}")

# --- JSON-LD sanity check ---
content = open(out).read()
for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL):
    parsed = json.loads(block)
    assert parsed["@context"] == "https://schema.org", parsed["@context"]
print("JSON-LD valid")

# --- Internal linkcheck: every /... href must exist in site tree ---
import os
bad = []
for m in re.findall(r'href="(/[a-z0-9\-./]*)"', content):
    p = m.split("#")[0].rstrip("/") or "/"
    cands = [f"site{p}.html", f"site{p}/index.html", f"site{p}"] if p != "/" else ["site/index.html"]
    if not any(os.path.exists(c) for c in cands):
        bad.append(m)
print("Link check:", "OK" if not bad else f"BROKEN {bad}")
assert not bad

# --- Sitemap ---
sm_path = "site/sitemap.xml"
sm = open(sm_path).read()
if SLUG not in sm:
    entry = f"  <url><loc>{URL}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n"
    sm = sm.replace("</urlset>", entry + "</urlset>")
    open(sm_path, "w").write(sm)
print(f"Sitemap updated: {sm.count('<loc>')} URLs")

# --- Cross-links from sibling posts ---
SIBLINGS = [
    "site/blog/copy-table-from-website-to-excel.html",
    "site/blog/copy-table-website-to-notion.html",
    "site/blog/copy-table-website-to-google-sheets.html",
]
new_link = '<a href="/blog/html-table-to-csv-converter" style="color:var(--color-accent);">HTML table to CSV converter</a>'
for path in SIBLINGS:
    t = open(path).read()
    if SLUG in t:
        print(f"{path}: already links")
        continue
    m = re.search(r'Related:[\s\S]*?</p>', t)
    if m:
        seg = m.group(0)
        t = t.replace(seg, seg.replace("</p>", f" &middot; {new_link}</p>", 1), 1)
        open(path, "w").write(t)
        print(f"{path}: link appended to Related")
    else:
        print(f"{path}: WARNING no Related block found")

# --- Link from the Clean Copy product card on the main page listing blog guides ---
tool = "site/clean-copy-tool.html"
t = open(tool).read()
link_line = 'href="/blog/html-table-to-csv-converter"'
if link_line not in t and 'href="/blog/' in t:
    m = re.search(r'<a href="/blog/[a-z0-9\-]+"[^>]*>[^<]+</a>', t)
    if m:
        seg = m.group(0)
        t = t.replace(seg, f'{seg} &middot; <a href="/blog/{SLUG}" style="color:var(--color-accent);">HTML table to CSV guide</a>', 1)
        open(tool, "w").write(t)
        print(f"{tool}: cross-link added")
    else:
        print(f"{tool}: WARNING no blog link found")
else:
    print(f"{tool}: slug present or no links")

# --- Also cross-link back from the DA sister post (it lists related EN posts) ---
da = "site/blog/html-tabel-til-csv.html"
t = open(da).read()
if "/blog/html-table-to-csv-converter" not in t:
    m = re.search(r'Related:[\s\S]*?</p>', t)
    if m:
        seg = m.group(0)
        t = t.replace(seg, seg.replace("</p>", ' &middot; <a href="/blog/html-table-to-csv-converter" style="color:var(--color-accent);">HTML table to CSV converter (EN)</a></p>', 1), 1)
        open(da, "w").write(t)
        print("DA post: EN cross-link added")
