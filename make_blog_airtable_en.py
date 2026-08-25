#!/usr/bin/env python3
"""Iteration 229: ny blogpost "Copy a Table From a Website Into Airtable" (EN).
Samme mønster som Notion-posten: Article + FAQPage JSON-LD, canonical, FAQ,
sammenligningstabel, CTA til /clean-copy. Tilføjer også posten i sitemap.xml
og gensidige krydslinks fra 3 søsterposter (Notion, Sheets, Excel)."""

import json, re

SLUG = "copy-table-website-to-airtable"
URL = f"https://hermes-passiv.pages.dev/blog/{SLUG}"

ARTICLE_LD = {
    "@context": "https://schema.org", "@type": "Article",
    "headline": "Copy a Table From a Website Into Airtable (Rows and Columns Intact)",
    "description": "Get any web table into Airtable as real records — every row a record, every column a field. No CSV gymnastics, no OCR, no re-typing.",
    "url": URL, "datePublished": "2026-08-25", "dateModified": "2026-08-25",
    "author": {"@type": "Organization", "name": "Hermes Compliance"},
    "publisher": {"@type": "Organization", "name": "Hermes Compliance"},
}

FAQS = [
    ("How do I copy a table from a website into Airtable?",
     "Install the free Clean Copy extension for Chrome or Firefox, click its icon while the table is on screen, choose Copy as Markdown, then create a new Airtable base and paste with Ctrl+V (Cmd+V on Mac) into the grid view. Airtable parses the pasted markdown into records and fields, using your first row as field names."),
    ("Why does pasting a table into Airtable sometimes end up in one column?",
     "If the clipboard only carries plain text without consistent delimiters, Airtable cannot tell where one cell ends and the next begins, so values stack in a single field. Copying the table element itself as markdown (as Clean Copy does) preserves the row and column boundaries Airtable needs."),
    ("Can I paste data straight into an existing Airtable base?",
     "Yes. Open the grid view of the table you want to fill, select the first cell where the data should land, and paste. Airtable fills existing fields left to right — so make sure your copied column order matches your field order before you paste."),
    ("Does this work on tables behind a login?",
     "Yes. Clean Copy runs inside your own browser session, so any table you can see while logged in can be copied — dashboards, admin panels, SaaS reports. Server-side scrapers usually fail here."),
    ("Is anything uploaded to a server?",
     "No. Clean Copy works entirely inside your browser. The table never leaves your machine until you paste it where you want it."),
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
<title>Copy a Table From a Website Into Airtable (2026 Guide)</title>
<meta name="description" content="Paste any table from a website into Airtable as real records — rows become records, columns become fields. No CSV round-trips, no OCR, no manual re-typing.">
<meta property="og:type" content="article">
<meta property="og:title" content="Copy a Table From a Website Into Airtable">
<meta property="og:description" content="Paste any web table into Airtable with every cell in place — no OCR, no re-typing, no CSV gymnastics.">
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
    <div class="badge">AIRTABLE &middot; TABLES &middot; NO-CODE</div>
    <h1>Copy a Table From a Website<br>Into Airtable</h1>
    <p class="subtitle">Competitor pricing, lead lists, research data — getting a live web table into Airtable usually means a fragile CSV export or an hour of fixing cells by hand. Here is the two-click way that lands as real records.</p>
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
    <p>Airtable wants structured rows and columns. The hard part is getting them off a live web page intact.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Select-and-copy grabs text</h3><p>Drag-select across a table often captures surrounding paragraphs, ads and captions. Pasted into Airtable, the structure is gone — values collapse or land in the wrong fields.</p></div>
      <div class="card"><h3>📸 Screenshots need OCR</h3><p>A screenshot is just pixels to Airtable. You end up running OCR and fixing the digit errors it introduces — worse than re-typing.</p></div>
      <div class="card"><h3>⌨️ CSV round-trips are fragile</h3><p>Some sites offer a CSV download, but then you need Airtable's import flow, and merged headers, footnotes and formatting disappear anyway.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>The fix: two clicks</h2>
    <p>The free <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a> extension for Chrome and Firefox converts exactly the table under your cursor into clean markdown — which Airtable parses into records and fields on paste.</p>

    <h3 style="margin-top:24px;">1. Install</h3>
    <pre class="cmd"><code>Chrome Web Store or Firefox Add-ons — search "Clean Copy", install, done.</code></pre>

    <h3 style="margin-top:24px;">2. Copy the table as markdown</h3>
    <pre class="cmd"><code>Open the page, click anywhere inside the table,
click the Clean Copy icon, choose "Copy as Markdown".</code></pre>

    <h3 style="margin-top:24px;">3. Paste into Airtable</h3>
    <pre class="cmd"><code>Create a new base (or open an existing grid view),
select the first target cell, press Ctrl+V (Cmd+V on Mac).
Every row becomes a record, every column a field —
your first row becomes the field names.

Pasting into an existing table? Check that your
column order matches the field order first.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Rows stay records</h3><p>Clean Copy reads the real HTML <code>&lt;table&gt;</code> element, so every <code>&lt;td&gt;</code> maps to its own field value in Airtable automatically.</p></div>
      <div class="card"><h3>🧹 No junk rows</h3><p>No ad fragments, cookie banners or captions — only the table you pointed at.</p></div>
      <div class="card"><h3>🔐 Works behind logins</h3><p>Dashboards, admin panels and SaaS reports all work, because the conversion happens in your own logged-in browser session.</p></div>
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
        <tr><td>Select + copy text</td><td>No</td><td>Grabs extra content, cells collapse into one field</td></tr>
        <tr><td>Screenshot + OCR</td><td>After cleanup</td><td>Digit errors are hard to spot</td></tr>
        <tr><td>CSV download + import</td><td>Sometimes</td><td>Only where the site offers export; loses formatting</td></tr>
        <tr><td>Browser table-scrapers</td><td>Often</td><td>Setup overhead per site; struggle behind logins</td></tr>
        <tr>
          <td><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy — Copy as Markdown</a></td>
          <td>Yes</td>
          <td>Free browser extension install required</td>
        </tr>
      </tbody>
    </table>
    <p>If the table lives behind a login or renders dynamically, server-side scrapers and import flows fail — a local copy tool that works in your session is the reliable option.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
__FAQCARDS__
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy" class="btn-primary">Get Clean Copy free &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/copy-table-website-to-notion" style="color:var(--color-accent);">Copy a Table From a Website Into Notion</a> &middot; <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Copy a Table From a Website Into Google Sheets</a> &middot; <a href="/blog/paste-into-obsidian-clean-markdown" style="color:var(--color-accent);">Paste Into Obsidian as Clean Markdown</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
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

# --- Verify JSON-LD blocks parse and @context is correct ---
raw = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.DOTALL)
for b in blocks:
    parsed = json.loads(b)
    assert parsed["@context"] == "https://schema.org", parsed["@context"]
print(f"Wrote {out} ({len(raw)} bytes), {len(blocks)} JSON-LD blocks OK")

# --- Sitemap ---
sm_path = "site/sitemap.xml"
sm = open(sm_path).read()
if SLUG not in sm:
    entry = f"  <url><loc>{URL}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n"
    sm = sm.replace("</urlset>", entry + "</urlset>")
    open(sm_path, "w").write(sm)
count = sm.count("<loc>")
print(f"Sitemap updated: {count} URLs")

# --- Cross-links from sibling posts (bidirectional) ---
SIBLINGS = {
    "site/blog/copy-table-website-to-notion.html":
        '<a href="/blog/copy-table-website-to-notion" style="color:var(--color-accent);">Copy a Table From a Website Into Notion</a>',
    "site/blog/copy-table-website-to-google-sheets.html":
        '<a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Copy a Table From a Website Into Google Sheets</a>',
    "site/blog/copy-table-from-website-to-excel.html":
        '<a href="/blog/copy-table-from-website-to-excel" style="color:var(--color-accent);">Copy a Table From a Website Into Excel</a>',
}
new_link = '<a href="/blog/copy-table-website-to-airtable" style="color:var(--color-accent);">Copy a Table From a Website Into Airtable</a>'
for path, old_link in SIBLINGS.items():
    t = open(path).read()
    if SLUG in t:
        print(f"{path}: already links")
        continue
    if old_link in t:
        t = t.replace(old_link, old_link + " &middot; " + new_link, 1)
        open(path, "w").write(t)
        print(f"{path}: link added")
    else:
        # fallback: append to Related paragraph
        m = re.search(r'(Related:[^<]*<p>.*?</p>|Related:.*?</p>)', t, re.DOTALL)
        if m:
            seg = m.group(0)
            t = t.replace(seg, seg.replace("</p>", f" &middot; {new_link}</p>", 1), 1)
            open(path, "w").write(t)
            print(f"{path}: link appended to Related")
        else:
            print(f"{path}: WARNING no Related block found")
