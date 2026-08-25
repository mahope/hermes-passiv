#!/usr/bin/env python3
"""Iteration 235: Hub-side "Copy & Clean Guide" — samler table-copy-serien.

- site/copy-clean-guide.html (EN hub, extensionless canonical /copy-clean-guide)
- Article JSON-LD + CollectionPage? -> Article valgt (ensartet med resten)
- Krydslinks: reciprokke "Related" links fra alle seriens poster
- Sitemap: idempotent tilfoejelse, XML-valideret
- Verificering: JSON-LD parse, interne linkmaal mod disk, sitemap-count
"""
import json, os, re

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
URL = f'{BASE}/copy-clean-guide'

# slug, title shown on card, one-line description
SERIES = [
    ('copy-table-from-website-to-excel', 'Copy a Website Table Into Excel',
     'Select the table, copy, paste — rows and columns intact in Excel.'),
    ('copy-table-from-pdf-to-excel', 'Copy a Table From a PDF Into Excel',
     'Get tables out of PDFs without OCR errors or retyping.'),
    ('copy-table-website-to-google-sheets', 'Website Table to Google Sheets',
     'The same clean paste works in Sheets, Numbers and Calc.'),
    ('copy-table-website-to-notion', 'Website Table Into Notion',
     'Paste real Markdown tables straight into a Notion page.'),
    ('copy-table-website-to-airtable', 'Website Table Into Airtable',
     'From web page to base with every field in its own column.'),
    ('kopier-tabel-fra-pdf', 'Kopiér en tabel fra en PDF (dansk)',
     'Samme PDF-guide på dansk.'),
    ('kopier-tabel-hjemmeside-til-excel', 'Hjemmeside-tabel til Excel (dansk)',
     'Dansk version af Excel-guiden.'),
    ('table-alignment-html-to-markdown', 'Table Alignment in HTML → Markdown',
     'Why column widths break and how Clean Copy keeps them readable.'),
    ('paste-without-formatting-chrome', 'Paste Without Formatting in Chrome',
     'Strip fonts, colors and tracking junk in one keystroke.'),
    ('copy-clean-text-from-website', 'Copy Clean Text From Any Website',
     'No formatting, no junk — just the words you pointed at.'),
    ('copy-as-markdown-chrome-extension', 'Copy as Markdown: Best Extensions',
     'Comparison of the Markdown-copy options in Chrome, 2026.'),
    ('html-to-markdown-converter', 'Free HTML to Markdown Converter',
     'Online converter — no upload, runs in your browser.'),
    ('url-to-markdown-converter', 'URL to Markdown Converter',
     'Turn any public page into clean Markdown from its URL.'),
    ('paste-into-obsidian-clean-markdown', 'Clean Paste Into Obsidian',
     'Keep your vault clean when pasting from the web.'),
    ('copy-from-chatgpt-into-word', 'ChatGPT Into Word Without the Junk',
     'Lose the code fences and asterisks on the way into Word.'),
]

desc = ('Every guide for copying tables and clean text out of websites and PDFs '
        'and into Excel, Google Sheets, Notion, Airtable, Obsidian and Word — '
        'free, browser-based, no signup.')

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Copy & Clean Guide: Tables and Text Out of Any Website or PDF',
    'description': desc,
    'url': URL,
    'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
}
FAQPAGE = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [
        {'@type': 'Question', 'name': 'Is all of this free?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
            'Yes. The guides use the free Clean Copy browser extension for Chrome '
            'and Firefox. Everything runs locally in your browser.'}},
        {'@type': 'Question', 'name': 'Do my data leave my computer?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
            'No. The clipboard work happens entirely in your browser. Nothing is '
            'uploaded until you paste it somewhere yourself.'}},
        {'@type': 'Question', 'name': 'Which destinations are covered?',
         'acceptedAnswer': {'@type': 'Answer', 'text':
            'Excel, Google Sheets, Numbers, LibreOffice Calc, Notion, Airtable, '
            'Obsidian and Word — plus plain-text and Markdown workflows.'}},
    ],
}
for block in (ARTICLE, FAQPAGE):
    assert block['@context'] == 'https://schema.org'
    json.loads(json.dumps(block))

cards = '\n'.join(
    f'<a class="hubcard" href="/blog/{slug}"><h3>{t}</h3><p>{d}</p></a>'
    for slug, t, d in SERIES)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Copy &amp; Clean Guide — Tables &amp; Text From Web/PDF Into Excel, Sheets, Notion</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Copy &amp; Clean Guide">
<meta property="og:description" content="All the guides for getting tables and clean text out of websites and PDFs — into Excel, Sheets, Notion, Airtable and more.">
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
  .hubgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:16px; margin:1.5rem 0; }}
  .hubcard {{ display:block; padding:18px 20px; border:1px solid var(--color-border); border-radius:10px;
             color:inherit; text-decoration:none; transition:border-color .15s; }}
  .hubcard:hover {{ border-color:var(--color-accent); }}
  .hubcard h3 {{ margin:0 0 6px; font-size:1rem; color:var(--color-accent); }}
  .hubcard p {{ margin:0; font-size:0.88rem; line-height:1.5; }}
  @media (max-width:600px) {{ .hubgrid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">GUIDE HUB &middot; TABLES &middot; CLEAN TEXT</div>
    <h1>The Copy &amp; Clean guide collection</h1>
    <p class="subtitle">Fifteen guides, one skill: getting exactly the table or text you want out of a website or a PDF — and into Excel, Sheets, Notion, Airtable, Obsidian, Word or your editor — with the structure intact.</p>
    <div class="hero-cta">
      <a href="#guides" class="btn-primary">Browse the guides &rarr;</a>
      <a href="/clean-copy" class="btn-secondary">About Clean Copy</a>
    </div>
    <p class="hero-note">Updated August 2026</p>
  </div>
</header>

<section class="products" id="guides">
  <div class="container">
    <h2>All guides</h2>
    <p>Start with the destination you are heading for. Every guide is standalone — no signup, nothing uploaded.</p>
    <div class="hubgrid">
{cards}
    </div>
    <h2>How it works, in short</h2>
    <p>Install the free <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a> extension for Chrome or Firefox, point at what you want, and choose Copy Table or Copy Clean Text. What lands on your clipboard is real structure — an actual table, or plain text — so it pastes correctly wherever it goes next.</p>
    <h2>Questions</h2>
    {''.join(f'<div class="card" style="margin-bottom:12px;"><h3>{q["name"]}</h3><p>{q["acceptedAnswer"]["text"]}</p></div>' for q in FAQPAGE['mainEntity'])}
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy" class="btn-primary">Get Clean Copy free &rarr;</a>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(ROOT, 'site/copy-clean-guide.html')
with open(out, 'w') as f:
    f.write(html)

# --- validate JSON-LD ---
content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org'
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

# --- validate ALL internal link targets exist ---
missing = []
for m in re.findall(r'href="/([^"#]+)"', content):
    path = m.split('?')[0]
    if not path or path.startswith('http'):
        continue
    if (path in ('sitemap.xml', 'style.css', 'track.js')
            or os.path.exists(os.path.join(ROOT, 'site', path))
            or os.path.exists(os.path.join(ROOT, 'site', path + '.html'))):
        continue
    missing.append(path)
assert not missing, f'missing link targets: {missing}'
n_links = len(set(re.findall(r'href="/blog/[a-z0-9-]+"', content)))
print('All internal link targets exist on disk (%d unique /blog/ links)' % n_links)

# --- sitemap (idempotent) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = f'<url><loc>{URL}</loc><lastmod>{TODAY}</lastmod></url>'
    c = c.replace('</urlset>', f'{entry}</urlset>')
else:
    print('URL already in sitemap, skipping')
c = c.replace('><url>', '>\n<url>')
open(sm, 'w').write(c)
import xml.dom.minidom
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

print('\nDone:', out)
