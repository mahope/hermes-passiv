#!/usr/bin/env python3
"""Iteration 285: Danish search-entry page — EAA-frist juni 2026 (nu håndhævelse).

site/da/blog/eaa-frist-hvad-nu.html: targets Danish queries like
"eaa frist", "tilgængelighedsloven frist 2026", "hvad gør jeg nu eaa" —
low competition, and the Danish pages are already the best-indexed entry.
House template, Article + FAQPage JSON-LD, idempotent sitemap add,
internal-link check, cross-link from the existing eaa-frister-2026 post.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
SLUG = 'eaa-frist-hvad-nu'
URL = f'{BASE}/da/blog/{SLUG}'

desc = ('EAA-fristen var 28. juni 2026 — og den er nu passeret. Her er hvad reglerne '
        'betyder nu: hvem der kan klage, hvilke bøder der kan komme, og hvordan du '
        'tjekker og fikser din hjemmeside gratis på én eftermiddag.')

FAQS = [
    ('Er EAA-fristen virkelig passeret?',
     'Ja. Fristen for at nye tjenester skulle opfylde European Accessibility Act var '
     '28. juni 2026. Kravene gælder nu, og tilsynsmyndighederne i EU-medlemslandene '
     'kan håndhæve dem over for virksomheder, der ikke lever op.'),
    ('Hvem kan klage over min hjemmeside?',
     'Enhver bruger kan klage til det nationale tilsynsorgan — i Danmark er det '
     'Digitaliseringsstyrelsen. Klager behandles uden gebyr for borgeren, så en '
     'utilgængelig betalingsflow eller bookingformular reelt kan blive meldt af enhver '
     'besøgende.'),
    ('Hvor store er bøderne ved manglende tilgængelighed?',
     'Det afhænger af medlemslandet. I Danmark fastsættes bøder individuelt og kan '
     'følges op af påbud om at rette problemerne inden for en frist. I andre lande som '
     'Frankrig når bøderne op i titusinder af euro. Det dyre er dog sjældent bøden — '
     'det er tvunget eftersomarbejde under tidspres.'),
    ('Hvor lang tid tager det at tjekke min hjemmeside?',
     'Et første tjek med et gratis scanner-værktøj tager minutter. De typiske problemer '
     '— manglende alt-tekster, for lav kontrast, formularefelter uden labels — kan ofte '
     'rettes på en enkelt eftermiddag. En komplet revision tager længere, men 80 % af '
     'klagepunkterne findes med automatiske værktøjer.'),
    ('Gælder reglerne min lille webshop?',
     'Reglerne gælder mikrovirksomheder med færre end ti ansatte kun delvist, men de '
     'fleste webshops ligger over grænsen — og betalingsudbydere og e-handelsplatforme '
     'kræver i stigende grad tilgængelighed uanset. Tjek status før du antager, at du er undtaget.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'EAA-fristen er passeret — hvad betyder det for din hjemmeside nu?',
    'description': desc,
    'url': URL,
    'datePublished': TODAY, 'dateModified': TODAY,
    'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
}
FAQPAGE = {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS],
}
for block in (ARTICLE, FAQPAGE):
    assert block['@context'] == 'https://schema.org', block['@context']
    json.loads(json.dumps(block))

faq_html = '\n'.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS)

html = f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EAA-fristen er passeret — hvad gør du nu? (Guide 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="EAA-fristen er passeret — hvad gør du nu?">
<meta property="og:description" content="Tilgængelighedslovens frist gik 28. juni 2026. Se hvad reglerne betyder nu, og hvordan du tjekker din hjemmeside gratis på en eftermiddag.">
<meta property="og:url" content="{URL}">
<link rel="canonical" href="{URL}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">
{json.dumps(ARTICLE, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(FAQPAGE, ensure_ascii=False)}
</script>
<script defer src="/track.js"></script>
<style>
  .compare {{ width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }}
  .compare th, .compare td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">TILGÆNGELIGHED &middot; EAA &middot; DANMARK</div>
    <h1>Fristen gik 28. juni 2026.<br>Hvad betyder det nu?</h1>
    <p class="subtitle">European Accessibility Act (i Danmark: tilgængelighedsloven) er ikke en fremtidig regel længere. Kravene gælder, klageadgangen er åben, og myndighederne kan håndhæve. Godt nyt: de fleste fejl på almindelige hjemmesider kan findes og rettes gratis — på én eftermiddag.</p>
    <div class="hero-cta">
      <a href="/scan-da" class="btn-primary">Tjek din side gratis &rarr;</a>
      <a href="#nu" class="btn-secondary">Se hvad reglerne betyder</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters læsning</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Den korte version af situationen efter fristen</h2>
    <div class="problem-cards">
      <div class="card"><h3>⚖️ Reglerne gælder allerede</h3><p>Nye tjenester skulle være compliant fra 28. juni 2026. Eksisterende tjenester følger senest i 2030 — men jo tidligere du retter, jo mindre risiko løber du op.</p></div>
      <div class="card"><h3>📢 Alle kan klage</h3><p>Klagevejen til Digitaliseringsstyrelsen koster borgeren intet. En utilgængelig bookingformular eller betalingstrin er netop det, loven dækker.</p></div>
      <div class="card"><h3>🔧 Rettingerne er billige nu</h3><p>Manglende alt-tekster, lav kontrast og labels på formularfelter findes automatisk. Det er billigere at rette dem selv end at modtage et påbud.</p></div>
    </div>
  </div>
</section>

<section class="products" id="nu">
  <div class="container">
    <h2>Tre trin til at komme oven vandet</h2>

    <h3 style="margin-top:24px;">1. Scan din side gratis</h3>
    <p><a href="/scan-da" style="color:var(--color-accent);">Den gratis EAA-scanner</a> gennemgår en given URL for de klassiske WCAG-fejl: kontrast, alt-tekster, labels, sprogangivelse og mere. Du får en rapport med konkrete fund — ingen konto nødvendig.</p>

    <h3 style="margin-top:24px;">2. Ret de mest almindelige fejl</h3>
    <table class="compare">
      <thead><tr><th>Typisk fund</th><th>Hvordan rettes det</th></tr></thead>
      <tbody>
        <tr><td>Billede uden alt-tekst</td><td>Kort beskrivende tekst i <code>alt</code>-attributten; dekorative billeder får tom alt</td></tr>
        <tr><td>Tekst/kontrast under 4,5:1</td><td>Mørkere tekst eller lysere baggrund — tjekket med den gratis <a href="/contrast-checker-da" style="color:var(--color-accent);">kontrastchecker</a></td></tr>
        <tr><td>Formularfelt uden label</td><td><code>&lt;label for&gt;</code> kobles til feltet</td></tr>
        <tr><td>Ingen sprogangivelse</td><td><code>&lt;html lang="da"&gt;</code> på alle sider</td></tr>
      </tbody>
    </table>

    <h3 style="margin-top:24px;">3. Dokumentér det</h3>
    <p>Siden kræver en <a href="/tilgaengelighedserklaering-generator-da" style="color:var(--color-accent);">tilgængelighedserklæring</a>. Generatoren laver en korrekt udformet erklæring på dansk på få minutter — inklusive link til klagevejen.</p>

    <div class="problem-cards">
      <div class="card"><h3>✅ Gratis hele vejen</h3><p>Scanner, kontrastchecker og erklæringsgenerator koster ingenting og kræver ingen konto.</p></div>
      <div class="card"><h3>🇩🇰 Dansk først</h3><p>Værktøjerne findes både på dansk og engelsk, og rapporterne bruger WCAG-kriterierne som tilsynet også måler efter.</p></div>
      <div class="card"><h3>🔐 Ingen data indsamlet</h3><p>Du scanner din egen side — resultaterne sendes ikke videre nogen steder.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Start med en gratis scanning &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/eaa-tjekliste-2026" style="color:var(--color-accent);">EAA-tjekliste</a> &middot; <a href="/da/blog/eaa-frister-2026" style="color:var(--color-accent);">Alle EAA-frister</a> &middot; <a href="/da/blog/pris-tilgaengelighedsgennemgang" style="color:var(--color-accent);">Pris på tilgængelighedsgennemgang</a> &middot; <a href="/da/blog/gratis-tilgaengelighedsvaerktoejer" style="color:var(--color-accent);">Gratis tilgængelighedsværktøjer</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/scan-da">EAA-scanner</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/da/blog/eaa-tjekliste-2026">EAA-tjekliste</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(SITE, f'da/blog/{SLUG}.html')
with open(out, 'w') as f:
    f.write(html)

content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

refs = re.findall(r'href="(/[^"#]+)"', content)
missing = []
for ref in set(refs):
    if ref.startswith('/api') or ref in ('/sitemap.xml', '/style.css', '/track.js'):
        continue
    p = os.path.join(ROOT, 'site', ref.lstrip('/') + '.html')
    if not os.path.exists(p):
        missing.append(ref)
assert not missing, missing
print('All internal link targets exist:', len(set(refs)), 'checked')
bad = [r for r in refs if r.endswith('.html')]
assert not bad, bad
print('No .html links')

# --- sitemap (idempotent) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = f'<url>\n    <loc>{URL}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>0.8</priority>\n  </url>\n  '
    c = c.replace('</urlset>', entry + '</urlset>')
else:
    print('URL already in sitemap, skipping')
open(sm, 'w').write(c)
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

# --- cross-link from existing eaa-frister-2026 post ---
src_path = os.path.join(SITE, 'da/blog/eaa-frister-2026.html')
x = open(src_path).read()
if SLUG not in x:
    x = x.replace('</body>', '<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="' + URL + '" style="color:var(--color-accent);">EAA-fristen er passeret — hvad nu?</a></p></div>\n</body>', 1)
    open(src_path, 'w').write(x)
    print('eaa-frister-2026: related line added')
else:
    print('eaa-frister-2026 already linked')

# --- llms.txt: add both new pages if missing ---
ll = os.path.join(ROOT, 'site/llms.txt')
l = open(ll).read()
adds = []
if '/clean-copy-brew' not in l:
    adds.append('- [Clean Copy CLI via Homebrew](https://hermes-passiv.pages.dev/clean-copy-brew): one-command brew install of the HTML-to-Markdown CLI.')
if '/da/blog/' + SLUG not in l:
    adds.append('- [EAA-fristen er passeret — hvad nu?](https://hermes-passiv.pages.dev/da/blog/eaa-frist-hvad-nu): Danish guide on what the June 2026 accessibility deadline means now, with free checking tools.')
if adds:
    open(ll, 'a').write('\n'.join(adds) + '\n')
    print('llms.txt:', len(adds), 'entries added')
else:
    print('llms.txt already up to date')

print('\nDone:', out)
