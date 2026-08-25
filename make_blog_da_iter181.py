#!/usr/bin/env python3
"""Iteration 181: Danish blog post about the v1.3.6 release-integrity leak.

A real story from this project: the Chrome zip shipped for two releases
without the core fixes. Written as a practical QA lesson (release
integrity / parity testing) that also surfaces Clean Copy.

- New page  site/da/blog/release-integrity-hvad-er-det.html
- Sitemap updated, JSON-LD validated, internal link check.
No EN pendant (DA-first; EN version only if it earns traffic).
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGE = {
    'slug': 'release-integrity-hvad-er-det',
    'title': 'Release integrity: da vores udvidelse blev udgivet uden sine egne rettelser',
    'h1': 'Release Integrity:<br>Da Udgivelsen Ikke Indhold Rettelserne',
    'desc': ('En ærlig case fra et rigtigt produkt: to udgivelser hvor download-zippen '
             'manglede kernerettelserne, som tests allerede havde godkendt. Hvad '
             'release-integrity er, hvordan fejlen opstår, og den ene test der fanger den.'),
    'og_desc': ('To udgivelser. Alle tests bestod. Alligevel manglede den fil brugerne '
                'downloadede de vigtigste rettelser. Sådan opdagede vi det — og den '
                'ene test der forhindrer det i at ske igen.'),
    'badge': 'QA &middot; RELEASE INTEGRITY &middot; CASE',
    'subtitle': ('Alle testene var grønne. Bygget var grønt. Alligevel manglede den zip-fil '
                 'brugerne downloadede de vigtigste fejlrettelser fra de seneste to '
                 'udgivelser. Her er hvad der gik galt — og den ene test der had '
                 'fanget det før udgivelsen.'),
    'cta1': ('<a href="/da/blog/indsæt-uden-formatering-i-chrome" class="btn-primary">'
             'Se produktet Clean Copy &rarr;</a>'),
    'cta2': '<a href="#laering" class="btn-secondary">Spring til læringerne</a>',
    'tool_url': '/da/blog/indsæt-uden-formatering-i-chrome',
    'tool_label': 'Prøv Clean Copy gratis',
    'faq': [
        ("Hvad betyder release integrity?",
         "At det du udgiver, er identisk med det du testede. Ikke \"bygget fra samme "
         "kodebase\" eller \"for det meste ens\" — men bit-for-bit de samme filer, "
         "samme versioner, ingen ældre artefakter blandet ind. Integrity fejler typisk "
         "ikke i koden, men i pakningen: hvilke filer der havner i artefaktet."),
        ("Hvorfor fangede enhedstests ikke fejlen?",
         "Fordi de testede kildefilen. Kernen havde alle rettelserne, og testene mod "
         "kernen bestod. Fejlen lå et andet sted: i en kopi af koden, der blev pakket "
         "ind i zip-filen, og som ingen test læste. En test kan kun garantere det, "
         "den faktisk indlæser."),
        ("Hvad er en parity-test?",
         "En test der sammenligner to ting, der burde være ens: fx kildetool.js og "
         "den kopier af tool.js, der ligger i udgivelsespakken. Hvis de adskiller "
         "sig, fejler buildet — uanset om funktionstests ellers er grønne. Den fanger "
         "præcis den klasse af fejl, hvor noget bliver vedligeholdt to steder."),
        ("Hvordan undgår jeg det i mit eget projekt?",
         "Tre regler: (1) Generér kopier fra kilden i stedet for at vedligeholde dem "
         "manuelt — ét sandhedssted. (2) Lad bygge-scriptet splicse delt kode ind i "
         "artefaktet automatisk. (3) Tilføj én parity-test, der verificerer at "
         "artefaktets indhold matcher kilden, og lad den køre før hver udgivelse."),
    ],
    'body': '''
<section class="problem" id="problem">
  <div class="container">
    <h2>Hvad der skete</h2>
    <p>Dette er en sand historie fra udviklingen af browser-udvidelsen
    <a href="/da/blog/indsæt-uden-formatering-i-chrome" style="color:var(--color-accent);">Clean Copy</a>.
    Projektet har én kernefil med al logikken (<code>clean_copy_core.js</code>) og seks
    overflader der bruger den: Chrome-udvidelse, Firefox-udvidelse, CLI-værktøj,
    bookmarklet, Obsidian-plugin og desktop-app.</p>
    <p>Ved en gennemgang opdagede vi noget ubehageligt: Chrome-udvidelsens baggrunds-script
    indeholdt <strong>ikke</strong> rettelserne fra de seneste to udgivelser. De lå i
    kernefilen — og i Firefox-versionen. Men den fil, der faktisk blev pakket i
    Chrome-zippen, var en ældre kopi.</p>
    <div class="problem-cards">
      <div class="card"><h3>✅ Tests: grønne</h3><p>Enheds- og integrationstestene kørte mod kernefilen. Den havde alle rettelser. Alt så perfekt ud.</p></div>
      <div class="card"><h3>📦 Artefakt: forkert</h3><p>Zip-filen indeholdt en manuel kopi af kernen — to udgivelser gammel, uden de nye fixes.</p></div>
      <div class="card"><h3>🚫 Brugere: ramt</h3><p>Alle der downloadede udvidelsen i den periode fik et produkt uden de rettelser, udgivelsesnoterne lovede.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvordan sker sådan noget?</h2>
    <p>Klassisk årsag: <strong>samme logik vedligeholdt flere steder.</strong> Da projektet
    var lille, blev kernen kopieret ind i hvert projekt med håndkraft. Kopien i
    Chrome-mappen blev simpelthen glemt i to iterationer — mens kilden og Firefox-kopien
    blev opdateret.</p>
    <ul>
      <li><strong>Manuelle kopier af kode er tidsbomber.</strong> De virker fint, indtil nogen glemmer én. Og der er ingen alarm, når det sker.</li>
      <li><strong>Tests tester kun, hvad de indlæser.</strong> Vores tests importerede kernefilen direkte. De vidste intet om, hvad der lå i zippen.</li>
      <li><strong>Udgivelsespresset forstærker det.</strong> Man bygger zips sidst, hurtigt, efter alt er godkendt. Netop dét trin får aldrig den opmærksomhed, det fortjener.</li>
    </ul>
  </div>
</section>

<section class="products" id="fix">
  <div class="container">
    <h2>Fiksen: ét sandhedssted + én parity-test</h2>
    <ol>
      <li><strong>Ingen manuelle kopier.</strong> Kernelogikken findes nu kun i én fil.
      Bygge-scriptet genererer alle kopier — udvidelsernes scripts får kernen
      <em>splicet ind</em> under bygning, med markerede blokke.</li>
      <li><strong>Parity-test før udgivelse.</strong> Én test læser den færdige zip,
      udpakker den, og sammenligner kernesektionen byte-for-byte med kilden. Afviger de,
      fejler buildet. Ingen udgivelse uden grøn parity-test.</li>
      <li><strong>Versionsbump før zips bygges.</content></strong> Regel: indholdsændring ⇒ versionsnummer op, <em>altid</em>, inden artefaktet bygges. Så kan man aldrig forveksle en ny zip med en gammel.</li>
      <li><strong>Efterudgivelses-verificering.</strong> Efter deploy hentes zip-filen live fra sitet og kontrolleres — samme parity-tjek, men mod det brugerne faktisk downloader.</li>
    </ol>
  </div>
</section>

<section class="products" id="laering">
  <div class="container">
    <h2>Tre læringer du kan bruge i morgen</h2>
    <ol>
      <li><strong>Test artefaktet, ikke bare kilden.</strong> Det brugeren modtager er zip-filen, pakken, installeret. Din test-suite skal mindst én gang åbne præcis det.</li>
      <li><strong>Sammensatte projekter skal generere, ikke kopiere.</strong> Hvis samme funktion findes i to filer, vil de på et tidspunkt være forskellige. Spørgsmålet er ikke <em>om</em>, men hvornår — og om en test opdager det.</li>
      <li><strong>Parity-testen er billig og fanger en hel fejlklasse.</strong> Den kræver ingen framework: læs to filer, sammenlign, fejlstå hvis ulige. Ti linjer kode der reddede os fra at udgive forkert indhold en tredje gang.</li>
    </ol>
    <p>Fejlen kostede os to udgivelser og en del tillid hos os selv. Fiksen kostede en
    eftermiddag. Det er den bedste investering projektet har lavet.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/da/blog/indsæt-uden-formatering-i-chrome" class="btn-primary">Prøv Clean Copy gratis &rarr;</a>
      &nbsp;
      <a href="/da/blog/kopier-som-markdown-udvidelse" class="btn-secondary">Flere guides</a>
    </div>
  </div>
</section>
'''.replace('</content>', ''),  # guard against stray tag
    'related': ('<a href="/da/blog/indsæt-uden-formatering-i-chrome" lang="da">Indsæt uden formatering i Chrome</a> &middot; '
                '<a href="/da/blog/kopier-som-markdown-udvidelse" lang="da">Kopier som Markdown</a> &middot; '
                '<a href="/da/blog/html-til-markdown-konverter" lang="da">HTML til Markdown</a>'),
}


def build_page(p):
    url = f'{BASE}/da/blog/{p["slug"]}'
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': p['title'], 'description': p['desc'],
        'url': url,
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Clean Copy'},
        'publisher': {'@type': 'Organization', 'name': 'Clean Copy'},
    }, ensure_ascii=False)
    main_entity = [{"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p['faq']]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage',
                         'mainEntity': main_entity}, ensure_ascii=False)

    faq_cards = '\n'.join(
        f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in p['faq'])

    return f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p['title']}</title>
<meta name="description" content="{p['desc']}">
<meta property="og:type" content="article">
<meta property="og:title" content="{p['title']}">
<meta property="og:description" content="{p['og_desc']}">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{p['badge']}</div>
    <h1>{p['h1']}</h1>
    <p class="subtitle">{p['subtitle']}</p>
    <div class="hero-cta">
      {p['cta1']}
      {p['cta2']}
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 6 minutters læsning</p>
  </div>
</header>
{p['body']}
<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
{faq_cards}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="{p['tool_url']}" class="btn-primary">{p['tool_label']} &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: {p['related']}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/scan-da">Scanner</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>'''


def update_sitemap(slug):
    path = f'{SITE}/sitemap.xml'
    c = open(path).read()
    url = f'{BASE}/da/blog/{slug}'
    if f'<loc>{url}</loc>' in c:
        print(f'sitemap: {slug} already present')
        return
    add = (f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
           f'<changefreq>weekly</changefreq><priority>0.7</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(path, 'w').write(c)
    print(f'sitemap: added {slug}')


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
    out = f'{SITE}/da/blog/{PAGE["slug"]}.html'
    page = build_page(PAGE)
    assert '</content>' not in page
    with open(out, 'w') as f:
        f.write(page)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org', d['@context']
    print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')
    update_sitemap(PAGE['slug'])

    files = [out]
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')
    sx = open(f'{SITE}/sitemap.xml').read()
    assert '</urlset>' in sx
    assert '.html</loc>' not in sx
    print('sitemap URLs:', sx.count('<loc>'))
    print('Done')


if __name__ == '__main__':
    main()
