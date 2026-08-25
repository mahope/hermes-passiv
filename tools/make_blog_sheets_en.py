#!/usr/bin/env python3
"""Iteration 226: EN blogpost — copy a website table into Google Sheets.

New: site/blog/copy-table-website-to-google-sheets.html
- House blog template (hero, steps, compare table, FAQ)
- Article + FAQPage JSON-LD, both json.loads-validated before and after write
- Links to /clean-copy, /blog/copy-table-from-website-to-excel,
  /blog/html-to-markdown-cli; sitemap updated; cross-link added back
  from the Excel post.
"""
import json, os, re

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
URL = f'{BASE}/blog/copy-table-website-to-google-sheets'

desc = ('Copy any table from a website straight into Google Sheets with rows and '
        'columns intact — no screenshot OCR, no re-typing, no add-ons.')

FAQS = [
    ('How do I copy a table from a website into Google Sheets?',
     'Install the free Clean Copy extension for Chrome or Firefox, click its icon '
     'while the table is on screen, choose Copy Table, then paste into your sheet '
     'with Ctrl+V (Cmd+V on Mac). Every cell lands in its own row and column.'),
    ('Why does pasting a table sometimes end up in one column?',
     'If you select the text instead of the table element, the browser copies plain '
     'text and Sheets has no structure to work with. Copying the table itself '
     '(as Clean Copy does) preserves HTML table semantics, which Sheets understands.'),
    ('Does it also work in Excel?',
     'Yes — the same clipboard content pastes cleanly into Excel, Numbers and LibreOffice '
     'Calc. We have a separate guide for Excel with more detail.'),
    ('What about tables that load when I scroll?',
     'Scroll to the part of the table you need first so the rows exist in the page, '
     'then copy. Lazy-loaded rows that have never rendered cannot be copied because '
     'they are not in the document yet.'),
    ('Is anything uploaded to a server?',
     'No. Clean Copy works entirely inside your browser. The table never leaves your '
     'machine until you paste it where you want it.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Copy a Table From a Website Into Google Sheets (Rows and Columns Intact)',
    'description': desc,
    'url': URL,
    'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
}
FAQPAGE = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS],
}
for block in (ARTICLE, FAQPAGE):
    assert block['@context'] == 'https://schema.org', block['@context']
    json.loads(json.dumps(block))

faq_html = '\n'.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Copy a Table From a Website Into Google Sheets (2026 Guide)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Copy a Table From a Website Into Google Sheets">
<meta property="og:description" content="Paste any web table into Google Sheets with every cell in place — no OCR, no re-typing, no add-ons.">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
<meta property="og:url" content="{URL}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{URL}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{json.dumps(ARTICLE, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(FAQPAGE, ensure_ascii=False)}
</script>
<script defer src="/track.js"></script>
<style>
  .compare {{ width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }}
  .compare th, .compare td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); }}
  pre.cmd {{
    background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px;
    overflow-x:auto; font-size:0.85rem; line-height:1.6; margin:0.8rem 0;
  }}
  pre.cmd code {{ font-family:'SF Mono','Monaco','Fira Code',monospace; }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">SPREADSHEETS &middot; GOOGLE SHEETS &middot; TABLES</div>
    <h1>Copy a Table From a Website<br>Into Google Sheets</h1>
    <p class="subtitle">Pricing pages, league tables, government statistics — getting them into Sheets usually means one giant text blob or hours of re-typing. Here is the two-click way that keeps every row and column exactly where it belongs.</p>
    <div class="hero-cta">
      <a href="#how" class="btn-primary">Show me the 2-click way &rarr;</a>
      <a href="/clean-copy" class="btn-secondary">About Clean Copy</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 4 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Why the usual methods fail</h2>
    <p>Google Sheets is happy to receive a real HTML table — the problem is getting one onto your clipboard without mangling it.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Select-and-copy grabs text</h3><p>Drag-select across a table and you often capture surrounding paragraphs, ads and captions. Pasted into Sheets, everything collapses into a few overloaded cells.</p></div>
      <div class="card"><h3>📸 Screenshots need OCR</h3><p>Screenshotting the table means running it through OCR software and fixing the errors it introduces. Numbers with wrong digits are worse than no numbers.</p></div>
      <div class="card"><h3>⌨️ Re-typing does not scale</h3><p>Fine for three rows. Not fine for the 200-row dataset behind that public dashboard.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>The fix: two clicks</h2>
    <p>The free <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a> extension for Chrome and Firefox has a dedicated Copy Table mode. It finds the real <code>&lt;table&gt;</code> element under your cursor and puts proper structured data on the clipboard.</p>

    <h3 style="margin-top:24px;">1. Install</h3>
    <pre class="cmd"><code>Chrome Web Store or Firefox Add-ons — search "Clean Copy", install, done.</code></pre>

    <h3 style="margin-top:24px;">2. Copy the table</h3>
    <pre class="cmd"><code>Open the page, click anywhere inside the table,
click the Clean Copy icon, choose "Copy table".</code></pre>

    <h3 style="margin-top:24px;">3. Paste into Sheets</h3>
    <pre class="cmd"><code>Click cell A1 in your sheet, press Ctrl+V (Cmd+V on Mac).
Every value lands in its own cell — headers included.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Cells stay cells</h3><p>Because the clipboard carries real table semantics, Sheets maps each <code>&lt;td&gt;</code> to its own cell automatically.</p></div>
      <div class="card"><h3>🧹 No junk rows</h3><p>No ad fragments, cookie banners or captions — only the table you pointed at.</p></div>
      <div class="card"><h3>🔁 Works beyond Sheets</h3><p>The same paste works in Excel, Numbers and LibreOffice Calc.</p></div>
    </div>
  </div>
</section>

<section class="products" id="options">
  <div class="container">
    <h2>Your options compared</h2>
    <table class="compare">
      <thead>
        <tr><th>Method</th><th>Keeps structure?</th><th>Catch</th></tr>
      </thead>
      <tbody>
        <tr><td>Select + copy text</td><td>Rarely</td><td>Grabs extra content, collapses columns</td></tr>
        <tr><td>Screenshot + OCR</td><td>After cleanup</td><td>Digit errors are hard to spot</td></tr>
        <tr><td>Sheets IMPORTHTML formula</td><td>Yes</td><td>Only public pages; breaks on JS-rendered tables</td></tr>
        <tr>
          <td><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy — Copy table</a></td>
          <td>Yes</td>
          <td>Free browser extension install required</td>
        </tr>
      </tbody>
    </table>
    <p>If your table lives behind a login or loads dynamically, the formula route fails and a local copy tool is the reliable option.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy" class="btn-primary">Get Clean Copy free &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/copy-table-from-website-to-excel" style="color:var(--color-accent);">Copy a Table From a Website Into Excel</a> &middot; <a href="/blog/html-to-markdown-cli" style="color:var(--color-accent);">HTML to Markdown From the Terminal</a> &middot; <a href="/blog/paste-without-formatting-chrome" style="color:var(--color-accent);">Paste Without Formatting in Chrome</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = '/Users/madsholstjensen/hermes-passiv/site/blog/copy-table-website-to-google-sheets.html'
with open(out, 'w') as f:
    f.write(html)

# --- validate JSON-LD ---
content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print(f'JSON-LD block {i+1}: OK (@type={parsed["@type"]})')

# --- validate internal links exist ---
for ref in [
    '/Users/madsholstjensen/hermes-passiv/site/clean-copy.html',
    '/Users/madsholstjensen/hermes-passiv/site/blog/copy-table-from-website-to-excel.html',
    '/Users/madsholstjensen/hermes-passiv/site/blog/html-to-markdown-cli.html',
    '/Users/madsholstjensen/hermes-passiv/site/blog/paste-without-formatting-chrome.html',
]:
    assert os.path.exists(ref), ref
print('All internal link targets exist')

# --- sitemap ---
sm = '/Users/madsholstjensen/hermes-passiv/site/sitemap.xml'
c = open(sm).read()
entry = f'<url><loc>{URL}</loc><lastmod>{TODAY}</lastmod></url>'
assert URL + '</loc>' not in c, 'already in sitemap'
c = c.replace('</urlset>', f'{entry}</urlset>')
open(sm, 'w').write(c)
import xml.dom.minidom
xml.dom.minidom.parse(sm)
print('sitemap updated + parses as XML,', c.count('<url>'), 'urls')

# --- reciprocal link from the Excel post ---
xl = '/Users/madsholstjensen/hermes-passiv/site/blog/copy-table-from-website-to-excel.html'
x = open(xl).read()
if 'copy-table-website-to-google-sheets' not in x:
    x = x.replace('</body>', '<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Copy a Table Into Google Sheets</a></p></div>\n</body>', 1)
    open(xl, 'w').write(x)
print('Excel post cross-linked:', 'copy-table-website-to-google-sheets' in open(xl).read())

print('\nDone:', out)
