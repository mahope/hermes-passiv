#!/usr/bin/env python3
"""Iteration 99: dansk pendant til /blog/cookie-consent-gdpr-compliance ->
/blog/cookie-consent-gdpr-2026 plus forsids-kort.
Genbruger iter.98-mønsteret: JSON-LD valideres med json.loads,
sitemap-tjek, internt link-tjek."""

import json
import re
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'


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


def page():
    slug = 'cookie-consent-gdpr-2026'
    desc = ('Cookie-consent i praksis 2026: hvornår kræver GDPR samtykke, hvad siger '
            'EDPB om consent banners, bøderne indtil nu, og en 5-trins plan for små webbureauer.')
    h = head(slug, 'da',
             'Cookie-consent & GDPR 2026: Reglerne for banners forklaret',
             desc,
             'Cookie-banners og GDPR: Hvad er faktisk lov?',
             'Hvornår kræves samtykke? Hvad siger EDPB? Hvilke bøder er givet? Og 5 trin til en korrekt løsning på klient-sites.',
             'Cookie-consent & GDPR: Hvad er faktisk lov i 2026?')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · COOKIE-CONSENT & GDPR</div>
    <h1>Cookie-banners og GDPR:<br>Hvad er faktisk lov?</h1>
    <p class="subtitle">De fleste cookie-banners på nettet bryder reglerne — og tilsynsmyndighederne er begyndt at slå ned på det. Her er hvornår samtykke kræves, hvad EDPB har fastslået, hvilke bøder der er givet indtil nu, og hvordan et lille webbureau gør sine klient-sites korrekte.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Læs guiden</a>
      <a href="/scan-da" class="btn-secondary">Scan dit site gratis →</a>
    </div>
    <p class="hero-note">Opdateret august 2026 · Læsetid: 7 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="reglerne">Grundreglen: ePrivacy + GDPR sammen</h2>
    <p>Cookies reguleres af to love på én gang. <strong>ePrivacy-direktivet (art. 5(3))</strong> kræver samtykke til at gemme eller læse information på brugerens udstyr — med én undtagelse: cookies der er <em>strengt nødvendige</em> for den tjeneste brugeren selv har bedt om. <strong>GDPR</strong> bestemmer hvordan samtykket skal indhentes, og hvad du skal fortælle.</p>
    <p>Det betyder i praksis: analytics-, marketing- og social-media-cookies kræver gyldigt samtykke <em>før</em> de sættes. Ikke "ved fortsat brug", ikke "opt-out", ikke pre-ticked bokse.</p>
    <div class="problem-cards">
      <div class="card"><h3>✅ Gyldigt samtykke (GDPR art. 4(11) + 7)</h3><p>Frit valgt · specifikt · informeret · utvetydigt. Lige let at sige nej til som ja. Kan altid trækkes tilbage lige så nemt. Dokumentation af samtykket skal kunne fremvises.</p></div>
      <div class="card"><h3>❌ Ugyldigt samtykke</h3><p>Pre-ticked bokse (CJEU Planet49, C-673/17) · "fortsat browsing = accept" · banner der gør "afvis"-knappen sværere at finde end "acceptér" · samtykke som vilkår for adgang til sitet.</p></div>
      <div class="card"><h3>🔓 Ingen samtykke kræves</h3><p>Strengt nødvendige cookies: session, indkurv, login-sikkerhed, CSRF-beskyttelse. Bemærk: Google Analytics er efter de fleste tilsynsmyndigheder IKKE nødvendig — den kræver samtykke.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvad EDPB har fastslået om banners</h2>
    <p>Det europæiske databeskyttelsesudvalg (EDPB) udsendte i januar 2025 sin opfattelse om legitim interesse i reklamekonteksten (Opinion 28/2024) og har tidligere (2020) fastslået kernekravene til banners:</p>
    <p><strong>1. Afvisning skal være lige så nem som accept.</strong> Et banner med tydelig "Acceptér alle" men kun en tekstlink "læs mere" for at afvise er en overtrædelse. Myndighederne i Frankrig, Tyskland, Spanien og Østrig har håndhævet netop dette.<br>
    <strong>2. Ingen "nødvendige klik".</strong> At skulle scrolle gennem en lang liste eller klikke sig igennem flere lag for at afvise alle, mens accept er ét klik, er ugyldigt.<br>
    <strong>3. Ingen gentagne forsøg.</strong> Banneret må ikke dukke op igen hver gang brugeren har afvist ("nagging").<br>
    <strong>4. Samtykke før cookies.</strong> Teknisk: tag managers og scripts skal konfigureres så intet sættes før samtykke. En Google Tag Manager-container der fyres ved sideindlæsning bryder reglen uanset hvad banneret siger.<br>
    <strong>5. Legitim interesse dækker ikke reklame-cookies.</strong> Opinion 28/2024 slog fast at behavioral advertising sjældent kan bygge på legitim interesse — samtykke er udgangspunktet.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Bøderne indtil nu</h2>
    <p>Cookie-sager giver mindre bøder end store GDPR-sager, men de kommer oftere — og de rammer også små virksomheder og bureauer der har sat banneret forkert op:</p>
    <div class="problem-cards">
      <div class="card"><h3>🇫🇷 CNIL (Frankrig)</h3><p>Pioner på området: bøder til Google (€150 mio., 2022) og Facebook (€60 mio.) netop fordi "afvis" var sværere end "acceptér". Hundredvis af mindre sanktioner og formelle påkrav til franske sites siden.</p></div>
      <div class="card"><h3>🇩🇪 Datenschutzaufsichtsbehörden</h3><p>Landsdækkende retningslinjer for telemedier (TTDSG/TDDDG): banners uden lige-vilkåret afvisning er en overtrædelse. Flere påbud mod websites og nyhedsbreve.</p></div>
      <div class="card"><h3>🇩🇰 Datatilsynet (Danmark)</h3><p>Dansk praksis: samtykke kræves til ikke-nødvendige cookies; pre-ticked bokse og manglende afvis-mulighed kritiseret i konkrete sager. Vejledningen fra Datatilsynet følger EDPB's krav til banners.</p></div>
      <div class="card"><h3>🇪🇺 Tyske/østrigske domme</h3><p>Planet49-dommen (CJEU 2019) er EU-præcedens: pre-ticked bokse = ugyldigt samtykke. Den gælder stadig og er fundamentet under hele banner-reguleringen.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Google Consent Mode v2 — det tekniske lag</h2>
    <p>Siden marts 2024 kræver Google <strong>Consent Mode v2</strong> for annoncører i EØS og Storbritannien: signals for <code>ad_storage</code>, <code>ad_user_data</code>, <code>ad_personalization</code> og <code>analytics_storage</code> skal sendes korrekt. To faldgruber bureauer ofte rammer:</p>
    <p><strong>Consent Mode er ikke samtykke.</strong> Det er et signal-lag under banneret. Har dit site Consent Mode men et ugyldigt banner, er du stadig i strid.<br>
    <strong>"Basic" vs. "Advanced".</strong> I Basic-mode sendes ingen cookies og ingen pings før samtykke. Advanced-mode sender Cookieless-pings før samtykke — juridisk omdiskuteret i flere lande. Vælger du sikkerhed: Basic.</p>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>5-trins plan for små webbureauer</h2>
    <p class="section-intro">Sådan gør du klient-sites korrekte uden at købe et dyrt CMP-abonnement:</p>
    <p><strong>1. Kortlæg alle cookies og scripts.</strong> DevTools → Application → Cookies, plus alt i tag manager. Kategoriser: nødvendige / statistik / marketing.<br>
    <strong>2. Bloker alt ikke-nødvendigt før samtykke.</strong> Teknisk blokering i tag manageren — ikke bare "skjul scripts". Test i incognito at ingen cookies sættes ved første besøg.<br>
    <strong>3. Byg et banner med lige vilkår.</strong> "Acceptér alle" og "Afvis alle" som lige tydelige knapper, plus mulighed for granuleret valg. Gem samtykket (hvad, hvornår, version af teksten).<br>
    <strong>4. Opdatér privatlivspolitikken.</strong> Navngiv kategorier, leverandører og formål — samme kategorier som banneret bruger, og link til politikken direkte fra banneret.<br>
    <strong>5. Gør afvis-nulstilling let.</strong> Et synligt link i footeren ("cookie-indstillinger") så brugeren kan ændre sit valg — det er del af kravet om at samtykke kan trækkes tilbage.</p>
    <p>Vores GDPR-e-bog gennemgår controller/processor-roller, de tre dokumenter der betyder noget, og en 14-dages handlingsplan — skrevet til små bureauer, ikke jurister.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Scan dit site gratis →</a>
      &nbsp;&nbsp;
      <a href="/#products" class="btn-secondary">Se GDPR-e-bogen →</a>
      &nbsp;&nbsp;
      <a href="/blog/cookie-consent-gdpr-compliance" class="btn-secondary">English version →</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      <div class="card"><h3>Kan jeg bare droppe banneret?</h3><p>Kun hvis du dropper alle ikke-nødvendige cookies. Et site med kun strengt nødvendige cookies behøver intet banner. Det er ofte en reel mulighed: drop GA og pixel-scripts, brug en cookiefri analyse-løsning — så fjerner du både banneret og risikoen.</p></div>
      <div class="card"><h3>Rækker Googles indbyggede consent-banner?</h3><p>Nej som udgangspunkt. Standard-banneret i nogle Google-produkter er opt-out og opfylder ikke GDPR/ePrivacy-kravene i EU ifølge flere tilsynsmyndigheder. Du skal have et banner der giver lige vilkår og blokerer før samtykke.</p></div>
      <div class="card"><h3>Er cookie-bøder relevante for små virksomheder?</h3><p>Ja. Sanktionerne skalerer med virksomheden, og de mest almindelige udfald er påbud og påkrav — men påbud kræver arbejde, dokumentation og i værste fald offentlig kendelse. For et bureau er klientens banner-fejl desuden et ansvarspørgsmål i kontrakten.</p></div>
      <div class="card"><h3>Hvem er ansvarlig — bureauet eller kunden?</h3><p>Dataansvarlig er typisk kunden (siteejeren), men bureauet kan hæfte kontraktuelt for fejlleverance, og som processor har I egne pligter i databehandleraftalen. Sæt cookie/GDPR-ansvar eksplicit i jeres aftaler — det står i vores GDPR-e-bog med klar-til-brug klausuler.</p></div>
      <div class="card"><h3>Gælder dette også session replay og heatmaps?</h3><p>Ja. Hotjar-lignende værktøjer, chat-widgets og embeddede YouTube-videoer sætter cookies/læser data før samtykke. Video-embeds skal lazy-loades med en placeholder indtil samtykke ("two-click solution").</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-haandhaevelse-2026" style="color:var(--color-accent);text-decoration:none;">EAA-håndhævelse 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">FRISTER</span><h3><a href="/blog/eaa-frister-2026" style="color:var(--color-accent);text-decoration:none;">EAA-frister 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">NIS2</span><h3><a href="/blog/nis2-readiness-guide" style="color:var(--color-accent);text-decoration:none;">NIS2 readiness-guide</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">ERKLÆRINGEN</span><h3><a href="/blog/gratis-eaa-saetninger" style="color:var(--color-accent);text-decoration:none;">Gratis sætninger til erklæringen</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Forside</a> · <a href="/scan-da">Gratis scanner</a> · <a href="/free-tools">Gratis værktøjer</a> · <a href="/#blog">Blog</a></p>
</footer>
</body>
</html>'''
    return slug, h + body


def update_sitemap(slugs):
    p = f'{SITE}/sitemap.xml'
    c = open(p).read()
    add = ''.join(f'  <url><loc>{BASE}/blog/{s}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
                  for s in slugs)
    assert all(f'/blog/{s}</loc>' not in c for s in slugs), 'slug already in sitemap'
    c = c.replace('</urlset>', add + '</urlset>')
    open(p, 'w').write(c)


CARD = '''      <div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">
        <h3><a href="/blog/cookie-consent-gdpr-2026" style="color:inherit;text-decoration:none;">Cookie-banners & GDPR (dansk)</a></h3>
        <p>Hvornår kræves samtykke, EDPB's banner-krav, CNIL-bøderne, Consent Mode v2 — og 5 trin til en korrekt løsning på klient-sites.</p>
        <a href="/blog/cookie-consent-gdpr-2026" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
'''


def add_frontpage_card():
    p = f'{SITE}/index.html'
    c = open(p).read()
    if '/blog/cookie-consent-gdpr-2026' in c:
        print('frontpage card already present')
        return
    anchor = '<div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">\n        <h3><a href="/blog/eaa-haandhaevelse-2026"'
    i = c.find(anchor)
    assert i > 0, 'anchor not found in index.html'
    c = c[:i] + CARD + c[i:]
    open(p, 'w').write(c)
    print('frontpage card added')


def check_links(files):
    import os
    broken = []
    for path in files:
        html = open(path).read()
        for m in set(re.findall(r'href="(/[^"#]*?)"', html)):
            url = m.split('?')[0]
            target = ('site' + url).rstrip('/')
            if not (os.path.exists(target) or os.path.exists(target + '.html')
                    or url == '/' or os.path.exists(target + '/index.html')):
                broken.append((path, m))
    return broken


def main():
    slug, html = page()
    with open(f'{SITE}/blog/{slug}.html', 'w') as f:
        f.write(html)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    assert blocks, 'no JSON-LD'
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org' and d['@type'] == 'Article', slug
    print(f'{slug}.html written, JSON-LD OK')
    update_sitemap([slug])
    print('sitemap updated')
    add_frontpage_card()
    broken = check_links([f'{SITE}/blog/{slug}.html', f'{SITE}/index.html'])
    print('broken internal links:', broken if broken else 'none')


if __name__ == '__main__':
    main()
