#!/usr/bin/env python3
"""Iteration 237: EN blogpost — Copy a Table From a Website Into Notion.

Ny post: site/blog/copy-table-website-to-notion (EN-version af den danske post).
- House-template som resten af serien (hero, steps, compare, FAQ)
- Article + FAQPage JSON-LD, valideret efter skrivning
- Sitemap opdateres kun hvis URL'en ikke allerede findes (idempotent)
- Krydslinks: reciprokke links fra DA-posten + soesterposter, hubkort i
  copy-clean-guide, forsidekort paa forsiden.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
URL = f'{BASE}/blog/copy-table-website-to-notion'

desc = ('Copy any table from a website and paste it straight into Notion as real '
        'database rows — every column its own property, no CSV gymnastics. Free '
        'browser method.')

FAQS = [
    ('How do I copy a table from a website into Notion?',
     'Install the free Clean Copy extension for Chrome or Firefox, click the icon '
     'while the table is on screen, choose Copy as Markdown — then paste into a '
     'Notion database view with Ctrl+V (Cmd+V on Mac). Notion turns the markdown '
     'into rows and columns, and the first row becomes the property names.'),
    ('Why do pasted tables end up in one column in Notion?',
     'If the clipboard only holds plain text without consistent separators, Notion '
     'cannot tell where one cell ends and the next begins — so values stack in a '
     'single column. Copying the actual table element as markdown (which Clean Copy '
     'does) preserves the row and column boundaries Notion needs.'),
    ('Can I paste directly into an existing Notion database?',
     'Yes. Open the view you want to fill, select the first target cell and paste. '
     'Notion fills existing properties left to right — check that the column order '
     'matches your properties before pasting.'),
    ('Does it work on tables behind a login?',
     'Yes. Clean Copy runs in your own logged-in browser session, so any table you '
     'can see while signed in can be copied — dashboards, admin panels, SaaS '
     'reports. Server-based scrapers typically fail here.'),
    ('Is anything sent to a server?',
     'No. Clean Copy works entirely inside your browser. The table never leaves '
     'your machine until you paste it where it needs to go yourself.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Copy a Table From a Website Into Notion (Rows and Columns Intact)',
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
<title>Copy a Table From a Website Into Notion (Guide 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Copy a Table From a Website Into Notion">
<meta property="og:description" content="Paste any web table into Notion as real database rows — every column its own property. Free browser method, nothing uploaded.">
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
    <div class="badge">NOTION &middot; TABLES &middot; DATABASES</div>
    <h1>Copy a table from a website<br>into Notion</h1>
    <p class="subtitle">Pricing pages, comparison sites, internal dashboards — the data is already on screen. Getting it into Notion usually means one merged blob of text or manual retyping. Here is the two-click way, with every row becoming a record and every column a property.</p>
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
    <p>The problem is not Notion — it is what reaches the clipboard.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Select + copy grabs too much</h3><p>Drag-selecting a table also catches captions, ads and surrounding text — and cells collapse into one long run of text when pasted.</p></div>
      <div class="card"><h3>🧱 Plain text has no structure</h3><p>Without consistent separators, Notion cannot see where one cell ends and the next begins — everything stacks in a single column.</p></div>
      <div class="card"><h3>⌨️ Retyping does not scale</h3><p>Fine for three rows. Not fine for a 200-row pricing matrix you need refreshed every quarter.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>The method: two clicks</h2>
    <p>The free <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a> extension for Chrome and Firefox converts exactly the table under your cursor into clean markdown — which Notion parses back into rows and columns on paste.</p>

    <h3 style="margin-top:24px;">1. Install</h3>
    <pre class="cmd"><code>Chrome Web Store or Firefox Add-ons — search for "Clean Copy",
install, done.</code></pre>

    <h3 style="margin-top:24px;">2. Copy the table as Markdown</h3>
    <pre class="cmd"><code>Open the page, click anywhere inside the table,
click the Clean Copy icon, choose "Copy as Markdown".</code></pre>

    <h3 style="margin-top:24px;">3. Paste into Notion</h3>
    <pre class="cmd"><code>Create a new database (or open an existing view),
select the first target cell, press Ctrl+V (Cmd+V on Mac).
Each row becomes a page, each column a property —
the first row supplies the property names.

Pasting into an existing database? Check that the
column order matches your properties first.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Rows become records</h3><p>Clean Copy reads the real HTML <code>&lt;table&gt;</code> element, so each <code>&lt;td&gt;</code> lands in its own Notion property automatically.</p></div>
      <div class="card"><h3>🧹 No junk rows</h3><p>No ad fragments, cookie banners or captions — only the table you pointed at.</p></div>
      <div class="card"><h3>🔐 Works behind logins</h3><p>Dashboards, admin panels and SaaS reports all work, because conversion happens in your own logged-in browser session.</p></div>
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
        <tr><td>Select + copy text</td><td>No</td><td>Captures extra content, cells collapse to one column</td></tr>
        <tr><td>Screenshot + OCR</td><td>After cleanup</td><td>Number errors are hard to spot</td></tr>
        <tr><td>CSV download + import</td><td>Sometimes</td><td>Only where the site offers export; loses formatting</td></tr>
        <tr><td>Browser table scrapers</td><td>Often</td><td>Setup per page; break behind logins</td></tr>
        <tr>
          <td><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy — Copy as Markdown</a></td>
          <td>Yes</td>
          <td>Free browser extension required</td>
        </tr>
      </tbody>
    </table>
    <p>If the table sits behind a login or renders dynamically, server-based scrapers and import flows fail — a local copying tool that works in your own session is the reliable option.</p>
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

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/kopier-tabel-hjemmeside-til-notion" style="color:var(--color-accent);">Same guide in Danish</a> &middot; <a href="/blog/copy-table-from-website-to-excel" style="color:var(--color-accent);">Website Table Into Excel</a> &middot; <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Table From Website to Google Sheets</a> &middot; <a href="/blog/copy-table-website-to-airtable" style="color:var(--color-accent);">Table From Website to Airtable</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/"> &larr; Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/copy-clean-guide">Guide collection</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(ROOT, 'site/blog/copy-table-website-to-notion.html')
with open(out, 'w') as f:
    f.write(html)

# --- validate JSON-LD ---
content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

# --- validate internal link targets exist BEFORE anything else ---
for ref in [
    'site/clean-copy.html',
    'site/blog/kopier-tabel-hjemmeside-til-notion.html',
    'site/blog/copy-table-from-website-to-excel.html',
    'site/blog/copy-table-website-to-google-sheets.html',
    'site/blog/copy-table-website-to-airtable.html',
]:
    p = os.path.join(ROOT, ref)
    assert os.path.exists(p), p
print('All internal link targets exist')

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
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

# --- reciprocal cross-links ---
def add_related(path, slug, label, word='Related'):
    x = open(path).read()
    if slug in x:
        return False
    x = x.replace('</body>', '<div style="text-align:center;margin-top:16px;"><p>' + word + ': <a href="' + URL + '" style="color:var(--color-accent);">' + label + '</a></p></div>\n</body>', 1)
    open(path, 'w').write(x)
    return True

for path, label, word in [
    ('site/blog/kopier-tabel-hjemmeside-til-notion.html', 'Copy a Table From a Website Into Notion (EN)', 'Relateret'),
    ('site/blog/copy-table-from-website-to-excel.html', 'Copy a Table From a Website Into Notion', 'Related'),
    ('site/blog/copy-table-website-to-google-sheets.html', 'Copy a Table From a Website Into Notion', 'Related'),
    ('site/blog/copy-table-website-to-airtable.html', 'Copy a Table From a Website Into Notion', 'Related'),
]:
    full = os.path.join(ROOT, path)
    changed = add_related(full, 'copy-table-website-to-notion', label, word)
    print(f'{path}: {"cross-linked" if changed else "already linked"}')

# --- hub card in /copy-clean-guide (idempotent) ---
hub_path = os.path.join(ROOT, 'site/copy-clean-guide.html')
hub = open(hub_path).read()
card = '<a class="hubcard" href="/blog/copy-table-website-to-notion"><h3>Website Table Into Notion (EN)</h3><p>The English version of the Danish Notion guide — same clean paste.</p></a>\n'
if 'copy-table-website-to-notion' not in hub:
    anchor = '<a class="hubcard" href="/blog/copy-table-website-to-notion">'
    # insert after the existing Notion card line if present, else before closing of grid
    marker = '<a class="hubcard" href="/blog/copy-table-website-to-airtable">'
    idx = hub.find(marker)
    assert idx > 0, 'hub airtable card not found'
    end = hub.find('\n', idx) + 1
    hub = hub[:end] + card + hub[end:]
    open(hub_path, 'w').write(hub)
    print('hub card added')
else:
    print('hub already links the new post')

# --- front-page blog card (idempotent) ---
idx_path = os.path.join(ROOT, 'site/index.html')
idx = open(idx_path).read()
if 'blog/copy-table-website-to-notion' not in idx:
    fp_card = '''              <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
                <h3><a href="/blog/copy-table-website-to-notion" style="color:inherit;text-decoration:none;">Copy a Table From a Website Into Notion</a></h3>
                <p>Pasted tables arrive as one merged column in Notion? Two clicks with the free Clean Copy extension — every row a record, every column a property.</p>
                <a href="/blog/copy-table-website-to-notion" class="btn-secondary" style="margin-top:12px;">Read Guide &rarr;</a>
              </div>
'''
    anchor_idx = idx.find('<div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">\n                <h3><a href="/blog/copy-table-from-pdf-to-excel"')
    assert anchor_idx > 0, 'frontpage pdf-card anchor not found'
    idx = idx[:anchor_idx] + fp_card + idx[anchor_idx:]
    open(idx_path, 'w').write(idx)
    print('frontpage card added')
else:
    print('frontpage already links the new post')

print('\nDone:', out)
