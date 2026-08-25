#!/usr/bin/env python3
"""Iteration 100: dansk pendant til /blog/nis2-readiness-guide ->
/blog/nis2-guide-da plus forsids-kort.
Genbruger iter.99-moensteret: JSON-LD valideres med json.loads,
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
    slug = 'nis2-guide-da'
    desc = ('NIS2 for små danske webbureauer 2026: hvem er omfattet, de 10 '
            'sikkerhedskrav, incident-72-timers-pligten, leverandørkæden — og en '
            '5-trins plan til at gøre bureauet klar.')
    h = head(slug, 'da',
             'NIS2-guiden 2026: Sådan bliver små webbureauer klare',
             desc,
             'NIS2: Hvad betyder direktivet for dit webbureau?',
             'Hvem er omfattet? De 10 sikkerhedskrav, 72-timers incident-pligten, leverandørkæden og en 5-trins plan.',
             'NIS2-guiden: Sådan bliver små webbureauer klare i 2026')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · NIS2</div>
    <h1>NIS2:<br>Hvad betyder direktivet for dit webbureau?</h1>
    <p class="subtitle">NIS2-direktivet er nu i dansk ret via cybersikkerhedsloven. Mange bureauer tror det kun rammer store virksomheder — men kravene flyder ned gennem kontrakter og leverandørkæder. Her er hvad der gælder, hvilke krav du møder som leverandør, og en 5-trins plan til at blive klar.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">Læs guiden</a>
      <a href="/scan-da" class="btn-secondary">Scan dit site gratis →</a>
    </div>
    <p class="hero-note">Opdateret august 2026 · Læsetid: 7 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="hvem">Hvem er omfattet af NIS2?</h2>
    <p>NIS2 (Directive (EU) 2022/2555) deler virksomheder i to grupper efter sektor og størrelse:</p>
    <p><strong>Vigtige enheder</strong> (essential): mellemstore og store virksomheder (50+ ansatte eller 10 mio. euro omsætning) i sektorer som energi, transport, bank, sundhed, digital infrastruktur og offentlig administration. <strong>Andre vigtige enheder</strong> (important): samme sektorer i mindre skala — her ligger mange digitale byrøer og softwarehuse.</p>
    <p>Direkte omfattede webbureauer er mindretallet. Men det er ikke hele historien: selv et bureau under tærskelen møder NIS2 gennem sine klienter.</p>
    <div class="problem-cards">
      <div class="card"><h3>🏢 Klienten er omfattet</h3><p>Klientens risikoanalyse skal dække leverandører. Dit bureau bliver bedt om at dokumentere sikkerhed i leverancen — ofte som en del af databehandleraftalen eller en separat IT-sikkerhedsklausul.</p></div>
      <div class="card"><h3>📜 Cybersikkerhedsloven</h3><p>I Danmark er NIS2 implementeret i cybersikkerhedsloven (2024/2025), der erstatter den gamle lov om net- og informationssikkerhed. Styrelsen for Samfundsresiliens fører tilsyn; bøder kan gå op til enten 10 eller 7 mio. euro afhængigt af kategori.</p></div>
      <div class="card"><h3>⚠️ Registrering</h3><p>Omfattede virksomheder skal registrere sig digitalt hos styrelsen senest 14. april 2026 (efter den danske ikrafttrædelsestidslinje). Er din klient omfattet, er registreringen ikke valgfri.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>De 10 minimumsforanstaltninger (art. 21)</h2>
    <p>Kernen i NIS2 er ti krav til risikostyring. Som leverandør til en omfattet klient vil du skulle svare på alle ti:</p>
    <p><strong>1. Risikostyring og politikker</strong> — skriftlige, godkendte politikker.<br>
    <strong>2. Håndtering af hændelser</strong> — proces fra opdagelse til læring.<br>
    <strong>3. Forretningskontinuitet</strong> — backup, disaster recovery, krisestyring.<br>
    <strong>4. Supply chain-sikkerhed</strong> — vurdering af underleverandører (det er HER du møder kravet).<br>
    <strong>5. Sikker indkøbsudvikling og vedligehold</strong> — bl.a. sårbarhedshåndtering og disclosure-praksis.<br>
    <strong>6. Effektiv håndtering af sårbarheder</strong> — kendte CVE'er skal følges og udbedres.<br>
    <strong>7. Kryptografi og kryptering</strong> — hvor relevant, inkl. TLS og nøglehåndtering.<br>
    <strong>8. Menneskelig ressourcer, adgangskontrol og aktivstyring</strong> — onboarding/offboarding, mindste-privilegium, MFA.<br>
    <strong>9. Multi-faktor-godkendelse og sikker kommunikation</strong>.<br>
    <strong>10. Ledelsens ansvar</strong> — ledelsen skal godkende og trænes; manglende ansvarlighed kan koste ledelsesmedlemmer personligt.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Incident-pligten: 24 / 72 / én måned</h2>
    <p>Art. 23 giver en stram tidsramme for væsentlige hændelser — og dine klienter vil kræve, at DU melder hurtigt nok til at de kan overholde deres pligt:</p>
    <p><strong>Inden for 24 timer:</strong> tidlig advarsel til CSIRT/myndighed.<br>
    <strong>Innen for 72 timer:</strong> fuld incident-notifikation med indledende vurdering.<br>
    <strong>Innen for én måned:</strong> slutrapport med årsag, konsekvenser og afhjælpning.</p>
    <div class="problem-cards">
      <div class="card"><h3>🕐 Hvad er "væsentligt"?</h3><p>En hændelse er væsentlig hvis den forårsager eller kan forårsage alvorlig driftsforstyrrelse eller økonomisk skade, eller har ramt/skan ramme andre. En kompromitteret hosting-konto, ransomware i jeres build-pipeline eller lækagedata fra et CMS er typisk væsentligt.</p></div>
      <div class="card"><h3>🔗 Kontrakten er dit værktøj</h3><p>Sæt en meldepligt i jeres aftaler: "leverandoren melder sikkerhedshændelser til klienten uden unødig forsinkelse, senest X timer efter opdagelse". Uden den kan klienten ikke overholde sin 24-timers-frist — og det bliver et ansvargsspørgsmål.</p></div>
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>5-trins plan for små bureauer</h2>
    <p class="section-intro">Du behover sandsynligvis ikke certificering (ISO 27001 er dyr og sjældent påkravet) — men du behover dokumentation. Sådan kommer du i mål:</p>
    <p><strong>1. Kortlæg jeres systemer og data.</strong> Hvilke klientsites hoster I? Hvor ligger adgangskoder, deploy-nøgler, backups? Én oversigt rækker langt.<br>
    <strong>2. Skriv kerne-politikkerne.</strong> Incident-proces, backup-rutine, adgangsstyring (MFA på alt), sårbarhedsopdateringer. Tre-fire sider pr. stk.<br>
    <strong>3. Sæt supply chain-svar klar.</strong> Et standardsvar på klienters leverandør-spørgeskemaer: politikker, subleverandører, data-opbevaringssted, incident-kontakt.<br>
    <strong>4. Opdatér kontrakterne.</strong> Meldefrister, sikkerhedsansvar, underleverandør-liste — vores NIS2-e-bog indeholder klar-til-brug klausuler.<br>
    <strong>5. Test én gang årligt.</strong> Gennemgå incident-processen på et konkret scenario (fx "vores deploy-server er kompromitteret"). Notér resultatet — dokumenteret øvelse tæller ved tilsyn.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Scan dit site gratis →</a>
      &nbsp;&nbsp;
      <a href="/#products" class="btn-secondary">Se NIS2-e-bogen →</a>
      &nbsp;&nbsp;
      <a href="/blog/nis2-readiness-guide" class="btn-secondary">English version →</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      <div class="card"><h3>Er mit lille bureau overhovedet omfattet?</h3><p>Muligvis ikke direkte — men tjek to ting: (1) Er I i en NIS2-sektor (inkl. digitale tjenester) og over tærsklen? (2) Har I klienter, der ER omfattede? Det andet rammer næsten alle B2B-bureauer i praksis gennem kontrakter og spørgeskemaer.</p></div>
      <div class="card"><h3>Koster det en formue at blive klar?</h3><p>Nej for de fleste små bureauer. Kravene er proportionalitetsskalaede. Kerne-arbejdet er dokumentation og processer, som allerede findes i halvfærdig form i de fleste shops: backup, adgangsstyring, opdateringsrutine. Få det skriftligt og konsistent.</p></div>
      <div class="card"><h3>Hvad er bøderne?</h3><p>Op til 10 mio. euro eller 2 % af global omsætning for vigtige enheder, 7 mio. euro / 1,4 % for andre. Ledelsen kan holdes personligt ansvarlig. Men realistisk set er den hyppigste konsekvens for underleverandører tabt kontrakt — ikke bøde.</p></div>
      <div class="card"><h3>Gælder NIS2 samtidig med GDPR?</h3><p>Ja, de overlapper. GDPR beskytter persondata; NIS2 kræver operationel cybersikkerhed. En hændelse kan udløse begge pligter: 72 timer til Datatilsynet (GDPR) og 24/72 timer til cybersikkerhedsmyndigheden (NIS2). Én incident-proces skal kunne håndtere begge spor.</p></div>
      <div class="card"><h3>Hvad med EAA?</h3><p>EAA (tilgængelighedsdirektivet) er en helt anden lovgivning om produkters og tjenesters tilgængelighed. Bureauer kan blive ramt af alle tre: NIS2 (driftssikkerhed), GDPR (data) og EAA (tilgængelighed). Vores e-bøger dækker dem hver for sig.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">GDPR</span><h3><a href="/blog/cookie-consent-gdpr-2026" style="color:var(--color-accent);text-decoration:none;">Cookie-consent & GDPR 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-haandhaevelse-2026" style="color:var(--color-accent);text-decoration:none;">EAA-håndhævelse 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">FRISTER</span><h3><a href="/blog/eaa-frister-2026" style="color:var(--color-accent);text-decoration:none;">EAA-frister 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">VÆRKTØJER</span><h3><a href="/blog/gratis-nis2-vaerktoejer" style="color:var(--color-accent);text-decoration:none;">Gratis NIS2-værktøjer (dansk)</a></h3></div>
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
        <h3><a href="/blog/nis2-guide-da" style="color:inherit;text-decoration:none;">NIS2-guiden (dansk)</a></h3>
        <p>Hvem er omfattet, de 10 sikkerhedskrav, 24/72-timers incident-pligten, leverandørkæden — og en 5-trins plan for små bureauer.</p>
        <a href="/blog/nis2-guide-da" class="btn-secondary" style="margin-top:12px;">Læs guiden →</a>
      </div>
'''


def add_frontpage_card():
    p = f'{SITE}/index.html'
    c = open(p).read()
    if '/blog/nis2-guide-da' in c:
        print('frontpage card already present')
        return
    anchor = '<div style="border:1px solid var(--color-border);border-radius:12px;padding:24px;background:var(--color-surface);margin-top:20px;">\n        <h3><a href="/blog/cookie-consent-gdpr-2026"'
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
