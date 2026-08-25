#!/usr/bin/env python3
"""Iteration 234: EN blogpost — Copy a Table From a PDF Into Excel.

Ny post: site/blog/copy-table-from-pdf-to-excel
- House-template som resten af serien (hero, steps, compare, FAQ)
- Article + FAQPage JSON-LD, valideret foer og efter skrivning
- Sitemap opdateres kun hvis URL'en ikke allerede findes (idempotent)
- Krydslinks: reciprokke links fra DA PDF-posten + Excel/Sheets/Notion-soesterposter,
  forsidekort paa forsiden.
"""
import json, os, re

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
URL = f'{BASE}/blog/copy-table-from-pdf-to-excel'

desc = ('Copy a table from a PDF and paste it into Excel or Google Sheets with rows '
        'and columns intact — no OCR errors, no retyping. Free browser method.')

FAQS = [
    ('Why does copying directly from a PDF turn into a mess?',
     'A PDF stores text as positioned blocks, not as a table. When you select and copy, '
     'you usually get each column as its own line of text — all content from row 1 first, '
     'then everything from row 2. The text has to be rebuilt into a real table before it '
     'can be pasted into Excel.'),
    ('Can I avoid using OCR?',
     'In most cases, yes. If the PDF was generated digitally (from Excel or a reporting '
     'tool), the text is already in the file. Clean Copy rebuilds the table from the '
     'page structure instead of reading pixels.'),
    ('What about scanned PDFs?',
     'Scanned PDFs contain images rather than text, so they require OCR (Adobe Acrobat '
     'or an online OCR tool). Always check the numbers afterwards — OCR typically fails '
     'on digits.'),
    ('Does it work with Google Sheets too?',
     'Yes. The clipboard contains ordinary table structure, so it pastes correctly into '
     'Google Sheets, Excel, Numbers and LibreOffice Calc.'),
    ('Do my data leave the browser?',
     'No. Clean Copy runs entirely in your browser. The table never leaves your machine '
     'until you paste it somewhere yourself.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'How to Copy a Table From a PDF Into Excel (Columns Intact)',
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
<title>Copy a Table From a PDF Into Excel (Guide 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Copy a Table From a PDF Into Excel">
<meta property="og:description" content="Get the table out of the PDF and into Excel with rows and columns intact — no OCR errors, no manual retyping.">
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
    <div class="badge">PDF &middot; EXCEL &middot; TABLES</div>
    <h1>Copy a table from a PDF<br>into Excel</h1>
    <p class="subtitle">Annual reports, quarterly statements, public statistics — the tables are locked inside PDFs. Select-and-copy almost always gives you one long blob of text. Here is the way around it, with every column landing where it should.</p>
    <div class="hero-cta">
      <a href="#how" class="btn-primary">Show me how &rarr;</a>
      <a href="/clean-copy" class="btn-secondary">About Clean Copy</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 4 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Why the usual methods fail</h2>
    <p>The problem is not Excel — it is the clipboard. A PDF has no real table structure to hand over.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Direct copy destroys the structure</h3><p>PDF viewers render text in reading order, not table order. The result is typically every value stacked column-wise, one per line.</p></div>
      <div class="card"><h3>📸 Screenshot + OCR = number errors</h3><p>OCR reads pixels, and digits are exactly what it gets wrong most often. One wrong digit in a financial statement is worse than no data.</p></div>
      <div class="card"><h3>⌨️ Retyping does not scale</h3><p>Fine for three rows. Not fine for a 40-page annual report with twenty tables.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>The method: open the PDF in your browser</h2>
    <p>When a PDF opens in Chrome or Firefox, the text is real text on the page — which is what the <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a> extension works with. It has a dedicated Copy Table mode that finds the table under your cursor and puts genuine table structure on the clipboard.</p>

    <h3 style="margin-top:24px;">1. Install</h3>
    <pre class="cmd"><code>Chrome Web Store or Firefox Add-ons — search for "Clean Copy", install, done.</code></pre>

    <h3 style="margin-top:24px;">2. Open the PDF in the browser</h3>
    <pre class="cmd"><code>Drag the PDF file into a Chrome or Firefox window,
then scroll to the table.</code></pre>

    <h3 style="margin-top:24px;">3. Copy the table</h3>
    <pre class="cmd"><code>Click anywhere inside the table, click the Clean Copy
icon and choose "Copy table".</code></pre>

    <h3 style="margin-top:24px;">4. Paste into Excel</h3>
    <pre class="cmd"><code>Click cell A1 and press Ctrl+V (Cmd+V on Mac).
Every value lands in its own cell — headers included.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Cells stay cells</h3><p>The clipboard carries real table structure, so Excel maps each value to the right cell.</p></div>
      <div class="card"><h3>🧹 No junk included</h3><p>No page headers, footer page numbers or running text — only the table you pointed at.</p></div>
      <div class="card"><h3>🔁 Works elsewhere too</h3><p>The same paste works in Google Sheets, Numbers and LibreOffice Calc.</p></div>
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
        <tr><td>Select + copy in the PDF viewer</td><td>Rarely</td><td>Text arrives in reading order, columns collapse</td></tr>
        <tr><td>Screenshot + OCR</td><td>After cleanup</td><td>Number errors are hard to spot</td></tr>
        <tr><td>Acrobat "Export to spreadsheet"</td><td>Yes</td><td>Paid subscription required; slow with many tables</td></tr>
        <tr><td>Excel Data tab "Get Data From PDF"</td><td>Yes</td><td>Requires Microsoft 365; struggles with complex layouts</td></tr>
        <tr>
          <td><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy — Copy Table</a></td>
          <td>Yes</td>
          <td>Free browser extension required; PDF opened in the browser</td>
        </tr>
      </tbody>
    </table>
    <p>If you already have Microsoft 365 or Acrobat, their built-in exports can be fine for occasional large tables. For quick copies — and for free — the browser route is the simplest.</p>
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

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/copy-table-from-website-to-excel" style="color:var(--color-accent);">Copy a Website Table Into Excel</a> &middot; <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Table From Website to Google Sheets</a> &middot; <a href="/blog/kopier-tabel-fra-pdf" style="color:var(--color-accent);">Same guide in Danish</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/"> &larr; Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(ROOT, 'site/blog/copy-table-from-pdf-to-excel.html')
with open(out, 'w') as f:
    f.write(html)

# --- validate JSON-LD ---
content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {{len(blocks)}}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

# --- validate internal link targets exist BEFORE writing anything else ---
for ref in [
    'site/clean-copy.html',
    'site/blog/kopier-tabel-fra-pdf.html',
    'site/blog/copy-table-from-website-to-excel.html',
    'site/blog/copy-table-website-to-google-sheets.html',
]:
    p = os.path.join(ROOT, ref)
    assert os.path.exists(p), p
print('All internal link targets exist')

# --- sitemap (idempotent, one entry per line after formatting) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = f'<url><loc>{URL}</loc><lastmod>{TODAY}</lastmod></url>'
    c = c.replace('</urlset>', f'{entry}</urlset>')
else:
    print('URL already in sitemap, skipping')
# pretty-format: newline between entries
c = c.replace('><url>', '>\n<url>')
open(sm, 'w').write(c)
import xml.dom.minidom
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

# --- reciprocal cross-links ---
def add_related(path, slug, label):
    x = open(path).read()
    if slug in x:
        return False
    x = x.replace('</body>', '<div style="text-align:center;margin-top:16px;"><p>Related: <a href="' + URL + '" style="color:var(--color-accent);">' + label + '</a></p></div>\n</body>', 1)
    open(path, 'w').write(x)
    return True

for path, label in [
    ('site/blog/kopier-tabel-fra-pdf.html', 'Copy a Table From a PDF Into Excel (EN)'),
    ('site/blog/copy-table-from-website-to-excel.html', 'Copy a Table From a PDF Into Excel'),
    ('site/blog/copy-table-website-to-google-sheets.html', 'Copy a Table From a PDF Into Sheets/Excel'),
    ('site/blog/copy-table-website-to-notion.html', 'Copy a Table From a PDF Into Notion'),
]:
    full = os.path.join(ROOT, path)
    changed = add_related(full, 'copy-table-from-pdf-to-excel', label)
    print(f'{path}: {"cross-linked" if changed else "already linked"}')

print('\nDone:', out)
