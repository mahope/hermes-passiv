#!/usr/bin/env python3
"""Iteration 101: dansk GDPR-overbliksguide for webbureauer ->
/blog/gdpr-webbureau-da plus forsids-kort.
Samme moenster som iter.97-100: JSON-LD valideres med json.loads,
sitemap-duplikattjek, internt link-tjek."""

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
    slug = 'gdpr-webbureau-da'
    desc = ('GDPR for danske webbureauer 2026: hvilken rolle har bureauet '
            '(dataansvarlig eller databehandler), cookies og samtykke, '
            'databehandleraftaler, hostvalg, hændelser på 72 timer — og en '
            '5-trins tjekliste.')
    h = head(slug, 'da',
             'GDPR-guiden 2026: Webbureauets rolle forklaret',
             desc,
             'GDPR: Hvad er webbureauets ansvar?',
             'Dataansvarlig eller databehandler? Cookies, DBA, hosting, 72-timers-reglen og en 5-trins tjekliste.',
             'GDPR-guiden: Webbureauets rolle og ansvar i 2026')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · GDPR</div>
    <h1>GDPR:<br>Hvad er webbureauets ansvar?</h1>
    <p class="subtitle">Bureauer rører persondata hver dag — kontaktformularer, analytics, nyhedsbreve, backups af klientsites. Alligevel er der uenighed om, hvem der bærer ansvaret: bureauet eller klienten? Svaret afhænger af rollen. Her er rollernes forskel, de fem klassiske fejl og en 5-trins tjekliste.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Læs guiden</a>
      <a href="/scan-da" class="btn-secondary">Scan dit site gratis →</a>
    </div>
    <p class="hero-note">Opdateret august 2026 · Læsetid: 7 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="roller">To roller: dataansvarlig og databehandler</h2>
    <p>GDPR (forordning 2016/679) kender to hovedroller, og forskningen i dem afgør hvem der svarer over for Datatilsynet:</p>
    <div class="problem-cards">
      <div class="card"><h3>🎯 Dataansvarlig</h3><p>Den der bestemmer <em>hvorfor</em> og <em>i store træk hvordan</em> data behandles. Din klient er typisk dataansvarlig for sit websites data: den bestemmer formål (marketing, salg) og midler (CMS, nyhedsbrevsværktøj).</p></div>
      <div class="card"><h3>🔧 Databehandler</h3><p>Den der behandler data på den ansvarliges instruks. Et bureau der vedligeholder et klientsite og har adgang til brugerdata via admin-login, backups eller staging-miljøer er typisk databehandler.</p></div>
      <div class="card"><h3>⚖️ Begge dele</h3><p>Mange bureauer er begge: databehandler for klientens websitedata — men selvstændig dataansvarlig for egne data (medarbejdere, egne leads, jeres egen analytics på jeres domæne).</p></div>
    </div>
    <p><strong>Hvorfor det betyder noget:</strong> som databehandler kan du ikke bare "følge klientens instruks" hvis instruksen bryder GDPR — så hæfter I sammen. Og uden en skriftlig databehandleraftale er behandlingen ulovlig fra dag ét (art. 28).</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>De fem klassiske fejl hos bureauer</h2>
    <p><strong>1. Ingen databehandleraftale.</strong> Art. 28 kræver en skriftlig aftale FØR behandlingen starter — ikke "den kommer nok senere". Det gælder også jeres subleverandører (hosting, e-mail).</p>
    <p><strong>2. Cookies før samtykke.</strong> Ikke-nødvendige cookies (analytics, marketing, sociale plugins) må først sættes efter et aktivt, informeret samtykke — og ligeså let at trække tilbage som at give. Et banner med "Acceptér alle" og gemt afvis-knap holder ikke.</p>
    <p><strong>3. Analytics uden hjemmel.</strong> Standard Google Analytics-setup overfører data til USA. Datatilsynene har slået fast, at det kræver ekstra forholdsregler (fx IP-truncering, DPA, evt. proxy-løsning) — ellers er trafikdata reelt persondata uden lovligt grundlag.</p>
    <p><strong>4. Formulardata i mailkæder.</strong> Kontaktformularer der videresendes som e-mail samler persondata i postkasser uden opbevaringsfrist eller adgangsstyring. Bedre: formular direkte til CMS/database med logget adgang.</p>
    <p><strong>5. Glemte staging- og backupmiljøer.</strong> Kopier af produktionssites med ægte brugerdata ligger ofte ubeskyttet på staging-domæner. Enten anonymiser data, eller lås miljøerne bag login — og sæt frist for sletning.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>72-timers-reglen — også for bureauet</h2>
    <p>Ved en persondata-brud skal den dataansvarlige melde til Datatilsynet <strong>inden for 72 timer</strong>, hvis risikoen er reel (art. 33). Som databehandler er pligten strammere: <strong>I skal mellem til klienten uden unødig forsinkelse</strong> efter at blive bekendt med bruddet (art. 33 §2).</p>
    <p>I praksis betyder det: hvis I opdager, at et klientsite er blevet kompromitteret, starter klientens 72-timers-ur snarest — og jeres meldepligt gør jeres reaktionstid til en kontraktlig størrelse. Hav en skriftlig incident-proces klar: hvem opdager, hvem vurderer, hvem melder, inden for hvor mange timer.</p>
    <div class="problem-cards">
      <div class="card"><h3>📝 Hvad skal en DBA indeholde?</h3><p>Art. 28 §3 lister minimumet: genstand og varighed, art og formål, datakategorier, klientens rettigheder og instrukspligt, fortrolighed, sikkerhedsforanstaltninger, subleverandører, hjælp ved indberetninger, sletning/tilbagelevering og revisionsrettigheder. Vores e-bog har en klar-til-brug skabelon.</p></div>
      <div class="card"><h3>🌍 Hosting og tredjeland</h3><p>Klienter spørger i stigende grad, hvor deres site hostes. EU/EOES-hosting fjerner et kapitel af transfer-spørgsmålene. Har I subleverandører i tredjelande, skal de stå på en liste i DBA'en og være dækket af standardkontraktclauses.</p></div>
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>5-trins tjekliste for bureauet</h2>
    <p class="section-intro">Sådan får I grundlaget på plads — uden at det bliver et projekt på måneder:</p>
    <p><strong>1. Kortlæg jeres dataprocesser.</strong> Hvilke klientsites har I adgang til? Hvor lander formulardata? Hvilke værktøjer sætter I selv op (analytics, nyhedsbrev)? Én oversigt rækker langt.<br>
    <strong>2. Få DBA'er på alle kundeforhold.</strong> En standardskabelon + kort proces: send ved kontraktopstart, arkivér underskrevet version.<br>
    <strong>3. Ryd op i cookies og tracking.</strong> Samtykkebanner med lige vilkår for ja/nej, nødvendige cookies alene før samtykke, dokumenteret cookiepolitik.<br>
    <strong>4. Skriv incident-processen.</strong> Én side: opdagelse → vurdering → melding til klient (timer, ikke dage) → hjælp til Datatilsynet-melding.<br>
    <strong>5. Gennemgå det årligt.</strong> Nye klienter, nye værktøjer, nye subleverandører? Opdater listen og aftalerne. Dokumenteret gennemgang tæller ved tilsyn.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Scan dit site gratis →</a>
      &nbsp;&nbsp;
      <a href="/#products" class="btn-secondary">Se GDPR-e-bogen →</a>
      &nbsp;&nbsp;
      <a href="/blog/nis2-guide-da" class="btn-secondary">NIS2-guiden (dansk) →</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      <div class="card"><h3>Er bureauet dataansvarlig for klientsitets cookies?</h3><p>Som udgangspunkt nej — klienten bestemmer formålet med tracking. MEN: sætter I cookien op, vælger I teknisk løsning og leverer konfigurationen. Vær derfor sikker på, at klienten aktivt har godkendt setup'et, og at samtykke-løsningen virker. Delvist ansvar kan deles (art. 26, fælles ansvar).</p></div>
      <div class="card"><h3>Skal der DBA med hostingleverandøren også?</h3><p>Ja — hosting af et website med persondata er behandling på vegne af den ansvarlige. Enten står klienten selv som part (typisk når klienten ejer hostingabonnementet), eller også er I mellemled og skal selv have aftale med hosten og videreføre kravene.</p></div>
      <div class="card"><h3>Hvor store er bøderne?</h3><p>Op til 20 mio. euro eller 4 % af global omsætning for de tunge principovertrædelser; 10 mio. euro / 2 % for fx manglende DBA eller utilstrækkelig sikkerhed. For små virksomheder er den reelle risiko dog oftest påbud, tilsynssag og tabt tillid.</p></div>
      <div class="card"><h3>Gælder GDPR overhovedet for små sites?</h3><p>Ja. GDPR har ingen størrelsesgrænse — kun undtagelser for ren privat/husholdningsbrug. Et firmas contactside med navn og e-mail er persondata, uanset om virksomheden har tre ansatte.</p></div>
      <div class="card"><h3>Hvordan hænger det sammen med NIS2 og EAA?</h3><p>Tre spor: GDPR beskytter persondata, NIS2 kræver operationel cybersikkerhed, EAA stiller krav om tilgængelighed. En hændelse kan ramme flere spor samtidig. Se vores NIS2-guide og EAA-guides for de andre ben.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">COOKIES</span><h3><a href="/blog/cookie-consent-gdpr-2026" style="color:var(--color-accent);text-decoration:none;">Cookie-consent &amp; GDPR 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">NIS2</span><h3><a href="/blog/nis2-guide-da" style="color:var(--color-accent);text-decoration:none;">NIS2-guiden (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-frister-2026" style="color:var(--color-accent);text-decoration:none;">EAA-frister 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">VÆRKTØJER</span><h3><a href="/free-tools" style="color:var(--color-accent);text-decoration:none;">Gratis compliance-værktøjer</a></h3></div>
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
        <h3><a href="/blog/gdpr-webbureau-da" style="color:inherit;text-decoration:none;">GDPR-guiden: webbureauets rolle (dansk)</a></h3>
        <p>Dataansvarlig eller databehandler? DBA-pligten, cookies, hosting, 72-timers-reglen — og en 5-trins tjekliste for bureauet.</p>
        <a href="/blog/gdpr-webbureau-da" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
'''


def add_frontpage_card():
    p = f'{SITE}/index.html'
    c = open(p).read()
    if '/blog/gdpr-webbureau-da' in c:
        print('frontpage card already present')
        return
    anchor = '<div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">\n        <h3><a href="/blog/nis2-guide-da"'
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
