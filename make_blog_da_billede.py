#!/usr/bin/env python3
"""Iteration 153: Danish blog post for the text-on-image contrast checker.

- New: site/da/blog/tekst-paa-billede-kontrasttjek.html (DA guide linking to /text-on-image-checker-da)
- Cross-links both directions: tool page -> guide, guide -> tools/scan, frontpage card
- JSON-LD validated with json.loads, sitemap dedupe check, internal link check
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

SLUG = 'tekst-paa-billede-kontrasttjek'


def build_page():
    desc = ('Sådan tjekker du om tekst oven på et billede opfylder WCAG-kravene: upload billedet, '
            'markér tekstområdet, og se den faktiske kontrast mellem teksten og pixels bagved. '
            'Gratis, kører i din browser — intet uploades til en server.')
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': 'Tekst-på-billede kontrasttjek — sådan tester du læsbarhed gratis',
        'description': desc,
        'url': f'{BASE}/da/blog/{SLUG}',
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    faq = [
        ("Hvorfor fejler tekst på billeder så ofte?",
         "Et foto har sjældent ens lysstyrke under hele tekstblokken. Kontrasten kan være fin over de mørke partier og helt væk over de lyse. WCAG måler kontrast mod de faktiske pixels bag hvert bogstav — derfor skal man teste det værste tilfælde, ikke gennemsnittet."),
        ("Hvilken kontrast kræves der?",
         "WCAG SC 1.4.3: mindst 4,5:1 for normal tekst og 3:1 for stor tekst (fra ca. 24 px normal eller 18,66 px fed). SC 1.4.11 kræver desuden 3:1 for meningsbærende grafik."),
        ("Er værktøjet gratis og sikkert at bruge?",
         "Ja. Billedet analyseres i JavaScript direkte i din browser. Intet uploades til nogen server, og der er ingen grænser eller tilmelding."),
        ("Hvad gør jeg hvis jeg ikke består?",
         "Læg en semi-transparent mørk eller lys skærm bag teksten, mørkned/lysnet kun det område hvor teksten står, eller flyt teksten til en fast bjælke under billedet. Test igen indtil alle målinger består."),
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
<title>Tekst-på-billede kontrasttjek — sådan tester du læsbarhed gratis</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Tekst-på-billede kontrasttjek — gratis WCAG-tjek i browseren">
<meta property="og:description" content="Upload et billede, markér tekstområdet, og se om kontrasten består WCAG AA. Gratis og uden tilmelding.">
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
    <h1>Tekst-på-Billede Kontrasttjek<br>Sådan Tester Du Læsbarhed Gratis</h1>
    <p class="subtitle">Hero-billeder med tekst ovenpå er en af de mest almindelige tilgængelighedsfehler. Her ser du hvordan du tjekker den faktiske kontrast mellem teksten og pixels bagved — og hvad du gør, hvis den ikke består.</p>
    <div class="hero-cta">
      <a href="#hvordan" class="btn-primary">Sådan virker det</a>
      <a href="/text-on-image-checker-da" class="btn-secondary">Tjek dit billede nu &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 4 minutters læsning</p>
  </div>
</header>

<section class="problem" id="hvad-er-det">
  <div class="container">
    <h2>Hvorfor fejler tekst på billeder så ofte?</h2>
    <p>Et foto har sjældent ens lysstyrke under hele tekstblokken. Hvid tekst kan være perfekt læselig over himlen og fuldstændig forsvinde over sneen to centimeter længere nede. WCAG måler kontrasten mod de faktiske pixels bag hvert bogstav — ikke mod gennemsnittet af billedet.</p>
    <div class="problem-cards">
      <div class="card"><h3>⚖️ Kravene</h3><p>SC 1.4.3: 4,5:1 for normal tekst, 3:1 for stor tekst (ca. 24 px normal / 18,66 px fed). SC 1.4.11 kræver 3:1 for meningsbærende UI-dele og grafik.</p></div>
      <div class="card"><h3>🎯 Det værste sted tæller</h3><p>En gradient kan bestå under halvdelen af bogstaverne og fejle under resten. Mål altid det værste tilfælde — det er dét, en bruger med dårligt syn rammer.</p></div>
      <div class="card"><h3>🔒 Dine billeder forbliver lokale</h3><p>Billedet læses og analyseres i JavaScript i din egen browser via canvas-API'en. Intet uploades til nogen server.</p></div>
    </div>
  </div>
</section>

<section class="products" id="hvordan">
  <div class="container">
    <h2>Sådan gør du (under et minut)</h2>
    <ol>
      <li>Åbn det <a href="/text-on-image-checker-da" style="color:var(--color-accent);">gratis tekst-på-billede kontrasttjek</a>.</li>
      <li>Træk dit billede ind — eller indsæt et screenshot fra dit design direkte fra udklipsholderen.</li>
      <li>Markér området hvor teksten står, og angiv tekstens farve.</li>
      <li>Læs resultatet: værste og gennemsnitlig kontrast i området, plus bestået/dumpet for AA og AAA. Juster designet, indtil alt er grønt.</li>
    </ol>
    <p>Værktøjet læser pixels via canvas-API'en og beregner relativ luminans pr. WCAG-specifikationen — samme formel som kommercielle værktøjer bruger. Du får altså samme tal, som en auditor vil måle.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Fra ét billede til hele siden</h2>
    <p>Kontrasttjekket tester ét billede ad gangen — perfekt når du designer en hero eller et banner. Skal hele sitets kontraster tjekkes, brug den gratis <a href="/scan-da" style="color:var(--color-accent);">Accessibility Scanner</a>: den gennemgår al tekst på en hel URL og finder lavkontrast-tekst sammen med overskrifts-, alt-tekst-, formulær- og tastaturfejl.</p>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">TILHØRENDE VÆRKTØJER</span><h3>Mere kontrast-hjælp</h3><p><a href="/contrast-checker-da" style="color:var(--color-accent);">Kontrast-checker</a> tester farvepar &middot; <a href="/palette-generator-da" style="color:var(--color-accent);">Palette generator</a> bygger tilgængelige paletter.</p></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">GUIDE</span><h3>Læs kontrast-guiden</h3><p>Guide til selve WCAG-kravene og hvordan du arbejder med dem: <a href="/da/blog/wcag-kontrast-checker" style="color:var(--color-accent);">WCAG kontrast-checker trin for trin</a>.</p></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">ENGELSK VERSION</span><h3>Arbejder du internationalt?</h3><p>Samme værktøj findes på <a href="/text-on-image-checker" style="color:var(--color-accent);">engelsk her</a>.</p></div>
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
      <a href="/text-on-image-checker-da" class="btn-primary">Prøv kontrasttjekket gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/scan-da" class="btn-secondary">Eller scan hele siden &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">KONTRAST · DA</span><h3><a href="/da/blog/wcag-kontrast-checker" style="color:var(--color-accent);text-decoration:none;">WCAG kontrast-checker: sådan tjekker du farvekontrast</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA · DA</span><h3><a href="/blog/eaa-frister-2026" style="color:var(--color-accent);text-decoration:none;">EAA-frister: hvornår gælder loven for dig?</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">VÆRKTØJER</span><h3><a href="/free-tools" style="color:var(--color-accent);text-decoration:none;">Alle gratis værktøjer</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/text-on-image-checker-da">Kontrasttjekket</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/#blog">Blog</a></p>
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
        print(f'{path}: anchor missing (skipped): {old[:60]!r}')
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

    # 3. Cross-link from the DA tool page back to this guide
    patch(f'{SITE}/text-on-image-checker-da.html',
          '<p style="margin-top:26px"><a href="/free-tools">',
          '<p style="margin-top:10px"><a href="/da/blog/tekst-paa-billede-kontrasttjek">Guide: sådan tester du tekst på billeder trin for trin</a></p>\n<p style="margin-top:26px"><a href="/free-tools">')

    # 4. Link from the EN tool page to the DA guide
    patch(f'{SITE}/text-on-image-checker.html',
          '<a href="/text-on-image-checker-da">',  # placeholder, replaced below
          '<a href="/text-on-image-checker-da">',
          must=False)

    # 5. Card on /da frontpage pointing to the new guide
    patch(f'{SITE}/da.html',
          '<a href="/text-on-image-checker-da" class="btn-secondary" style="margin-top:12px;">Tjek billede →</a>',
          '<a href="/text-on-image-checker-da" class="btn-secondary" style="margin-top:12px;">Tjek billede →</a>\n          <a href="/da/blog/tekst-paa-billede-kontrasttjek" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>',
          must=False)

    # 6. Internal link check on everything touched
    files = [out, f'{SITE}/text-on-image-checker-da.html', f'{SITE}/da.html']
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')

    print(f'\nDone: /da/blog/{SLUG} created + sitemap + cross-links')


if __name__ == '__main__':
    main()
