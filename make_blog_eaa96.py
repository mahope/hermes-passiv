#!/usr/bin/env python3
"""Iteration 96: dansk SEO-side /blog/gratis-eaa-saetninger (EAA statement-generators, DA)
samt EN pendant /blog/free-eaa-statement-generators. Crawl-bait: hver side = flere indgange.
Kører selvstændigt; skriver HTML direkte i samme stil som gratis-nis2-vaerktoejer.html."""

import json
import re
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

DA_TOOLS = [
    ('✅ Tilgængelighedserklæring-generator',
     'Udfyld oplysningerne om din hjemmeside og din overensstemmelse med WCAG 2.1 AA — '
     'generatoren producerer en komplet erklæring efter EU-ministeriets model, som du kan '
     'kopiere eller downloade. Intet uploades; alt kører i din browser.',
     '/accessibility-statement-generator'),
    ('🔍 EAA-scanner',
     'Et teknisk tjek af de synlige tegn på tilgængelighedsproblemer: manglende alt-tekster, '
     'kontrastfejl, formularetiketter og mere. Brug resultatet til at udfylde erklæringens '
     '"overensstemmelsesstatus" ærligt — det er den del myndighederne ser på.',
     '/scan-da'),
    ('🎨 Kontrasttjekker',
     'WCAG kræver mindst 4.5:1 for almindelig tekst. Indtast to farver og se straks om '
     'kombinationen består — med både AA- og AAA-niveauer.',
     '/contrast-checker-da'),
    ('🖼️ Tekst-på-billede-tjekker',
     'Tekst lagt henover billeder er en hyppig kilde til kontrastfejl. Tjekket viser, hvor '
     'ofte din side bruger mønsteret, og hvor risikabelt det er.',
     '/text-on-image-checker-da'),
]

EN_TOOLS = [
    ('✅ Accessibility Statement Generator',
     'Fill in details about your site and its conformance status — the generator produces a '
     'complete statement based on the EU model, ready to copy or download. Nothing is uploaded; '
     'everything runs in your browser.', '/accessibility-statement-generator'),
    ('🔍 Free Accessibility Scanner',
     'A technical check of the visible signs of accessibility problems: missing alt text, '
     'contrast failures, missing form labels and more. Use the results to fill in the '
     '"conformance status" section of your statement honestly — that is the part regulators read.',
     '/scan'),
    ('🎨 Contrast Checker',
     'WCAG requires at least 4.5:1 for normal text. Enter two colours and see instantly whether '
     'the combination passes — at both AA and AAA levels.', '/contrast-checker'),
    ('🖼️ Text-on-Image Checker',
     'Text overlaid on images is a frequent source of contrast failures. The checker shows how '
     'often your site uses the pattern and how risky it is.', '/text-on-image-checker'),
]


def head(slug, lang, title, meta_desc, og_title, og_desc, headline):
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article', 'headline': headline,
        'description': meta_desc, 'url': f'{BASE}/blog/{slug}',
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    })
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{BASE}/blog/{slug}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<link rel="canonical" href="{BASE}/blog/{slug}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{ld}
</script>
<script defer src="/track.js"></script>
</head>'''


def cards(tools):
    out = []
    for name, desc, link in tools:
        label = 'Åbn værktøjet →' if link.endswith('-da') else 'Open the tool →'
        out.append(f'      <div class="card"><h3>{name}</h3><p>{desc}<br>'
                   f'<a href="{link}">{label}</a></p></div>')
    return '\n'.join(out)


def da_page():
    slug = 'gratis-eaa-saetninger'
    desc = ('Gratis browserbaserede værktøjer til den tilgængelighedserklæring, Den Europæiske '
            'Accessibilitetsloven kræver: generator, scanner og kontrasttjek — hvad dækker de, '
            'og hvad gør du med resultatet?')
    h = head(slug, 'da',
             'Gratis tilgængelighedserklærings-værktøjer (2026): generator, scanner &amp; kontrasttjek',
             desc,
             'Gratis værktøjer til tilgængelighedserklæringen (2026)',
             'Byg en lovpligtig tilgængelighedserklæring i din browser — intet uploades, ingen tilmelding.',
             'Gratis værktøjer til tilgængelighedserklæringen (2026)')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · TILGÆNGELIGHED</div>
    <h1>Gratis værktøjer til<br>tilgængelighedserklæringen</h1>
    <p class="subtitle">Den Europæiske Accessibilitetsloven (EAA) kræver siden 28. juni 2025, at mange digitale tjenester dokumenterer deres tilgængelighed. Her er de gratis browserbaserede værktøjer, der bygger en troværdig erklæring — og en ærlig guide til, hvad de ikke kan.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Læs guiden</a>
      <a href="/accessibility-statement-generator" class="btn-secondary">Byg erklæringen nu →</a>
    </div>
    <p class="hero-note">Opdateret august 2026 · Læsetid: 5 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="why">Hvorfor skal du have en erklæring?</h2>
    <p>EAA (direktiv (EU) 2019/882) gælder for e-handel, banktjenester, e-bøger og meget andet, der sælges til forbrugere i EU. Kravene følger WCAG 2.1 AA via standarden EN 301 549 — og virksomheder skal kunne <strong>dokumentere</strong> overensstemmelsen, typisk i form af en offentligt tilgængelig tilgængelighedserklæring. Myndighederne i flere medlemslande har allerede uddelt bøder. Erklæringen er altså ikke et "nice to have", men det papir, en tilsynsmyndighed beder om først.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Trin 1: Mål</h3><p>Kør en teknisk scanning. Du kan ikke skrive en ærlig erklæring, før du ved, hvor dine problemer er.</p></div>
      <div class="card"><h3>🛠️ Trin 2: Ret det vigtigste</h3><p>Kontrast, alt-tekster og formularetiketter er de mest almindelige — og billigste — rettelser.</p></div>
      <div class="card"><h3>📄 Trin 3: Erklæring</h3><p>Beskriv status, kendte begrænsninger og feedbackkanal. Ærlighed om begrænsninger tæller mere end perfektion.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="tools">De gratis værktøjer</h2>
    <p>Alle værktøjerne kører helt i din browser. Ingen konto, ingen e-mailadresse — intet af det du indtaster, forlader din maskine.</p>
    <div class="problem-cards">
{cards(DA_TOOLS)}
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>Hvor stopper de gratis værktøjer?</h2>
    <p class="section-intro">En generator giver dig dokumentet, en scanner giver dig tallene — men automatiserede tjek fanger kun en del af WCAG-kravene. Tastaturbetjening, skærmlæsere og logisk rækkefølge kræver manuel test. Vores e-bog kombinerer begge dele i en 14-dages handlingsplan med klar-til-brug skabeloner.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/#products" class="btn-primary">Se EAA-e-bogen →</a>
      &nbsp;&nbsp;
      <a href="/free-tools" class="btn-secondary">Alle gratis compliance-værktøjer →</a>
      &nbsp;&nbsp;
      <a href="/blog/free-eaa-statement-generators" class="btn-secondary">English version →</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">ERKLÆRINGEN</span><h3><a href="/blog/how-to-write-accessibility-statement" style="color:var(--color-accent);text-decoration:none;">Sådan skriver du en tilgængelighedserklæring</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">FRISTER</span><h3><a href="/blog/eaa-deadline-2026" style="color:var(--color-accent);text-decoration:none;">EAA-fristen: hvad håndhæves nu?</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">TJEKKLISTE</span><h3><a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);text-decoration:none;">EAA-tjekliste</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">OVERLAYS</span><h3><a href="/blog/accessibility-overlays-eaa" style="color:var(--color-accent);text-decoration:none;">Hvorfor overlays ikke løser EAA</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Forside</a> · <a href="/accessibility-statement-generator">Erklæringsgenerator</a> · <a href="/free-tools">Gratis værktøjer</a> · <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''
    return slug, h + body


def en_page():
    slug = 'free-eaa-statement-generators'
    desc = ('Free browser-based tools for the accessibility statement required under the European '
            'Accessibility Act: a generator, scanner and contrast checker compared — what they cover, '
            'and what to do with the result.')
    h = head(slug, 'en',
             'Free Accessibility Statement Tools (2026): Generator, Scanner &amp; Contrast Checks',
             desc,
             'Free Accessibility Statement Tools (2026)',
             'Build an EAA-compliant accessibility statement in your browser — nothing uploaded, no sign-up.',
             'Free Accessibility Statement Tools (2026)')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · ACCESSIBILITY</div>
    <h1>Free Tools for Your<br>Accessibility Statement</h1>
    <p class="subtitle">Since June 28, 2025 the European Accessibility Act requires many digital services to document their accessibility. Here are the free browser-based tools that build a credible statement — and an honest guide to what they cannot do.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Read the guide</a>
      <a href="/accessibility-statement-generator" class="btn-secondary">Generate your statement now →</a>
    </div>
    <p class="hero-note">Updated August 2026 · Reading time: 5 minutes</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="why">Why do you need a statement?</h2>
    <p>The EAA (Directive (EU) 2019/882) covers e-commerce, banking services, e-books and more sold to consumers in the EU. The requirements follow WCAG 2.1 AA through the EN 301 549 standard — and businesses must be able to <strong>evidence</strong> conformance, typically via a publicly available accessibility statement. Market-surveillance authorities have already issued fines in several member states. The statement is not a nice-to-have; it is usually the first paper an inspector asks for.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Step 1: Measure</h3><p>Run a technical scan first. You cannot write an honest statement before you know where your problems are.</p></div>
      <div class="card"><h3>🛠️ Step 2: Fix the big ones</h3><p>Contrast, alt text and form labels are the most common — and cheapest — fixes.</p></div>
      <div class="card"><h3>📄 Step 3: Statement</h3><p>Describe status, known limitations and a feedback channel. Honesty about limitations counts more than perfection.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2 id="tools">The free tools</h2>
    <p>All tools below run entirely in your browser. No account, no email address — nothing you enter leaves your machine.</p>
    <div class="problem-cards">
{cards(EN_TOOLS)}
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>Where free tools stop</h2>
    <p class="section-intro">A generator gives you the document, a scanner gives you the numbers — but automated checks catch only part of WCAG. Keyboard operability, screen readers and logical focus order require manual testing. Our e-book combines both into a 14-day fix plan with ready-to-use templates.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/#products" class="btn-primary">See the EAA e-book →</a>
      &nbsp;&nbsp;
      <a href="/free-tools" class="btn-secondary">All free compliance tools →</a>
      &nbsp;&nbsp;
      <a href="/blog/gratis-eaa-saetninger" class="btn-secondary">Dansk version →</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Related guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">STATEMENT</span><h3><a href="/blog/how-to-write-accessibility-statement" style="color:var(--color-accent);text-decoration:none;">How to Write an Accessibility Statement</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">DEADLINE</span><h3><a href="/blog/eaa-deadline-2026" style="color:var(--color-accent);text-decoration:none;">EAA Deadline: What Is Enforced Now</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">CHECKLIST</span><h3><a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);text-decoration:none;">EAA Accessibility Checklist</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">OVERLAYS</span><h3><a href="/blog/accessibility-overlays-eaa" style="color:var(--color-accent);text-decoration:none;">Why Overlays Don't Fix the EAA</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Home</a> · <a href="/accessibility-statement-generator">Statement Generator</a> · <a href="/free-tools">Free Tools</a> · <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''
    return slug, h + body


def update_sitemap(slugs):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    add = ''.join(f'  <url><loc>{BASE}/blog/{s}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
                  for s in slugs)
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)


def cross_link_en_da():
    """Add Danish-version card to the existing EN NIS2-tools page? No — link DA↔EN new pages only."""
    pass


def main():
    pages = [da_page(), en_page()]
    slugs = []
    for slug, html in pages:
        with open(f'{SITE}/blog/{slug}.html', 'w') as f:
            f.write(html)
        slugs.append(slug)
        # validate JSON-LD
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        assert blocks, slug
        for b in blocks:
            d = json.loads(b)
            assert d['@context'] == 'https://schema.org' and d['@type'] == 'Article', slug
        print(f'{slug}.html written, JSON-LD OK')
    update_sitemap(slugs)
    print('sitemap updated')


if __name__ == '__main__':
    main()
