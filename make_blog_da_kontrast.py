#!/usr/bin/env python3
"""Iteration 152: Danish blog post for the WCAG contrast checker + cross-links.

- New: site/da/blog/wcag-kontrast-checker.html (Danish guide linking to /contrast-checker-da)
- Cross-link DA/EN contrast tools <-> blog post (both directions)
- JSON-LD validated with json.loads, sitemap dedupe check, internal link check
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

SLUG = 'wcag-kontrast-checker'


def build_page():
    desc = ('Sådan tjekker du farvekontrast mod WCAG 2.1 AA og AAA gratis: indtast to farver, '
            'se ratioen med det samme, og få at vide præcis hvilke krav der bestås. Intet '
            'forlader din browser — ingen tilmelding.')
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': 'WCAG Kontrast-Checker — sådan tjekker du farvekontrast (gratis)',
        'description': desc,
        'url': f'{BASE}/da/blog/{SLUG}',
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    faq = [
        ("Hvilken kontrast-ratio kræver WCAG AA?",
         "Normal tekst under 24 px skal have mindst 4,5:1. Stor tekst (18 pt / 14 pt fed og opefter) kræver 3:1. AAA kræver 7:1 for normal tekst og 4,5:1 for stor tekst."),
        ("Gælder kontrastkravene også for ikoner og knapper?",
         "Ja — WCAG 2.1 success-kriterium 1.4.11 (Non-text Contrast) kræver 3:1 for grafiske objekter som ikoner, input-kanter og vigtige UI-elementer."),
        ("Er værktøjet gratis?",
         "Ja. Kontrast-checkeren på /contrast-checker-da kører helt i din browser. Ingen konto, ingen grænser, intet sendes til en server."),
        ("Hvordan finder jeg lavkontrast på en hel side?",
         "Brug den gratis Accessibility Scanner på /scan-da: den gennemgår alle tekst-/baggrundskombinationer på en hel URL og viser hver overtrædelse af 1.4.3."),
    ]
    main_entity = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                   for q, a in faq]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': main_entity},
                        ensure_ascii=False)

    head_html = f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WCAG Kontrast-Checker — sådan tjekker du farvekontrast gratis</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="WCAG Kontrast-Checker — gratis AA/AAA-tjek i browseren">
<meta property="og:description" content="Indtast to farver, få ratio og bestået/dumpet for AA og AAA med det samme. Gratis og uden tilmelding.">
<meta property="og:image" content="{BASE}/cover.jpg">
<meta property="og:url" content="{BASE}/da/blog/{SLUG}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{BASE}/da/blog/{SLUG}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">BLOG &middot; TILGÆNGELIGHED</div>
    <h1>WCAG Kontrast-Checker<br>Sådan Tjekker Du Farvekontrast Gratis</h1>
    <p class="subtitle">Lav kontrast er den mest udbredte tilgængelighedsfejl på nettet — og den letteste at rette. Indtast to farver, se ratioen med det samme, og få at vide præcis hvilke WCAG-krav der består og hvilke der dumpes.</p>
    <div class="hero-cta">
      <a href="#hvordan" class="btn-primary">Sådan virker det</a>
      <a href="/contrast-checker-da" class="btn-secondary">Tjek kontrast nu &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 4 minutters læsning</p>
  </div>
</header>

<section class="problem" id="hvad-er-det">
  <div class="container">
    <h2>Hvorfor er kontrast så vigtig?</h2>
    <p>Cirka én ud af tolv mænd har nedsat farvesyn. Tekst med for lav kontrast bliver ulæselig for dem — og svær at læse for alle i sollys, på gamle skærme eller på en projektor. Derfor var lavkontrast-tekst den hyppigste fejl i WebAIMs store årlige gennemgang af de million mest besøgte hjemmesider.</p>
    <div class="problem-cards">
      <div class="card"><h3>⚖️ Kravene</h3><p>AA: 4,5:1 for normal tekst, 3:1 for stor tekst og grafik (1.4.11). AAA: 7:1 / 4,5:1. Ved EAA og offentlige sites er AA minimum.</p></div>
      <div class="card"><h3>⚡ Sekunder, ikke timer</h3><p>Du behøver ikke beregne relativ luminans i hånden. Indtast to farver — hex eller farvevælger — og se resultatet live.</p></div>
      <div class="card"><h3>🔒 Dine data forbliver lokale</h3><p>Beregningen kører i JavaScript i din egen browser. Ingen farver sendes nogen steder hen.</p></div>
    </div>
  </div>
</section>

<section class="products" id="hvordan">
  <div class="container">
    <h2>Sådan gør du (under 5 sekunder)</h2>
    <ol>
      <li>Åbn den <a href="/contrast-checker-da" style="color:var(--color-accent);">gratis WCAG Kontrast-Checker</a>.</li>
      <li>Vælg tekstfarve og baggrundsfarve — enten med farvevælgerne eller ved at taste hex-koder direkte.</li>
      <li>Læs ratioen og resultatet: bestået/dumpet for AA og AAA, både for normal og stor tekst, plus en live forhåndsvisning.</li>
      <li>Juster den ene af farverne, indtil alle de krav du skal opfylde er grønne.</li>
    </ol>
    <p>Ratioen beregnes med WCAG-specifikationens egen formel: begge farver konverteres til sRGB relativ luminans, og kontrasten er (L1 + 0,05) / (L2 + 0,05). Resultatet matcher therefore specifikationen nøjagtigt — samme tal som kommercielle værktøjer viser.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Fra enkelt par til hele siden</h2>
    <p>Kontrast-checkeren tester ét farvepar ad gangen — perfekt når du designer et nyt element. Skal et helt site tjekkes, brug den gratis <a href="/scan-da" style="color:var(--color-accent);">Accessibility Scanner</a>: indsæt URL'en, og den finder al lavkontrast-tekst på siden sammen med overskrifts-, alt-tekst-, formulär- og tastaturfejl.</p>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">TILHØRENDE VÆRKTØJER</span><h3>Mere kontrast-hjælp</h3><p><a href="/palette-generator-da" style="color:var(--color-accent);">Palette generator</a> bygger tilgængelige farvepaletter · <a href="/text-on-image-checker-da" style="color:var(--color-accent);">Tekst-på-billede-tjek</a> tester tekst oven på billeder.</p></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">ENGELSK VERSION</span><h3>Arbejder du internationalt?</h3><p>Samme checker findes på <a href="/contrast-checker" style="color:var(--color-accent);">engelsk her</a>.</p></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3>Hvad siger loven?</h3><p>Europas tilgængelighedslov (EAA) stiller WCAG-krav til de fleste e-handelssider fra juni 2025. Læs <a href="/blog/eaa-frister-2026" style="color:var(--color-accent);">fristerne her</a>.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
'''
    for q, a in faq:
        head_html += f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>\n'
    tail_html = '''    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/contrast-checker-da" class="btn-primary">Prøv kontrast-checkeren gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/scan-da" class="btn-secondary">Eller scan hele siden &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA · DA</span><h3><a href="/blog/eaa-frister-2026" style="color:var(--color-accent);text-decoration:none;">EAA-frister: hvornår gælder loven for dig?</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">VÆRKTØJER</span><h3><a href="/free-tools" style="color:var(--color-accent);text-decoration:none;">Alle gratis værktøjer</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">MARKDOWN · DA</span><h3><a href="/da/blog/url-til-markdown-konverter" style="color:var(--color-accent);text-decoration:none;">URL til Markdown-konverter</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/contrast-checker-da">Kontrast-checkeren</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});}catch(e){}})();
</script>
</body>
</html>'''
    return head_html + tail_html


def update_sitemap():
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    url = f'{BASE}/da/blog/{SLUG}'
    if f'<loc>{url}</loc>' in c:
        print('sitemap: already present')
        return
    add = (f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
           f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)
    print('sitemap updated')


def patch(path, old, new, must=True):
    c = open(path).read()
    if new in c:
        print(f'{path}: already patched')
        return True
    if old not in c:
        if must:
            raise SystemExit(f'anchor NOT found in {path}: {old[:70]!r}')
        return False
    open(path, 'w').write(c.replace(old, new))
    print(f'{path}: patched')
    return True


def check_links(files):
    broken = []
    for path in files:
        html = open(path).read()
        for m in sorted(set(re.findall(r'href="(/[^"#]*?)"', html))):
            url = m.split('?')[0]
            t = ('site' + url).rstrip('/')
            if not (os.path.exists(t) or os.path.exists(t + '.html') or url == '/'
                    or os.path.exists(t + '/index.html')):
                broken.append((path, m))
    return broken


def main():
    # 1. New Danish blog page
    page = build_page()
    out = f'{SITE}/da/blog/{SLUG}.html'
    with open(out, 'w') as f:
        f.write(page)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org'
    print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')

    # 2. Sitemap
    update_sitemap()

    # 3. Cross-link from the DA tool page to the blog post
    patch(f'{SITE}/contrast-checker-da.html',
          '<p style="margin-top:26px"><a href="/free-tools">',
          '<p style="margin-top:10px"><a href="/da/blog/wcag-kontrast-checker">Guide: sådan tjekker du kontrast trin for trin</a></p>\n<p style="margin-top:26px"><a href="/free-tools">')

    # 4. Cross-link from the EN tool page to the DA guide (lang attr)
    patch(f'{SITE}/contrast-checker.html',
          '<a href="/contrast-checker-da">Dansk version</a>',
          '<a href="/contrast-checker-da">Dansk version</a> · <a href="/da/blog/wcag-kontrast-checker" lang="da">dansk guide</a>',
          must=False)

    # 5. Card on /da frontpage pointing to the guide? Keep tool card; add link line.
    patch(f'{SITE}/da.html',
          '<a href="/contrast-checker-da" class="btn-secondary" style="margin-top:12px;">Tjek kontrast →</a>',
          '<a href="/contrast-checker-da" class="btn-secondary" style="margin-top:12px;">Tjek kontrast →</a>\n          <a href="/da/blog/wcag-kontrast-checker" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>',
          must=False)

    # 6. Internal link check on everything touched
    files = [out, f'{SITE}/contrast-checker-da.html']
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')

    print(f'\nDone: /da/blog/{SLUG} created + sitemap + cross-links')


if __name__ == '__main__':
    main()
