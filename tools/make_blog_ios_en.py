#!/usr/bin/env python3
"""Iteration 238: EN blogpost — Copy a Table on iPhone & iPad (iOS Safari).

Ny post: site/blog/copy-table-website-iphone-ipad (EN).
- House-template som resten af serien (hero, steps, compare, FAQ)
- Article + FAQPage JSON-LD, valideret efter skrivning
- Sitemap opdateres kun hvis URL'en ikke allerede findes (idempotent)
- Krydslinks fra soesterposter + bookmarklet-siden, hubkort, forsidekort.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
URL = f'{BASE}/blog/copy-table-website-iphone-ipad'

desc = ('How to copy a table from a website on iPhone and iPad — and get it into '
        'Notes, Numbers, Excel or Notion with rows and columns intact. Free Safari '
        'bookmarklet method, no app required.')

FAQS = [
    ('Can you copy a table from a website on an iPhone?',
     'Yes. The trick is a Safari bookmarklet: save any page as a bookmark, edit it '
     'and paste in the Clean Copy bookmarklet address. Open the page with the table, '
     'tap the bookmark — the table is copied as clean Markdown, ready to paste '
     'anywhere as rows and columns.'),
    ('Why does pasting a table into Notes give me one blob of text?',
     'A normal copy grabs plain text without separators, so iOS has no way to know '
     'where one cell ends and the next begins. Copying the table element itself as '
     'Markdown preserves row and column boundaries, which apps like Notion, Obsidian '
     'and Craft parse back into a real structure.'),
    ('Does this work in Chrome or Firefox on iOS?',
     'Yes — every browser on iPhone and iPad uses WebKit under the hood, and the '
     'bookmarklet method works wherever bookmarks can be edited. In most iOS '
     'browsers that means adding a bookmark manually and replacing its address, '
     'exactly like in Safari.'),
    ('Can I get the table into Excel or Numbers on iPad?',
     'Copy the table with the bookmarklet, open Numbers or Excel, tap the first '
     'target cell and paste. Tabular clipboard content is split into cells '
     'automatically — check the column order matches your sheet before pasting.'),
    ('Is anything sent to a server?',
     'No. The bookmarklet runs entirely inside your browser. The table never leaves '
     'your device until you paste it where it needs to go yourself.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Copy a Table From a Website on iPhone & iPad (Rows and Columns Intact)',
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
<title>Copy a Table From a Website on iPhone &amp; iPad (Guide 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Copy a Table From a Website on iPhone &amp; iPad">
<meta property="og:description" content="Get any web table into Notes, Numbers, Excel or Notion on iOS with rows and columns intact. Free Safari bookmarklet method.">
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
    <div class="badge">IOS &middot; SAFARI &middot; TABLES</div>
    <h1>Copy a table from a website<br>on iPhone &amp; iPad</h1>
    <p class="subtitle">Pricing pages, comparison tables, sports stats — the data is right there in Safari on your phone. But long-press copy gives you one merged blob of text, and there is no extension store for iOS Safari. Here is the free workaround that keeps every row and column.</p>
    <div class="hero-cta">
      <a href="#how" class="btn-primary">Show me how &rarr;</a>
      <a href="/clean-copy-bookmarklet" class="btn-secondary">Get the Bookmarklet</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 4 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Why copying tables on iOS usually fails</h2>
    <p>The problem is not your iPhone — it is what reaches the clipboard.</p>
    <div class="problem-cards">
      <div class="card"><h3>👆 Long-press copy grabs one cell</h3><p>iOS selects the single cell you pressed, not the whole table — and dragging to extend the selection across a table is unreliable at best.</p></div>
      <div class="card"><h3>🧱 Plain text has no structure</h3><p>Even when you manage to select the whole table, it arrives as unseparated text. Apps cannot tell where one column ends and the next begins.</p></div>
      <div class="card"><h3>🚫 No desktop extensions</h3><p>Safari on iOS supports Web Extensions only since iOS 15, and installing them is nothing like the one-click stores on desktop. Most people never bother.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>The method: a Safari bookmarklet</h2>
    <p>The free <a href="/clean-copy-bookmarklet" style="color:var(--color-accent);">Clean Copy bookmarklet</a> converts exactly the table you point at into clean Markdown — no install, no account, works in Safari on any iPhone or iPad.</p>

    <h3 style="margin-top:24px;">1. Create the bookmark (once)</h3>
    <pre class="cmd"><code>Open the Clean Copy bookmarklet page in Safari.
Copy the bookmarklet link.
Tap Share → Add Bookmark → save it
(any page works as a placeholder).</code></pre>

    <h3 style="margin-top:24px;">2. Edit the bookmark's address</h3>
    <pre class="cmd"><code>Open Bookmarks, find the new bookmark,
tap Edit and replace the address field with
the bookmarklet link you copied. Save.</code></pre>

    <h3 style="margin-top:24px;">3. Copy the table</h3>
    <pre class="cmd"><code>Open the page with the table in Safari.
Type the bookmark's name in the address bar
and tap it. Choose "Copy as Markdown".
The whole table is now on your clipboard.</code></pre>

    <h3 style="margin-top:24px;">4. Paste anywhere</h3>
    <pre class="cmd"><code>Notes / Craft / Obsidian: paste as-is for a real table.
Numbers / Excel: tap the first target cell and paste —
each value lands in its own cell.
Notion: paste into a database view for rows + properties.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Structure survives</h3><p>Clean Copy reads the real HTML <code>&lt;table&gt;</code>, so every <code>&lt;td&gt;</code> lands where it belongs after paste.</p></div>
      <div class="card"><h3>🧹 No junk rows</h3><p>No ads, cookie banners or captions — only the table you pointed at.</p></div>
      <div class="card"><h3>🔐 Nothing leaves your device</h3><p>The conversion runs inside Safari itself. No server, no upload, works behind logins too.</p></div>
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
        <tr><td>Long-press + Copy</td><td>No</td><td>Selects one cell; multi-cell selection collapses to text</td></tr>
        <tr><td>Screenshot + OCR</td><td>After cleanup</td><td>Number errors are hard to spot on small screens</td></tr>
        <tr><td>"Open in desktop Excel" flows</td><td>Sometimes</td><td>Only where the site offers export</td></tr>
        <tr><td>Third-party scanner apps</td><td>Often</td><td>Paid, per-app setup, privacy questions</td></tr>
        <tr>
          <td><a href="/clean-copy-bookmarklet" style="color:var(--color-accent);">Clean Copy bookmarklet — Copy as Markdown</a></td>
          <td>Yes</td>
          <td>One-time manual bookmark edit</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy-bookmarklet" class="btn-primary">Get the free bookmarklet &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/copy-table-from-website-to-excel" style="color:var(--color-accent);">Website Table Into Excel</a> &middot; <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Table From Website to Google Sheets</a> &middot; <a href="/blog/copy-table-website-to-notion" style="color:var(--color-accent);">Table Into Notion</a> &middot; <a href="/blog/paste-without-formatting-chrome" style="color:var(--color-accent);">Paste Without Formatting</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/"> &larr; Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/copy-clean-guide">Guide collection</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(ROOT, 'site/blog/copy-table-website-iphone-ipad.html')
with open(out, 'w') as f:
    f.write(html)

# fix stray typo guard: ensure no broken tags slipped in
content = open(out).read()
assert '</pre-code>' not in content, 'stray tag found'

# --- validate JSON-LD ---
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

# --- validate internal link targets exist ---
refs = re.findall(r'href="(/\w[\w/-]*)"', content)
missing = []
for ref in set(refs):
    if ref.startswith('/api'):
        continue
    p = os.path.join(ROOT, 'site', ref.lstrip('/') + '.html')
    if not os.path.exists(p):
        missing.append(ref)
assert not missing, missing
print('All internal link targets exist:', len(set(refs)), 'checked')

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
    ('site/blog/copy-table-from-website-to-excel.html', 'Copy a Table From a Website on iPhone & iPad', 'Related'),
    ('site/blog/copy-table-website-to-google-sheets.html', 'Copy a Table From a Website on iPhone & iPad', 'Related'),
    ('site/blog/copy-table-website-to-notion.html', 'Copy a Table From a Website on iPhone & iPad', 'Related'),
    ('site/blog/paste-without-formatting-chrome.html', 'Copy Tables on iPhone & iPad', 'Related'),
]:
    full = os.path.join(ROOT, path)
    changed = add_related(full, 'copy-table-website-iphone-ipad', label, word)
    print(f'{path}: {"cross-linked" if changed else "already linked"}')

# --- hub card in /copy-clean-guide (idempotent) ---
hub_path = os.path.join(ROOT, 'site/copy-clean-guide.html')
hub = open(hub_path).read()
if 'copy-table-website-iphone-ipad' not in hub:
    card = '<a class="hubcard" href="/blog/copy-table-website-iphone-ipad"><h3>Copy Tables on iPhone &amp; iPad</h3><p>The Safari bookmarklet method — rows and columns intact, no app needed.</p></a>\n'
    marker = '<a class="hubcard" href="/blog/copy-table-website-to-notion">'
    idx = hub.find(marker)
    assert idx > 0, 'hub notion card not found'
    end = hub.find('\n', idx) + 1
    hub = hub[:end] + card + hub[end:]
    open(hub_path, 'w').write(hub)
    print('hub card added')
else:
    print('hub already links the new post')

# --- front-page blog card (idempotent) ---
idx_path = os.path.join(ROOT, 'site/index.html')
idx = open(idx_path).read()
if 'blog/copy-table-website-iphone-ipad' not in idx:
    fp_card = '''              <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
                <h3><a href="/blog/copy-table-website-iphone-ipad" style="color:inherit;text-decoration:none;">Copy a Table From a Website on iPhone &amp; iPad</a></h3>
                <p>Long-press copy gives you one blob of text? A free Safari bookmarklet copies any web table with rows and columns intact — straight into Notes, Numbers, Excel or Notion.</p>
                <a href="/blog/copy-table-website-iphone-ipad" class="btn-secondary" style="margin-top:12px;">Read Guide &rarr;</a>
              </div>
'''
    anchor_idx = idx.find('<div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">\n                <h3><a href="/blog/copy-table-website-to-notion"')
    assert anchor_idx > 0, 'frontpage notion-card anchor not found'
    idx = idx[:anchor_idx] + fp_card + idx[anchor_idx:]
    open(idx_path, 'w').write(idx)
    print('frontpage card added')
else:
    print('frontpage already links the new post')

print('\nDone:', out)
