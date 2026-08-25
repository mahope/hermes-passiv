#!/usr/bin/env python3
"""Iteration 103: Danish counterpart of /blog/gdpr-agency-role ->
/blog/gdpr-rolle-webbureau plus frontpage card.
Same safety pattern as iter.97-102: JSON-LD validated with json.loads,
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
    slug = 'gdpr-rolle-webbureau'
    desc = ('GDPR for webbureauer i 2026: hvilken rolle spiller bureauet '
            '(dataansvarlig eller databehandler), cookies og samtykke, '
            'databehandleraftaler, hostingvalg, 72-timers-reglen — og en '
            '5-trins tjekliste.')
    h = head(slug, 'da',
             'GDPR-guide 2026: Webbureauets rolle forklaret',
             desc,
             'GDPR: Hvem har ansvaret \u2014 bureauet eller kunden?',
             'Dataansvarlig eller databehandler? Cookies, DBA\\u2019er, hosting, 72-timers-reglen og en 5-trins tjekliste.',
             'GDPR-guide: Webbureauets rolle og ansvar i 2026')
    body = f'''
<body><header class="hero">
  <div class="container">
    <div class="badge">BLOG · GDPR</div>
    <h1>GDPR:<br>Hvem har ansvaret &mdash; bureauet eller kunden?</h1>
    <p class="subtitle">Webbureauer r&oslash;rer persondata hver dag &mdash; kontaktformularer, analytics, nyhedsbreve, backups af kundesider. Alligevel er der vedvarende forvirring om, hvem der b&aelig;rer ansvaret. Svaret afh&aelig;nger af din rolle. Her er rollerne forklaret, de fem klassiske fejl og en 5-trins tjekliste.</p>
    <div class="hero-cta">
      <a href="#content" class="btn-primary">L&aelig;s guiden</a>
      <a href="/scan" class="btn-secondary">Scan din side gratis &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 · L&aelig;setid: 7 minutter</p>
  </div>
</header>

<section class="problem" id="content">
  <div class="container">
    <h2 id="roller">To roller: dataansvarlig og databehandler</h2>
    <p>GDPR (forordning 2016/679) definerer to hovedroller, og det er dem, der afg&oslash;r, hvem der skal svare over for tilsynet:</p>
    <div class="problem-cards">
      <div class="card"><h3>&#127919; Dataansvarlig</h3><p>Den part, der bestemmer, <em>hvorfor</em> og i store tr&aelig;k <em>hvordan</em> data behandles. Din kunde er typisk dataansvarlig for sin sides data: kunden bestemmer form&aring;lene (markedsf&oslash;ring, salg) og midlerne (CMS, nyhedsbrevsv&aelig;rkt&oslash;j).</p></div>
      <div class="card"><h3>&#128295; Databehandler</h3><p>Den part, der behandler data p&aring; den ansvarliges instruks. Et bureau, der vedligeholder en kundeside med adgang til brugerdata via admin-logins, backups eller staging-milj&oslash;er, er typisk databehandler.</p></div>
      <div class="card"><h3>&#9878;&#65039; Begge dele p&aring; samme tid</h3><p>Mange bureauer er begge: databehandler for kundernes sidedata &mdash; men selvst&aelig;ndig dataansvarlig for egne data (medarbejdere, egne leads, analytics p&aring; eget dom&aelig;ne).</p></div>
    </div>
    <p><strong>Hvorfor det betyder noget:</strong> som databehandler kan du ikke bare &quot;f&oslash;lge kundens instruks&quot;, hvis den bryder GDPR &mdash; I er begge udsat. Og uden en skriftlig databehandleraftale (DBA) er behandlingen ulovlig fra dag &eacute;n (art. 28).</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>De fem klassiske bureau-fejl</h2>
    <p><strong>1. Ingen databehandleraftale.</strong> Art. 28 kr&aelig;ver en skriftlig DBA F&Oslash;R behandlingen starter &mdash; ikke &quot;det n&aring;r vi senere&quot;. Det g&aelig;lder ogs&aring; jeres underbehandlere (hosting, e-mail).</p>
    <p><strong>2. Cookies f&oslash;r samtykke.</strong> Ikke-n&oslash;dvendige cookies (analytics, markedsf&oslash;ring, sociale plugins) m&aring; kun s&aelig;ttes efter aktivt, informeret samtykke &mdash; og det skal v&aelig;re lige let at sige nej som ja. Et banner med &quot;Accept&eacute;r alle&quot; og en gemt afvis-knap lever ikke op til kravene.</p>
    <p><strong>3. Analytics uden retsgrundlag.</strong> En standard Google Analytics-ops&aelig;tning sender data til USA. Europ&aelig;iske datatilsyn har afgjort, at det kr&aelig;ver ekstra sikkerheder (IP-afrunding, DBA, evt. proxy-l&oslash;sninger) &mdash; ellers er trafikdata i praksis persondata uden lovligt grundlag.</p>
    <p><strong>4. Formularer videresendt som e-mail.</strong> Kontaktformularer sendt som mail spreder persondata ud i postkasser uden opbevaringsgr&aelig;nse eller adgangsstyring. Bedre: lad indsendelser lande direkte i CMS/databasen med logget adgang.</p>
    <p><strong>5. Glemte staging- og backupmilj&oslash;er.</strong> Kopier af produktionssider med &aelig;gte brugerdata ligger ofte ubeskyttet p&aring; staging-dom&aelig;ner. Enten anonymiser dataene, eller l&aring;s milj&oslash;erne bag login &mdash; og s&aelig;t en sletningsfrist.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>72-timers-reglen &mdash; den g&aelig;lder ogs&aring; bureauet</h2>
    <p>Ved brud p&aring; persondatasikkerheden skal den dataansvarlige underrette tilsynet <strong>inden for 72 timer</strong>, hvor risikoen er reel (art. 33). Som databehandler er din pligt skarpere: <strong>du skal underrette kunden uden un&oslash;dig forsinkelse</strong>, efter du er blevet opm&aelig;rksom p&aring;bruddet (art. 33, stk. 2).</p>
    <p>I praksis: opdager du, at en kundeside er kompromitteret, startede kundens 72-timersur med det samme &mdash; og din underrettelsespligt g&oslash;r jeres reaktionstid til et kontraktsp&oslash;rgsm&aring;l. Hav en skriftlig incidentproces klar: hvem opdager, hvem vurderer, hvem underretter, inden for hvor mange timer.</p>
    <div class="problem-cards">
      <div class="card"><h3>&#128221; Hvad skal en DBA indeholde?</h3><p>Art. 28, stk. 3, lister minimumet: genstand og varighed, art og form&aring;l, datakategorier, den ansvarliges rettigheder og pligter, fortrolighed, sikkerhedsforanstaltninger, underbehandlere, hj&aelig;lp til underrettelse, sletning/tilbagelevering og revisionsret. Vor e-bog indeholder en klar-til-brug skabelon.</p></div>
      <div class="card"><h3>&#127757; Hosting og tredjelande</h3><p>Kunder sp&oslash;rger i stigende grad, hvor deres side hostes. EU/E&Oslash;S-hosting fjerner et helt kapitel om tredjelandsoverf&oslash;rsler. Bruger du underbehandlere i tredjelande, skal de st&aring; i DBA\\u2019en og v&aelig;re d&aelig;kket af standardkontraktklausuler.</p></div>
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="container">
    <h2>En 5-trins tjekliste for dit bureau</h2>
    <p class="section-intro">S&aring;dan f&aring;r I det basale p&aring; plads &mdash; uden at det bliver et m&aring;nederlangt projekt:</p>
    <p><strong>1. Kortl&aelig;gg jeres dataprocesser.</strong> Hvilke kundesider har I adgang til? Hvor lander formulardata? Hvilke v&aelig;rkt&oslash;jer s&aelig;tter I selv op (analytics, nyhedsbreve)? &Eacute;n oversigt r&aelig;kker langt.<br>
    <strong>2. F&aring; DBA p&aring; alle kundeforhold.</strong>&Eacute;n standardskabelon + en kort proces: send ved kontraktstart, arkiv&eacute;r den underskrevne version.<br>
    <strong>3. Ryd op i cookies og tracking.</strong> Samtykkebanner med lige vilk&aring;r for ja/nej, kun n&oslash;dvendige cookies f&oslash;r samtykke, dokumenteret cookiepolitik.<br>
    <strong>4. Skriv incidentprocessen.</strong> &Eacute;n side: opdagelse &rarr; vurdering &rarr; kundeunderrettelse (timer, ikke dage) &rarr; hj&aelig;lp til tilsynsrapporten.<br>
    <strong>5. Gennemg&aring; &aring;rligt.</strong> Nye kunder, nye v&aelig;rkt&oslash;jer, nye underbehandlere? Opdat&eacute;r listen og aftalerne. En dokumenteret gennemgang t&aelig;ller ved revision.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan" class="btn-primary">Scan din side gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/#products" class="btn-secondary">Se GDPR-e-bogen &rarr;</a>
      &nbsp;&nbsp;
      <a href="/blog/nis2-guide-da" class="btn-secondary">NIS2-guiden &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede sp&oslash;rgsm&aring;l</h2>
    <div class="problem-cards">
      <div class="card"><h3>Er bureauet ansvarligt for kundens cookies?</h3><p>Som udgangspunkt nej &mdash; kunden bestemmer form&aring;let med tracking. MEN: s&aelig;tter I cookien op, valgte I teknisk l&oslash;sning og leverede konfigurationen. S&oslash;rg for, at kunden aktivt godkendte ops&aelig;tningen, og at samtyccel&oslash;sningen faktisk virker. Ansvaret kan v&aelig;re delt (art. 26, f&aelig;lles ansvar).</p></div>
      <div class="card"><h3>Skal vi ogs&aring; have en DBA med hostingleverand&oslash;ren?</h3><p>Ja &mdash; hosting af en hjemmeside med persondata er behandling p&aring; den ansvarliges vegne. Enten er kunden den direkte part (typisk n&aring;r kunden ejer hostingkontoen), eller ogs&aring; er I mellemled og skal have egen aftale med hosten, der videref&oslash;r de samme krav.</p></div>
      <div class="card"><h3>Hvor store er b&oslash;derne?</h3><p>Op til 20 mio. euro eller 4 % af global oms&aelig;tning for alvorlige principbrud; 10 mio. euro / 2 % for fx manglende DBA\\u2019er eller utilstr&aelig;kkelig sikkerhed. For sm&aring; virksomheder er den realistiske risiko dog oftest p&aring;bud, tilsynssager og mistet tillid.</p></div>
      <div class="card"><h3>G&aelig;lder GDPR overhovedet sm&aring; sider?</h3><p>Ja. GDPR har ingen st&oslash;rrelsesgr&aelig;nse &mdash; kun undtagelser for rent privat brug. En firmakontaktside med navne og e-mails er persondata, uanset om virksomheden har tre eller tre hundrede ansatte.</p></div>
      <div class="card"><h3>Hvordan forholder det sig til NIS2 og EAA?</h3><p>Tre spor: GDPR beskytter persondata, NIS2 kr&aelig;ver operationel cybersikkerhed, EAA forlanger tilg&aelig;ngelighed. &Eacute;n enkelt h&aelig;ndelse kan ramme flere spor p&aring; samme tid. Se vores NIS2- og EAA-guides for de andre s&oslash;jler.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Relaterede guides</h2>
    <div class="problem-cards">
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">COOKIES</span><h3><a href="/blog/cookie-consent-gdpr-compliance" style="color:var(--color-accent);text-decoration:none;">Cookie-samtykke &amp; GDPR 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">NIS2</span><h3><a href="/blog/nis2-guide-da" style="color:var(--color-accent);text-decoration:none;">NIS2-guiden (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">EAA</span><h3><a href="/blog/eaa-frister-2026" style="color:var(--color-accent);text-decoration:none;">EAA-frister 2026 (dansk)</a></h3></div>
      <div class="card"><span class="badge" style="font-size:0.75em;display:inline-block;margin-bottom:6px;">V&AElig;RKT&Oslash;J</span><h3><a href="/free-tools" style="color:var(--color-accent);text-decoration:none;">Gratis compliance-v&aelig;rkt&oslash;j</a></h3></div>
    </div>
  </div>
</section>

<footer style="padding:32px 24px;">
    <p><a href="/">← Forside</a> &middot; <a href="/scan">Gratis scanner</a> &middot; <a href="/free-tools">Gratis v&aelig;rkt&oslash;j</a> &middot; <a href="/#blog">Blog</a></p>
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
        <h3><a href="/blog/gdpr-rolle-webbureau" style="color:inherit;text-decoration:none;">GDPR-guide: webbureauets rolle (dansk)</a></h3>
        <p>Dataansvarlig eller databehandler? DBA-pligter, cookies, hosting, 72-timers-reglen &mdash; plus en 5-trins tjekliste for bureauer.</p>
        <a href="/blog/gdpr-rolle-webbureau" class="btn-secondary" style="margin-top:12px;">L&aelig;s guiden &rarr;</a>
      </div>
'''


def add_frontpage_card():
    p = f'{SITE}/index.html'
    c = open(p).read()
    if '/blog/gdpr-rolle-webbureau' in c:
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
