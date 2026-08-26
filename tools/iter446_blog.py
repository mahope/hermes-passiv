#!/usr/bin/env python3
"""Iteration 446: two new SEO entries for page-profile distribution.

- site/blog/website-seo-metadata-audit.html (EN)
- site/da/blog/seo-metadata-tjek-hjemmeside.html (DA mirror)
House template, Article+FAQPage JSON-LD (validated), canonical/hreflang pair,
CTA to /page-profile (free CLI + Pro), cross-links to existing SEO posts,
sitemap entries, backlinks from blog index + page-profile footer.
"""
import json, re, os

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-26'
SLUG_EN = 'website-seo-metadata-audit'
SLUG_DA = 'seo-metadata-tjek-hjemmeside'
URL_EN = f'{BASE}/blog/{SLUG_EN}'
URL_DA = f'{BASE}/da/blog/{SLUG_DA}'
ROOT = '/Users/madsholstjensen/hermes-passiv/site'

FAQS_EN = [
    ('What is a website SEO metadata audit?',
     'It is a structured check of everything search engines and social platforms read '
     'before a human does: title tags, meta descriptions, robots directives, canonical '
     'URLs, Open Graph and Twitter cards, heading structure, image alt text and '
     'structured data. A good audit catches problems before they cost rankings or clicks.'),
    ('How do I audit every page of my site without checking them by hand?',
     'Use a crawler-style CLI tool that takes a list of URLs (or your sitemap) and '
     'reports each issue per page. The free page-profile command does exactly this: '
     'point it at a URL and it grades title length, description, canonical, viewport, '
     'Open Graph, headings and alt text in seconds.'),
    ('How long should a title tag and meta description be?',
     'Aim for roughly 50–60 characters for titles and 140–160 characters for meta '
     'descriptions. Longer text is truncated in results pages, which lowers click-through '
     'even when the page still ranks.'),
    ('Is Open Graph really an SEO factor?',
     'Not directly for ranking — but shares on Slack, LinkedIn, Facebook and X drive real '
     'traffic, and a missing og:image or og:title makes those shares look broken. Most '
     'audits treat social metadata as first-class because the traffic impact is measurable.'),
    ('What should I fix first if the audit shows many issues?',
     'Prioritise in this order: missing or duplicated titles and descriptions, wrong or '
     'conflicting canonical URLs, robots noindex on pages that should rank, then social '
     'tags and structured data. The first group affects indexing directly; the rest affect clicks.'),
]

ARTICLE_EN = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Website SEO Metadata Audit: the Complete Pre-Launch Checklist',
    'description': 'Run a full SEO metadata audit on any site: titles, descriptions, canonicals, Open Graph, headings, alt text and structured data — checked automatically, page by page.',
    'url': URL_EN, 'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
}
FAQPAGE_EN = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS_EN],
}

FAQS_DA = [
    ('Hvad er en SEO-metadata-audit?',
     'Et struktureret tjek af alt hvad søgemaskiner og sociale platforme læser, før et '
     'menneske gør: titeltags, meta-beskrivelser, robots-direktiver, kanoniske URL’er, '
     'Open Graph og Twitter-kort, overskriftsstruktur, alt-tekster og strukturerede data.'),
    ('Hvordan tjekker jeg alle sider uden at gå dem manuelt igennem?',
     'Brug et CLI-værktøj der tager en liste af URL’er eller dit sitemap og rapporterer '
     'hvert fund pr. side. Det gratis page-profile-værktøj giver hvert sekund en karakter '
     'for titel, beskrivelse, canonical, viewport, Open Graph, overskrifter og alt-tekster.'),
    ('Hvor lang skal en titel og meta-beskrivelse være?',
     'Cirka 50–60 tegn til titler og 140–160 tegn til meta-beskrivelser. Længere tekst '
     'klippes af i søgeresultaterne, hvilket sænker klikraten selv når siden rangerer.'),
    ('Hvad skal jeg rette først?',
     'I denne rækkefølge: manglende eller duplikerede titler og beskrivelser, forkerte '
     'canonical-URL’er, noindex på sider der skal rangere — derefter sociale tags og '
     'strukturerede data.'),
]

ARTICLE_DA = dict(ARTICLE_EN, headline='SEO- og metadata-tjek af din hjemmeside: den komplette tjekliste',
                  description='Kør et fuldt SEO- og metadata-tjek af enhver side: titler, beskrivelser, canonicals, Open Graph, overskrifter, alt-tekster og strukturerede data.',
                  url=URL_DA)
FAQPAGE_DA = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS_DA],
}
for b in (ARTICLE_EN, FAQPAGE_EN, ARTICLE_DA, FAQPAGE_DA):
    assert b['@context'] == 'https://schema.org'
    json.loads(json.dumps(b, ensure_ascii=False))

STYLE = '''
  .compare {{ width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }}
  .compare th, .compare td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); }}
  pre.cmd {{
    background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px;
    overflow-x:auto; font-size:0.85rem; line-height:1.6; margin:0.8rem 0;
  }}
  pre.cmd code {{ font-family:'SF Mono','Monaco','Fira Code',monospace; }}
'''

TRACK = '''<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});}catch(e){}});
</script>'''


def head(lang, title, desc, url, alt_url, alt_lang, article, faqpage):
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="{alt_lang}" href="{alt_url}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{json.dumps(article, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(faqpage, ensure_ascii=False)}
</script>
<script defer src="/track.js"></script>
<style>{STYLE}</style>
</head>'''


def faq_cards(faqs):
    return '\\n'.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in faqs)


# ---------------- EN ----------------
en_body = f'''
<body>
<header class="hero">
  <div class="container">
    <div class="badge">SEO &middot; METADATA &middot; AUDIT</div>
    <h1>Website SEO Metadata Audit:<br>The Pre-Launch Checklist</h1>
    <p class="subtitle">Before a visitor ever sees your page, Google and every social platform have already read its metadata. Here is what to check on every single page — and how to automate the whole pass instead of eyeballing view-source.</p>
    <div class="hero-cta">
      <a href="#checklist" class="btn-primary">See the checklist &rarr;</a>
      <a href="/page-profile" class="btn-secondary">Run it automatically with page-profile</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 6 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Why metadata breaks quietly</h2>
    <p>Metadata has no visual failure state. A missing canonical, a truncated title or a page with no <code>og:image</code> renders perfectly fine in a browser — and leaks clicks and rankings for months until someone checks.</p>
    <div class="problem-cards">
      <div class="card"><h3>🔍 Nobody views source</h3><p>Title truncation, duplicate descriptions and missing viewport tags are invisible on the rendered page. They only show up in an audit.</p></div>
      <div class="card"><h3>📉 Small errors compound</h3><p>One weak title costs little. Two hundred of them across a site is a systematic ceiling on click-through rate.</p></div>
      <div class="card"><h3>🤝 Shares look broken</h3><p>A link pasted into Slack or LinkedIn with no og:title and og:image looks like spam — even from a trusted domain.</p></div>
    </div>
  </div>
</section>

<section class="products" id="checklist">
  <div class="container">
    <h2>The checklist — what to verify on every page</h2>
    <table class="compare">
      <thead><tr><th>#</th><th>Item</th><th>Pass condition</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>Title tag</td><td>Present, unique, ~50–60 chars, primary keyword first</td></tr>
        <tr><td>2</td><td>Meta description</td><td>Present, unique, ~140–160 chars, has a reason to click</td></tr>
        <tr><td>3</td><td>Canonical URL</td><td>Self-referencing, absolute, no conflicts</td></tr>
        <tr><td>4</td><td>Robots meta</td><td>No accidental <code>noindex</code>/<code>nofollow</code> on indexable pages</td></tr>
        <tr><td>5</td><td>Viewport</td><td><code>width=device-width, initial-scale=1</code> present</td></tr>
        <tr><td>6</td><td>Open Graph</td><td>og:title, og:description, og:image, og:url all set</td></tr>
        <tr><td>7</td><td>Headings</td><td>One H1, logical H2/H3 hierarchy, no skipped levels</td></tr>
        <tr><td>8</td><td>Images</td><td>Every meaningful image has alt text</td></tr>
        <tr><td>9</td><td>Structured data</td><td>Valid JSON-LD where relevant (Article, Product, FAQ)</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products" id="automate">
  <div class="container">
    <h2>Automate the whole pass</h2>
    <p>Checking nine items per page by hand stops being realistic after about ten pages. The free, open-source <a href="/page-profile" style="color:var(--color-accent);">page-profile</a> CLI runs the entire table above against any URL and returns a graded report:</p>
    <pre class="cmd"><code>npx page-profile https://example.com        # single page report
npx page-profile --urls-from-file urls.txt  # batch mode (Pro)
npx page-profile --compare old.html new.html # diff two versions (Pro)</code></pre>
    <div class="problem-cards">
      <div class="card"><h3>✅ Graded, not just listed</h3><p>Each check gets a pass/warn/fail so you can triage instead of reading raw HTML dumps.</p></div>
      <div class="card"><h3>📦 Batch &amp; compare</h3><p>Pro adds batch mode over a URL file, side-by-side compares and shareable HTML reports.</p></div>
      <div class="card"><h3>🔒 Runs locally</h3><p>No account, no upload. Your client's staging URLs never leave your machine.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/page-profile" class="btn-primary">Get page-profile free &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
      {faq_cards(FAQS_EN)}
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/technical-seo-check-website" style="color:var(--color-accent);">Technical SEO Check for Your Website</a> &middot; <a href="/blog/meta-tag-checker" style="color:var(--color-accent);">Meta Tag Checker</a> &middot; <a href="/blog/open-graph-checker" style="color:var(--color-accent);">Open Graph Checker</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/page-profile">page-profile</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
{TRACK}
</body>
</html>'''

en_html = head('en',
    'Website SEO Metadata Audit: the Complete Pre-Launch Checklist',
    ARTICLE_EN['description'], URL_EN, URL_DA, 'da', ARTICLE_EN, FAQPAGE_EN) + en_body

# ---------------- DA ----------------
da_body = f'''
<body>
<header class="hero">
  <div class="container">
    <div class="badge">SEO &middot; METADATA &middot; TJEK</div>
    <h1>SEO- og metadata-tjek<br>af din hjemmeside</h1>
    <p class="subtitle">Før en besøgende ser din side, har Google og alle sociale platforme allerede læst dens metadata. Her er hvad du skal tjekke på hver eneste side — og hvordan du automatiserer hele runden i stedet for at kigge i kildekoden.</p>
    <div class="hero-cta">
      <a href="#tjekliste" class="btn-primary">Se tjeklisten &rarr;</a>
      <a href="/da/page-profile" class="btn-secondary">Kør det automatisk med page-profile</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 6 minutters læsning</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Hvorfor metadata går i stykker i smug</h2>
    <p>Metadata har ingen synlig fejltilstand. En manglende canonical, en klippet titel eller en side uden <code>og:image</code> ser perfekt ud i browseren — og lækker klik og placeringer i måneder, indtil nogen tjekker.</p>
    <div class="problem-cards">
      <div class="card"><h3>🔍 Ingen kigger i kilden</h3><p>Titler der bliver klippet, dubletbeskrivelser og manglende viewport-tags er usynlige på den renderede side. De dukker kun op i en audit.</p></div>
      <div class="card"><h3>📉 Små fejl lægges sammen</h3><p>Én svag titel koster lidt. To hundrede på tværs af et site er en systematisk loft over klikraten.</p></div>
      <div class="card"><h3>🤝 Delinger ser ødelagte ud</h3><p>Et link delt i Slack eller LinkedIn uden og:title og og:image ligner spam — også fra et troværdigt domæne.</p></div>
    </div>
  </div>
</section>

<section class="products" id="tjekliste">
  <div class="container">
    <h2>Tjeklisten — hvad du skal verificere på hver side</h2>
    <table class="compare">
      <thead><tr><th>#</th><th>Punkt</th><th>Krav for at bestå</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>Titel-tag</td><td>Findes, unik, ca. 50–60 tegn, primært nøgleord først</td></tr>
        <tr><td>2</td><td>Meta-beskrivelse</td><td>Findes, unik, ca. 140–160 tegn, giver en grund til at klikke</td></tr>
        <tr><td>3</td><td>Canonical-URL</td><td>Selvrefererende, absolut, ingen konflikter</td></tr>
        <tr><td>4</td><td>Robots-meta</td><td>Ingen utilsigtet <code>noindex</code>/<code>nofollow</code> på sider der skal indexeres</td></tr>
        <tr><td>5</td><td>Viewport</td><td><code>width=device-width, initial-scale=1</code> findes</td></tr>
        <tr><td>6</td><td>Open Graph</td><td>og:title, og:description, og:image og og:url alle sat</td></tr>
        <tr><td>7</td><td>Overskrifter</td><td>Én H1, logisk H2/H3-hierarki, ingen sprunget niveauer</td></tr>
        <tr><td>8</td><td>Billeder</td><td>Hvert meningsfyldt billede har alt-tekst</td></tr>
        <tr><td>9</td><td>Strukturerede data</td><td>Gyldig JSON-LD hvor relevant (Article, Product, FAQ)</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products" id="automatiser">
  <div class="container">
    <h2>Automatisér hele runden</h2>
    <p>At tjekke ni punkter pr. side i hånden holder op med at være realistisk efter cirka ti sider. Det gratis open source-værktøj <a href="/da/page-profile" style="color:var(--color-accent);">page-profile</a> kører hele tabellen ovenfor mod enhver URL og returnerer en karaktergivende rapport:</p>
    <pre class="cmd"><code>npx page-profile https://eksempel.dk          # rapport for én side
npx page-profile --urls-from-file urls.txt   # batch (Pro)
npx page-profile --compare gammel.html ny.html  # sammenlign to versioner (Pro)</code></pre>
    <div class="problem-cards">
      <div class="card"><h3>✅ Karakterer, ikke bare lister</h3><p>Hvert tjek får bestået/advar/dump, så du kan prioritere i stedet for at læse rå HTML-dumps.</p></div>
      <div class="card"><h3>📦 Batch &amp; sammenlign</h3><p>Pro tilføjer batch over en URL-fil, side-om-side-sammenligning og delbare HTML-rapporter.</p></div>
      <div class="card"><h3>🔒 Kører lokalt</h3><p>Ingen konto, intet uploades. Kundens staging-URL’er forlader aldrig din maskine.</p></div>
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/da/page-profile" class="btn-primary">Hent page-profile gratis &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      {faq_cards(FAQS_DA)}
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);">Teknisk SEO-tjek af hjemmesiden</a> &middot; <a href="/da/blog/meta-tjekker" style="color:var(--color-accent);">Meta-tjekker</a> &middot; <a href="/da/blog/open-graph-tjekker" style="color:var(--color-accent);">Open Graph-tjekker</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/da/">&larr; Forside</a> &middot; <a href="/da/page-profile">page-profile</a> &middot; <a href="/">Blog</a></p></footer>
{TRACK}
</body>
</html>'''

da_html = head('da',
    'SEO- og metadata-tjek af din hjemmeside (gratis tjekliste)',
    ARTICLE_DA['description'], URL_DA, URL_EN, 'en', ARTICLE_DA, FAQPAGE_DA) + da_body


def validate(path, expect=2):
    c = open(path).read()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', c, re.DOTALL)
    assert len(blocks) == expect, f'{path}: {len(blocks)} JSON-LD blocks'
    for b in blocks:
        p = json.loads(b)
        assert p['@context'] == 'https://schema.org'
    print(f'OK {path} ({len(c)} bytes, {expect} JSON-LD blocks)')


def write(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(html)


write(f'{ROOT}/blog/{SLUG_EN}.html', en_html)
write(f'{ROOT}/da/blog/{SLUG_DA}.html', da_html)
validate(f'{ROOT}/blog/{SLUG_EN}.html')
validate(f'{ROOT}/da/blog/{SLUG_DA}.html')

# --- internal link targets must exist ---
targets = ['blog/technical-seo-check-website.html', 'blog/meta-tag-checker.html',
           'blog/open-graph-checker.html', 'page-profile.html', 'free-tools.html',
           'da/blog/teknisk-seo-tjek-hjemmeside.html', 'da/blog/meta-tjekker.html',
           'da/blog/open-graph-tjekker.html', 'da/page-profile.html']
for t in targets:
    assert os.path.exists(f'{ROOT}/{t}'), f'MANGLER link-target: {t}'
print('Alle interne link-targets findes')

# --- sitemap ---
sm = f'{ROOT}/sitemap.xml'
c = open(sm).read()
entries = ''.join(
    f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>'
    for u in (URL_EN, URL_DA))
for u in (URL_EN, URL_DA):
    assert u + '</loc>' not in c, f'allerede i sitemap: {u}'
c = c.replace('</urlset>', f'{entries}</urlset>')
open(sm, 'w').write(c)
import xml.dom.minidom
xml.dom.minidom.parseString(c)
print('Sitemap opdateret + gyldig XML')

# --- backlink fra blog-index (EN) ---
bi = f'{ROOT}/blog/index.html'
b = open(bi).read()
assert SLUG_EN not in b
new_li = ('<li style="margin-bottom:20px"><a href="/blog/%s" style="color:var(--color-accent);'
          'font-weight:600;text-decoration:none;font-size:1.02rem">Website SEO Metadata Audit: '
          'the Pre-Launch Checklist</a><br><span style="color:var(--color-text-muted);font-size:0.88rem">'
          'The full metadata checklist — titles, descriptions, canonicals, Open Graph, headings, '
          'alt text and structured data — plus how to run it automatically on every page with '
          'the free page-profile CLI.</span></li>\n') % SLUG_EN
marker = '<li style="margin-bottom:20px"><a href="/blog/technical-seo-check-website"'
idx = b.find(marker)
assert idx > 0, 'marker ikke fundet i blog-index'
b = b[:idx] + new_li + b[idx:]
open(bi, 'w').write(b)
print('Blog-index opdateret')
print('FAERDIG')
