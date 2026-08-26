#!/usr/bin/env python3
"""Iteration 450: hreflang hygiene + new Hreflang Guide blog pair (EN+DA).

1. Fix: all DA mirror pages with an hreflang set lacked the x-default link
   (iter 448 claimed complete sets — EN pages had it, DA pages did not).
   Adds <link rel="alternate" hreflang="x-default" href="<EN mirror URL>">
   right before the first existing hreflang link on each affected page.
2. New blog post pair targeting "hreflang guide" / "hreflang guide dansk":
   site/blog/hreflang-guide.html + site/da/blog/hreflang-guide-da.html,
   Article+FAQPage JSON-LD, full hreflang pair incl. x-default,
   cross-links to canonical guide + SEO posts + page-profile.
3. Sitemap add (idempotent), blog-index insert (EN), internal-link check.
"""
import glob, json, os, re

BASE = 'https://hermes-passiv.pages.dev'
ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
TODAY = '2026-08-26'

# ---------- 1. x-default fix ----------
fixed = []
for p in sorted(glob.glob(os.path.join(SITE, '**', '*.html'), recursive=True)):
    c = open(p).read()
    alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', c)
    if len(alts) >= 2 and 'x-default' not in [a[0] for a in alts]:
        # x-default points at the EN mirror: swap /da/ segment out of own URL
        own = [h for lang, h in alts if lang == 'da']
        if own:
            xd = own[0].replace(f'{BASE}/da/', f'{BASE}/')
        else:
            # EN page missing x-default (should not happen) -> self
            selfs = [h for lang, h in alts if lang == 'en']
            xd = selfs[0] if selfs else ''
        assert xd, p
        first = f'<link rel="alternate" hreflang="{alts[0][0]}" href="{alts[0][1]}">'
        c = c.replace(first, f'<link rel="alternate" hreflang="x-default" href="{xd}">\n' + first, 1)
        open(p, 'w').write(c)
        fixed.append(p)
print('x-default added to', len(fixed), 'pages')
for f_ in fixed:
    print(' ', os.path.relpath(f_, SITE))

# verify sitewide now
bad = []
for p in sorted(glob.glob(os.path.join(SITE, '**', '*.html'), recursive=True)):
    c = open(p).read()
    alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', c)
    if len(alts) >= 2 and 'x-default' not in [a[0] for a in alts]:
        bad.append(p)
assert not bad, bad
print('verified: every multi-hreflang page now has x-default')

# ---------- 2. new blog pair ----------
SLUG_EN = 'hreflang-guide'
SLUG_DA = 'hreflang-guide-da'
URL_EN = f'{BASE}/blog/{SLUG_EN}'
URL_DA = f'{BASE}/da/blog/{SLUG_DA}'

FAQS_EN = [
    ('What is hreflang?',
     'Hreflang is an HTML attribute (<link rel="alternate" hreflang="...">) that tells '
     'search engines which language and region version of a page to show to which users. '
     'If your site exists in English and Danish, hreflang helps Google serve the Danish '
     'page to Danish searchers and the English page to everyone else.'),
    ('Does hreflang affect SEO rankings?',
     'It does not boost rankings directly, but it routes the right users to the right '
     'version — which improves engagement and conversions in each market. It also prevents '
     'duplicate-content confusion between translated pages, so the correct version ranks '
     'in each locale instead of Google guessing.'),
    ('Is hreflang required to have x-default?',
     'Not required, but recommended. The x-default value tells search engines which URL to '
     'show users whose language matches none of your versions — typically your global or '
     'English page. Every complete hreflang set should include it.'),
    ('Do hreflang tags need to be reciprocal?',
     'Yes. If page A lists page B as its alternate, page B must list page A back. Missing '
     'return tags are the single most common hreflang error and cause search engines to '
     'ignore the entire annotation set.'),
    ('Should hreflang be used together with canonical?',
     'Yes — they work together. Each language version should have a self-referencing '
     'canonical AND point to its alternate versions via hreflang. The canonical says '
     '"this is the authoritative URL for this version"; hreflang says "these other URLs '
     'are equivalent versions for other languages".'),
    ('Where do I put hreflang tags?',
     'Three places work: the <head> of each page (most common), an XML sitemap with '
     'xhtml:link entries, or HTTP headers (for non-HTML files like PDFs). Pick one method '
     'and use it consistently — mixing methods risks conflicts.'),
    ('How do I check my hreflang implementation?',
     'Inspect the <head> of each page for <link rel="alternate"> tags and verify every '
     'listed URL returns 200 and links back reciprocally. For more than a few pages, a CLI '
     'tool like <a href="/page-profile">page-profile</a> automates the head-tag audit '
     'across your whole sitemap.'),
]
FAQS_DA = [
    ('Hvad er hreflang?',
     'Hreflang er en HTML-attribut (<link rel="alternate" hreflang="...">), der fortæller '
     'søgemaskinerne, hvilken sprog- og regionsversion af en side der skal vises til hvilke '
     'brugere. Eksisterer dit site på dansk og engelsk, hjælper hreflang Google med at vise '
     'den danske side til danske søgende og den engelske til alle andre.'),
    ('Påvirker hreflang dine placeringer i søgninger?',
     'Ikke direkte — men den sender de rigtige brugere til den rigtige version, hvilket '
     'forbedrer engagement og konvertering i hvert marked. Den forhindrer også '
     'dubletindholds-forvirring mellem oversatte sider.'),
    ('Skal man have x-default med?',
     'Det er ikke et krav, men det anbefales. x-default fortæller søgemaskinerne, hvilken '
     'URL der skal vises til brugere, hvis sprog ikke matcher nogen af dine versioner — '
     'typisk din globale eller engelske side. Enhver komplet hreflang-sæt bør have den.'),
    ('Skal hreflang-tags være gensidige?',
     'Ja. Hvis side A lister side B som alternativ, skal side B liste side A tilbage. '
     'Manglende retur-tags er den mest almindelige hreflang-fejl og får søgemaskinerne til '
     'at ignorere hele annotationssættet.'),
    ('Hvor placerer jeg hreflang-tags?',
     'Tre steder virker: i <head> på hver side (mest almindeligt), i en XML-sitemap med '
     'xhtml:link-entries, eller i HTTP-headers (til ikke-HTML-filer som PDF\'er). Vælg én '
     'metode og hold den konsekvent.'),
    ('Hvordan tjekker jeg min hreflang-implementering?',
     'Inspicér <head> på hver side for <link rel="alternate">-tags og verificér at hver '
     'listet URL svarer 200 og linker gensidigt tilbage. Til mere end et par sider kan et '
     'CLI-værktøj som <a href="/da/page-profile">page-profile</a> automatisere tjekket på '
     'tværs af hele dit sitemap.'),
]

def mk(lang, url, alt_url, alt_lang, headline, desc, faqs):
    art = {'@context': 'https://schema.org', '@type': 'Article',
           'headline': headline, 'description': desc, 'url': url,
           'datePublished': TODAY, 'dateModified': TODAY,
           'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
           'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'}}
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage',
           'mainEntity': [{'@type': 'Question', 'name': q,
                           'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}
    return art, faq

ART_EN, FAQ_EN = mk('en', URL_EN, URL_DA, 'da',
    'Hreflang Guide: How to Implement and Check Language Targeting',
    'Learn how hreflang annotations work, the most common mistakes (missing return tags, no x-default), and how to check every page of a multilingual site automatically.',
    FAQS_EN)
ART_DA, FAQ_DA = mk('da', URL_DA, URL_EN, 'en',
    'Guide til hreflang: Sådan implementerer og tjekker du sprogstyring',
    'Lær hvordan hreflang fungerer, de mest almindelige fejl (manglende retur-tags, manglende x-default), og hvordan du automatisk tjekker hver side på et flersproget site.',
    FAQS_DA)
for b in (ART_EN, FAQ_EN, ART_DA, FAQ_DA):
    assert b['@context'] == 'https://schema.org'
    json.loads(json.dumps(b, ensure_ascii=False))

def hreflangs(url_en, url_da):
    return (f'<link rel="alternate" hreflang="x-default" href="{url_en}">\n'
            f'<link rel="alternate" hreflang="en" href="{url_en}">\n'
            f'<link rel="alternate" hreflang="da" href="{url_da}">')

def head(lang, title, desc, url, hl_block, art, faq):
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
<meta property="og:image" content="{BASE}/cover.jpg">
<meta property="og:image:alt" content="{title}">
<meta property="og:site_name" content="Hermes Passiv">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{BASE}/cover.jpg">
<link rel="canonical" href="{url}">
{hl_block}
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{json.dumps(art, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(faq, ensure_ascii=False)}
</script>
<script defer src="/track.js"></script>
<style>
  .compare {{ width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }}
  .compare th, .compare td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); }}
  pre.cmd {{ background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px; overflow-x:auto; font-size:0.85rem; line-height:1.6; margin:0.8rem 0; }}
  pre.cmd code {{ font-family:'SF Mono','Monaco','Fira Code',monospace; }}
</style>
</head>'''

TRACK = '''<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});}catch(e){}});
</script>'''

import html as _html

def faq_cards(faqs):
    out = []
    for q, a in faqs:
        # escape raw tag literals inside answer prose so they render as code text
        a = re.sub(r'<(link|head)\b[^>]*>', lambda m: _html.escape(m.group(0)), a)
        a = a.replace('<head>', '&lt;head&gt;')
        out.append(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>')
    return '\n'.join(out)

HL_EN = hreflangs(URL_EN, URL_DA)
HL_DA = hreflangs(URL_EN, URL_DA)

en_body = f'''
<body>
<header class="hero">
  <div class="container">
    <div class="badge">INTERNATIONAL SEO &middot; HREFLANG &middot; GUIDE</div>
    <h1>Hreflang Guide:<br>How to Implement and Check Language Targeting</h1>
    <p class="subtitle">Hreflang tells Google which language version of your page to show in which country. Get it wrong and Danish users land on your English page (or worse, nothing ranks). Here is how the annotation works, which mistakes are most common, and how to check a whole site automatically.</p>
    <div class="hero-cta">
      <a href="#mistakes" class="btn-primary">The 6 common mistakes &rarr;</a>
      <a href="/page-profile" class="btn-secondary">Audit your multilingual site with page-profile</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 5 minute read</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>What hreflang does</h2>
    <p>A hreflang annotation is a line in the page <code>&lt;head&gt;</code>:</p>
    <pre class="cmd"><code>&lt;link rel="alternate" hreflang="en" href="https://example.com/page"&gt;
&lt;link rel="alternate" hreflang="da" href="https://example.com/da/page"&gt;
&lt;link rel="alternate" hreflang="x-default" href="https://example.com/page"&gt;</code></pre>
    <p>Together these three lines say: English speakers get the first URL, Danish speakers get the second, and everyone else gets the x-default. Each version should also carry a self-referencing <a href="/blog/canonical-url-guide">canonical URL</a>.</p>
    <div class="problem-cards">
      <div class="card"><h3>🌍 Right users, right version</h3><p>Danish searchers see the Danish page in results — better comprehension, higher conversion, fewer bounces.</p></div>
      <div class="card"><h3>📑 Translations are not duplicates</h3><p>Without hreflang, Google may treat translated pages as duplicate content and pick one to rank everywhere.</p></div>
      <div class="card"><h3>🎯 Region variants supported</h3><p><code>en-gb</code>, <code>de-at</code>, <code>pt-br</code> — hreflang handles language-region pairs when spelling, currency or legal text differs.</p></div>
    </div>
  </div>
</section>

<section class="products" id="mistakes">
  <div class="container">
    <h2>The 6 most common hreflang mistakes</h2>
    <table class="compare">
      <thead><tr><th>#</th><th>Mistake</th><th>Consequence</th><th>Fix</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>Missing return tags (not reciprocal)</td><td>Search engines ignore the whole annotation set.</td><td>Every listed URL must link back to every other one, including itself.</td></tr>
        <tr><td>2</td><td>No x-default</td><td>Users with unmatched languages get an arbitrary version.</td><td>Add x-default pointing to your global/English page.</td></tr>
        <tr><td>3</td><td>Relative URLs in href</td><td>Annotations may be misinterpreted.</td><td>Always absolute URLs: <code>https://…</code>.</td></tr>
        <tr><td>4</td><td>Wrong language/region codes</td><td>Google cannot match users; annotation ignored.</td><td>Use ISO 639-1 language + optional ISO 3166-1 Alpha 2 region (<code>da</code>, <code>en-gb</code>).</td></tr>
        <tr><td>5</td><td>Listed URLs return errors or redirect chains</td><td>Broken targets invalidate the set.</td><td>Every hreflang target must return HTTP 200 directly.</td></tr>
        <tr><td>6</td><td>Conflicting canonical</td><td>A version canonicalising elsewhere contradicts hreflang.</td><td>Each version gets a self-referencing canonical.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Check a multilingual site automatically</h2>
    <p>The free, open-source <a href="/page-profile" style="color:var(--color-accent);">page-profile</a> CLI audits the <code>&lt;head&gt;</code> of any URL — canonical, hreflang alternates, meta robots, titles:</p>
    <pre class="cmd"><code>npx page-profile https://example.com/da/page        # single page report
npx page-profile --urls-from-file urls.txt          # batch all language versions (Pro)</code></pre>
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

<div style="text-align:center;margin-top:16px;"><p>Related: <a href="/blog/canonical-url-guide" style="color:var(--color-accent);">Canonical URL Guide</a> &middot; <a href="/blog/website-seo-metadata-audit" style="color:var(--color-accent);">SEO Metadata Audit</a> &middot; <a href="/blog/technical-seo-check-website" style="color:var(--color-accent);">Technical SEO Check</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">&larr; Home</a> &middot; <a href="/page-profile">page-profile</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
{TRACK}
</body>
</html>'''

en_html = head('en', ART_EN['headline'], ART_EN['description'], URL_EN, HL_EN, ART_EN, FAQ_EN) + en_body

da_body = f'''
<body>
<header class="hero">
  <div class="container">
    <div class="badge">INTERNATIONALT SEO &middot; HREFLANG &middot; GUIDE</div>
    <h1>Guide til hreflang:<br>Sådan implementerer og tjekker du sprogstyring</h1>
    <p class="subtitle">Hreflang fortæller Google, hvilken sprogversion af din side der skal vises i hvilket land. Kommer det galt, lander danske brugere på din engelske side — eller intet rangerer. Sådan virker annotationen, hvilke fejl der er mest almindelige, og hvordan du tjekker et helt site automatisk.</p>
    <div class="hero-cta">
      <a href="#fejl" class="btn-primary">De 6 almindelige fejl &rarr;</a>
      <a href="/da/page-profile" class="btn-secondary">Revidér dit flersprogede site med page-profile</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters læsning</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Hvad hreflang gør</h2>
    <p>En hreflang-annotation er en linje i sidens <code>&lt;head&gt;</code>:</p>
    <pre class="cmd"><code>&lt;link rel="alternate" hreflang="en" href="https://eksempel.dk/page"&gt;
&lt;link rel="alternate" hreflang="da" href="https://eksempel.dk/da/page"&gt;
&lt;link rel="alternate" hreflang="x-default" href="https://eksempel.dk/page"&gt;</code></pre>
    <p>Sammen siger de tre linjer: engelsktalende får den første URL, dansktalende den anden, og alle andre får x-default. Hver version bør også have en selvrefererende <a href="/da/blog/canonisk-url-guide">kanonisk URL</a>.</p>
    <div class="problem-cards">
      <div class="card"><h3>🌍 Rigtige brugere, rigtig version</h3><p>Danske sögende ser den danske side i resultaterne — bedre forståelse, højere konvertering, færre afbrydelser.</p></div>
      <div class="card"><h3>📑 Oversættelser er ikke dubletter</h3><p>Uden hreflang kan Google behandle oversatte sider som dubletindhold og vælge én version til at rangere overalt.</p></div>
      <div class="card"><h3>🎯 Regionsvarianter understøttet</h3><p><code>en-gb</code>, <code>de-at</code>, <code>pt-br</code> — hreflang håndterer sprog-region-par når stavning, valuta eller juridisk tekst adskiller sig.</p></div>
    </div>
  </div>
</section>

<section class="products" id="fejl">
  <div class="container">
    <h2>De 6 mest almindelige hreflang-fejl</h2>
    <table class="compare">
      <thead><tr><th>#</th><th>Fejl</th><th>Konsekvens</th><th>Løsning</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>Manglende retur-tags (ikke gensidig)</td><td>Søgemaskinerne ignorerer hele sættet.</td><td>Enhver listet URL skal linke tilbage til alle andre — inklusive sig selv.</td></tr>
        <tr><td>2</td><td>Ingen x-default</td><td>Brugere uden matchende sprog får en vilkårlig version.</td><td>Tilføj x-default der peger på din globale/engelske side.</td></tr>
        <tr><td>3</td><td>Relative URL'er i href</td><td>Annotationerne kan misfortolkes.</td><td>Brug altid absolutte URL'er: <code>https://…</code>.</td></tr>
        <tr><td>4</td><td>Forkerte sprog-/regionkoder</td><td>Google kan ikke matche brugere; annotationen ignoreres.</td><td>Brug ISO 639-1 sprog + valgfri ISO 3166-1 Alpha 2 region (<code>da</code>, <code>en-gb</code>).</td></tr>
        <tr><td>5</td><td>Listede URL'er giver fejl eller redirect-kæder</td><td>Ødelagte mål ugyldiggør sættet.</td><td>Hvert hreflang-mål skal svare HTTP 200 direkte.</td></tr>
        <tr><td>6</td><td>Konfliktskabende canonical</td><td>En version der canonical et andet sted modsiger hreflang.</td><td>Hver version får en selvrefererende canonical.</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Tjek et flersproget site automatisk</h2>
    <p>Det gratis open source-værktøj <a href="/da/page-profile" style="color:var(--color-accent);">page-profile</a> reviderer <code>&lt;head&gt;</code> på enhver URL — canonical, hreflang-alternativer, meta robots, titler:</p>
    <pre class="cmd"><code>npx page-profile https://eksempel.dk/da/side       # rapport for én side
npx page-profile --urls-from-file urls.txt         # batch alle sprogversioner (Pro)</code></pre>
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

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/canonisk-url-guide" style="color:var(--color-accent);">Guide til kanoniske URL'er</a> &middot; <a href="/da/blog/seo-metadata-tjek-hjemmeside" style="color:var(--color-accent);">SEO- og metadata-tjek</a> &middot; <a href="/da/blog/teknisk-seo-tjek-hjemmeside" style="color:var(--color-accent);">Teknisk SEO-tjek</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/da/">&larr; Forside</a> &middot; <a href="/da/page-profile">page-profile</a> &middot; <a href="/">Blog</a></p>
</footer>
{TRACK}
</body>
</html>'''

da_html = head('da', ART_DA['headline'], ART_DA['description'], URL_DA, HL_DA, ART_DA, FAQ_DA) + da_body

for path, html in [(f'{SITE}/blog/{SLUG_EN}.html', en_html),
                   (f'{SITE}/da/blog/{SLUG_DA}.html', da_html)]:
    with open(path, 'w') as f:
        f.write(html)

# validate new pages
for path in (f'{SITE}/blog/{SLUG_EN}.html', f'{SITE}/da/blog/{SLUG_DA}.html'):
    c = open(path).read()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', c, re.DOTALL)
    assert len(blocks) == 2, path
    for b in blocks:
        p = json.loads(b)
        assert p['@context'] == 'https://schema.org'
    n_hl = c.count('rel="alternate" hreflang=') + c.count('rel=&quot;alternate&quot; hreflang=')
    assert n_hl >= 3, (path, n_hl)  # 3 head links + several escaped in prose/code
    assert 'x-default' in c
    print('OK', path, len(c), 'bytes')

# internal link targets exist, no .html links
for path in (f'{SITE}/blog/{SLUG_EN}.html', f'{SITE}/da/blog/{SLUG_DA}.html'):
    c = open(path).read()
    refs = [r for r in re.findall(r'href="(/[^"#]+)"', c)
            if not r.startswith('/api') and r not in ('/sitemap.xml', '/style.css', '/track.js', '/', '/da/')]
    missing = [r for r in refs if not os.path.exists(os.path.join(SITE, r.lstrip('/') + '.html'))]
    assert not missing, missing
    bad = [r for r in refs if r.endswith('.html')]
    assert not bad, bad
print('internal links OK')

# ---------- 3. sitemap ----------
sm = os.path.join(SITE, 'sitemap.xml')
c = open(sm).read()
added = []
for url in (URL_EN, URL_DA):
    if url + '</loc>' not in c:
        c = c.replace('</urlset>',
                      f'<url>\n    <loc>{url}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>0.8</priority>\n  </url>\n  </urlset>')
        added.append(url)
open(sm, 'w').write(c)
import xml.dom.minidom
xml.dom.minidom.parse(sm)
print('sitemap OK,', c.count('<loc'), 'urls,', len(added), 'added')

# cross-link from canonical guide posts (related line already covers SEO cluster; add hreflang link)
for src, label in [(f'{SITE}/blog/canonical-url-guide.html', '/blog/hreflang-guide'),
                   (f'{SITE}/da/blog/canonisk-url-guide.html', '/da/blog/hreflang-guide-da')]:
    x = open(src).read()
    if label not in x:
        rel = ('Related' if 'blog/canonical' == SLUG_EN else 'Relateret')
        word = 'Related:' if '/da/' not in label else 'Relateret:'
        x = x.replace('</body>', f'<div style="text-align:center;margin-top:16px;"><p>{word} <a href="{BASE}{label}" style="color:var(--color-accent);">Hreflang Guide</a></p></div>\n</body>', 1)
        open(src, 'w').write(x)
        print('cross-linked:', src)
