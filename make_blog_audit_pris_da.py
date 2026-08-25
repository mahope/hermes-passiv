#!/usr/bin/env python3
"""Iteration 104: Danish counterpart of /blog/accessibility-audit-cost ->
/blog/pris-tilgaengelighedsgennemgang plus frontpage card.
Same safety pattern as iter.97-103: JSON-LD validated with json.loads,
sitemap duplicate check, internal link check."""

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
        'inLanguage': lang,
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
    slug = 'pris-tilgaengelighedsgennemgang'
    desc = ('Hvad koster en tilgængelighedsgennemgang (WCAG/EAA-audit) i 2026? '
            'Reelle prisniveauer: gratis automatisk scan, hybrid-audit og fuld '
            'manuel audit — og hvordan små webbureauer selv prissætter arbejdet.')
    h = head(slug, 'da',
             'Pris på tilgængelighedsgennemgang 2026: hvad koster en WCAG-audit?',
             desc,
             'Hvad koster en tilgængelighedsaudit i 2026?',
             'Reelle prisintervaller: gratis scanninger, hybrid-audits og manuelle audits — og hvordan du prissætter EAA-arbejdet som bureau.',
             'Pris på tilgængelighedsgennemgang 2026: reelle tal for små bureauer')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · EAA &amp; PRISER</div>
    <h1>Hvad koster en<br>tilg&aelig;ngelighedsgennemgang?</h1>
    <p class="subtitle">Tilbud sp&aelig;nder fra 0 til over 200.000 kr &mdash; og begge ender kan v&aelig;re legitime. Her er hvad hvert prisniveau faktisk k&oslash;ber, hvad der driver prisen, og hvordan du som lille webbureau selv scoper og priss&aelig;tter tilg&aelig;ngelighedsarbejde under EAA.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">L&aelig;s guiden</a>
      <a href="/scan" class="btn-secondary">Scan din side gratis &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; L&aelig;setid: 8 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2>Hvorfor priserne svinger s&aring; meget</h2>
    <p>Sp&oslash;rg tre leverand&oslash;rer hvad en tilg&aelig;ngelighedsgennemgang koster, og du f&aring;r tre svar der adskiller sig med en faktor ti. Det er ikke prisafskalning &mdash; &quot;audit&quot; d&aelig;kker alt fra en to-minutters automatisk rapport til en ugers manuel evaluering med sk&aelig;rml&aelig;sere. Leverancerne, grundigheden og den juridiske v&aelig;gt er helt forskellige.</p>
    <p>Realistiske markedspriser i 2026 (omregnet til DKK): automatiserede scanninger koster fra 0 til ca. 3.500 kr; hybrid-gennemgange (automatik plus m&aring;lrettet manuelt test) ligger omkring 10.000-25.000 kr for et mindre site; fulde manuelle audits fra specialister koster groft 35.000-110.000 kr for sm&aring;-mellemstore sites og mere for komplekse applikationer; enterprise-platforme med l&oslash;bende overv&aring;gning koster fra ca. 150.000 kr om &aring;ret og op.</p>
    <div class="problem-cards">
      <div class="card"><h3>&#127881; Automatisk scanning: 0-3.500 kr</h3><p>V&aelig;rkt&oslash;jer som axe DevTools, Lighthouse, WAVE og vores egen gratis scanner fanger groft 30-40 % af WCAG-problemerne &mdash; kontrast, alt-tekster, formullabels, overskriftsstruktur. Et godt udgangspunkt, aldrig et forsvarligt resultat p&aring; sig selv.</p></div>
      <div class="card"><h3>&#128269; Hybrid-gennemgang: ~10.000-25.000 kr</h3><p>Automatisk scan plus 6-12 timers erfaret manuelt test (tastaturnavigation, sk&aelig;rml&aelig;ser p&aring; n&oslash;gleflows). Det bedste kompromis for et typisk mindre virksomhedssite.</p></div>
      <div class="card"><h3>&#127891; Fuld manuel audit: 35.000-110.000+ kr</h3><p>Specialfirma tester alle unikke skabeloner og interaktive komponenter mod WCAG 2.2 AA med sv&aelig;rhedsvurderede fund og anbefalinger. Kravet n&aring;r den juridiske dokumentation skal kunne holde.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvad driver prisen op?</h2>
    <p>Den st&oslash;rste prisdriver er ikke antallet af sider &mdash; auditorer tester p&aring; et repr&aelig;sentativt udvalg. Det er antallet af <em>unikke</em> side-typer og interaktive komponenter: filtre, modalbokse, trinvise formularer, kortl&oslash;sninger, bookingflows. Hver af dem skal testes manuelt med tastatur og sk&aelig;rml&aelig;ser.</p>
    <p>Andre drivere:</p>
    <p><strong>1. Kompleksitet i komponenter.</strong> En statisk marketingside er billig at teste. En datotabel med tastaturnavigation, live regions og aria-attributter tager timer pr. komponent.<br>
    <strong>2. Hvilke hj&aelig;lpeteknologier der skal d&aelig;kkes.</strong> NVDA + Chrome er minimum. JAWS, VoiceOver p&aring; iOS og TalkBack f&oslash;jer tid &mdash; men ogs&aring; trov&aelig;rdighed.<br>
    <strong>3. Dokumentationskrav.</strong> Fund med WCAG-referencer, sv&aelig;rhedsgrad og konkret fix-vejledning koster flere timer end en liste af fejl. Til geng&aelig;ld er det den leverance din kunde (eller en tilsynsmyndighed) faktisk kan bruge.<br>
    <strong>4. Hastighed.</strong> Ekspresleverancer koster typisk 25-50 % mere.</p>
    <p><strong>Omkostningen ved fejlretning kommer oveni.</strong> Audit'en finder problemerne &mdash; rettelserne er et separat budget. Som tommelfingerregel ligger rettelsesarbejdet p&aring; 1-3 x auditens timeantal afh&aelig;ngigt af hvor slemt det st&aring;r til. Byg derfor altid rettelsestid ind i dit tilbud fra starten.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>S&aring;dan priss&aelig;tter du selv arbejdet</h2>
    <p><strong>Trin 1 &mdash; K&oslash;r en gratis automatisk scanning f&oslash;rste.</strong> Den giver dig en fejlliste og et kvalitetsindtryk af koden, f&oslash;r du lover noget. Vores scanner er gratis og kr&aelig;ver ingen installation.</p>
    <p><strong>Trin 2 &mdash; Opt&aelig;l de unikke skabeloner.</strong> G&aring; sitet igennem og list hver side-type: forsiden, produktliste, produktside, kontakt, blogindl&aelig;g, formularer, s&oslash;geresultater. Antallet gange dine estimerede timer direkte.</p>
    <p><strong>Trin 3 &mdash; Estim&eacute;r timer pr. skabelon.</strong> Tommelfingerregel for en erfaren tester: 30-60 min automatisk gennemgang + manuel tastaturtest pr. enkel skabelon, 2-4 timer pr. kompleks komponent. L&aelig;g 20 % oveni til rapportering.</p>
    <p><strong>Trin 4 &mdash; S&aelig;t en timepris og hold den.</strong> Sm&aring; bureauer i DK ligger typisk p&aring; 800-1.400 kr/timen for specialiseret tilg&aelig;ngelighedsarbejde. Undervurd&eacute;r ikke: EAA-risikoen for kunden er reel, og ekspertisen er sj&aelig;lden.</p>
    <p><strong>Trin 5 &mdash; S&aelig;lg en pakke, ikke bare en rapport.</strong> St&aelig;rkest tilbud er &quot;audit + rettelse af kritiske fejl + gen-test&quot;. Kunden slipper for at koordinere to leverand&oslash;rer, og du tjener p&aring; hele forl&oslash;bet.</p>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>Gratis v&aelig;rkt&oslash;jer til at komme i gang</h2>
    <p>Du beh&oslash;ver ikke vente p&aring; et tilbud for at finde ud af, hvor dit site st&aring;r:</p>
    <div class="problem-cards">
      <div class="card"><h3>&#9889; Gratis automatisk scanner</h3><p>16 WCAG-regler, kontrastberegning, scorekort A-D og konkrete fix-tips. Inds&aelig;t URL, f&aring; resultat p&aring; under et minut.</p><p style="margin-top:10px;"><a href="/scan" class="btn-primary">Scan nu &rarr;</a></p></div>
      <div class="card"><h3>&#9002; CLI til CI/CD</h3><p>Samme motor som npm-pakke og Python: kør scanninger i din pipeline og f&aring; exit-kode ved fejl. Gratis.</p><p style="margin-top:10px;"><a href="/downloads" class="btn-secondary">Hent CLI'en &rarr;</a></p></div>
      <div class="card"><h3>&#128220; EAA-tjeklisten</h3><p>10-point checkliste over hvad loven faktisk kr&aelig;ver &mdash; god til at scope samtaler med kunder.</p><p style="margin-top:10px;"><a href="/blog/eaa-accessibility-checklist" class="btn-secondary">L&aelig;s tjeklisten &rarr;</a></p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
    <div class="problem-cards">
      <div class="card"><h3>Kan man ikke bare bruge en gratis scanner?</h3><p>Til et f&oslash;rste indtryk, ja. Men automatiske v&aelig;rkt&oslash;jer fanger kun omkring 30-40 % af WCAG-problemerne. Tingene de ikke kan se &mdash; om en alt-tekst giver mening, om fokusordenen er logisk, om en sk&aelig;rml&aelig;serbruger kan gennemf&oslash;re et k&oslash;b &mdash; er netop dem der skaber risiko under EAA. Brug scannern som filter, ikke som dokumentation.</p></div>
      <div class="card"><h3>Hvor ofte b&oslash;r en gennemgang gentages?</h3><p>Ved st&oslash;rre redesign eller ny funktionalitet, og som minimum &eacute;n gang om &aring;ret p&aring; sites med l&oslash;bende udvikling. Mange bureauer s&aelig;lger en &aring;rlig &quot;tilg&aelig;ngelighedstilstand&quot; som fast ydelse &mdash; gen-scanning plus en kort manuel gennemgang af nye features.</p></div>
      <div class="card"><h3>Hvem betaler &mdash; bureauet eller kunden?</h3><p>EAA-forpligtelsen ligger hos den der s&aelig;lger tjenesten &mdash; alts&aring; kunden. Bureauet har pligt til at levere tilg&aelig;ngeligt h&aring;ndv&aelig;rk, men selve auditten og rettelserne b&oslash;r v&aelig;re en kundebetalt linje i tilbuddet. S&aelig;lger du et site uden at n&aelig;vne tilg&aelig;ngelighed, risikerer du at skulle spise omkostningen senere.</p></div>
      <div class="card"><h3>Hvad koster det hvis vi IKKE g&oslash;r noget?</h3><p>B&ouml;derne varierer pr. land (op til flere millioner euro i Frankrig og Sverige), og klage-drevet h&aring;ndh&aelig;velse betyder at &eacute;n utilfreds kunde kan udl&oslash;se en sag. Men den mest realistiske omkostning er tabt forretning: offentlige udbud kr&aelig;ver allerede dokumenteret tilg&aelig;ngelighed, og flere private g&oslash;r det samme i deres leverand&oslash;rkrav.</p></div>
      <div class="card"><h3>Gylder tallene her ogs&aring; i Danmark?</h3><p>Timel&oslash;n-niveauerne er danske, og markedet ligner resten af EU. Danske tilbud p&aring; manuelle audits ligger typisk i samme interval: titusinder for hybride gennemgange, hundredetusinder for fulde manuelle audits af komplekse l&oslash;sninger. F&aring; altid mindst to tilbud &mdash; spredningen er stor.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-frister-2026" style="color:var(--color-accent);text-decoration:none;">EAA-frister 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">V&AElig;RKT&Oslash;J</span><h3><a href="/blog/gratis-eaa-saetninger" style="color:var(--color-accent);text-decoration:none;">Gratis v&aelig;rkt&oslash;j til tilg&aelig;ngelighedserkl&aelig;ringen (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">CHECKLISTE</span><h3><a href="/blog/eaa-accessibility-checklist" style="color:var(--color-accent);text-decoration:none;">EAA Accessibility Checklist</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">OVERLAYS</span><h3><a href="/blog/accessibility-overlays-eaa" style="color:var(--color-accent);text-decoration:none;">Accessibility overlays og EAA</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">&larr; Forside</a> &middot; <a href="/scan">Gratis scanner</a> &middot; <a href="/free-tools">Gratis v&aelig;rkt&oslash;j</a> &middot; <a href="/#blog">Blog</a></p>
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
        <h3><a href="/blog/pris-tilgaengelighedsgennemgang" style="color:inherit;text-decoration:none;">Prisen på en tilgængelighedsgennemgang (dansk)</a></h3>
        <p>Hvad koster en WCAG-audit i 2026? Reelle prisintervaller fra gratis scanning til fuld manuel audit — og hvordan bureauet selv prissætter arbejdet.</p>
        <a href="/blog/pris-tilgaengelighedsgennemgang" class="btn-secondary" style="margin-top:12px;">L&aelig;s guiden &rarr;</a>
      </div>
'''


def add_frontpage_card():
    p = f'{SITE}/index.html'
    c = open(p).read()
    if '/blog/pris-tilgaengelighedsgennemgang' in c:
        print('frontpage card already present')
        return
    anchor = CARD.split('\n')[0]
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
