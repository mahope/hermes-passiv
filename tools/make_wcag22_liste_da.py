#!/usr/bin/env python3
"""Iteration 287: Danish search-entry page — WCAG 2.2 krav-liste (tjekliste).

site/da/blog/wcag-22-krav-liste.html: targets Danish queries like
"wcag 2.2 krav liste", "wcag 2.2 tjekliste", "wcag 2.2 krav på dansk".
There is an existing wcag-22-aendringer.html (what changed) but no checklist
form. House template, Article + FAQPage JSON-LD, idempotent sitemap add,
internal-link check, cross-link from wcag-22-aendringer.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-26'
ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
SLUG = 'wcag-22-krav-liste'
URL = f'{BASE}/da/blog/{SLUG}'

desc = ('Komplet liste over WCAG 2.2-kravene på dansk — alle 50 kriterier på niveau '
        'A og AA på et sted, inklusive de nye i 2.2, med kort forklaring af hvert krav '
        'og hvordan du tjekker din side gratis.')

FAQS = [
    ('Hvor mange krav er der i WCAG 2.2?',
     'WCAG 2.2 har 87 succeskriterier: 30 på niveau A, 20 på niveau AA og 37 på '
     'niveau AAA. Offentlige myndigheder og de fleste lovgivninger (herunder '
     'tilgængelighedsloven/EAA) kræver niveau A og AA — altså 50 kriterier.'),
    ('Hvad er nyt i WCAG 2.2 sammenlignet med 2.1?',
     'Ni nye kriterier kom til i 2.2 — bl.a. fokusegenskab (focus appearance), '
     'trækningsbevægelser (dragging movements), hjælpefunktioner ved login '
     '(accessible authentication) og konsistent hjælp (consistent help). Samtidig '
     'blev kriteriet om fejlanalyse fjernet. De vigtigste rammer almindelige '
     'hjemmesider direkte: synligt fokus og login uden kognitive fælder.'),
    ('Er WCAG 2.2 lov i Danmark?',
     'Ikke direkte. Tilgængelighedsloven (EAA) henviser til EN 301 549, som '
     'inkorporerer WCAG 2.1 niveau A/AA — men tilsynet arbejder i praksis med den '
     'nyeste version, og EU er ved at opdatere harmoniserede standarder til 2.2. '
     'Bygger du efter WCAG 2.2 AA, er du dækket ind for begge.'),
    ('Hvad betyder niveauerne A, AA og AAA?',
     'Niveauerne er sværheds-/vigtighedsgrader. Niveau A er grundkravene (uden dem '
     'kan mange ikke bruge siden), AA er standarden som lov og kontrakter peger på, '
     'og AAA er det bedste niveau — sjældent påkrævet i sin helhed, da nogle '
     'AAA-krav ikke kan opfyldes for alle typer indhold.'),
    ('Hvordan tjekker jeg hurtigst muligt mod listen?',
     'De automatiserbare kriterier — kontrast, alt-tekster, labels, sprog, '
     'overskriftshierarki — kan tjekkes gratis med et scanner-værktøj på minutter. '
     'Resten (fokusorden, tastatnavigation) går bedst med manuel gennemgang. En '
     'gratis scanning finder typisk 80 % af de fejl, der faktisk klages over.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'WCAG 2.2-kravene på dansk — komplet liste og tjekliste',
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

# Checklist data: (level, number, Danish title, one-line explanation)
CHECKS = [
    ('A', '1.1.1', 'Ikke-tekstligt indhold', 'Alle billeder har alt-tekst; dekorative billeder har tom alt'),
    ('A', '1.2.2', 'Tekstning (undertekster)', 'Videoer med lyd har undertekster'),
    ('A', '1.2.3', 'Audiobeskrivelse eller mediakompensation', 'Videoer er tilgængelige også uden at se skærmen'),
    ('A', '1.3.1', 'Info og relationer', 'Overskrifter, lister og tabeller bruger rigtig HTML-struktur'),
    ('A', '1.3.2', 'Meningsfyldt rækkefølge', 'Indhold giver mening i DOM-rækkefølgen'),
    ('A', '1.3.4', 'Ingen begrænsning af retning', 'Intet indhold låser til kun liggende/kun stående'),
    ('A', '1.4.1', 'Brug af farve', 'Farve er aldrig eneste måde at formidle information på'),
    ('A', '1.4.2', 'Lydstyring', 'Autoplayende lyd kan slås fra'),
    ('A', '2.1.1', 'Tastatur', 'Alt fungerer med keyboard alene'),
    ('A', '2.1.2', 'Ingen tastaturfælde', 'Fokus kan altid flyttes væk igen'),
    ('A', '2.2.1', 'Justérbar timing', 'Tidsbegrænsninger kan udvides eller slås fra'),
    ('A', '2.3.1', 'Tre blink eller under grænseværdi', 'Intet blinkende indhold over grænserne'),
    ('A', '2.4.1', 'Spring over blokke', '"Hop til indhold"-link eller korrekt landmark-struktur'),
    ('A', '2.4.2', 'Sidetitel', 'Hver side har en beskrivende titel'),
    ('A', '2.4.3', 'Fokusorden', 'Tab-rækkefølgen følger logisk rækkefølge'),
    ('A', '2.4.4', 'Linkformål (i kontekst)', 'Links beskriver hvor de fører hen'),
    ('A', '2.5.1', 'Peg-bevægelser', 'Multi-point-gestus har enkeltpeg-alternativ'),
    ('A', '3.1.1', 'Sidens sprog', '<html lang="da"> (eller anden korrekt kode)'),
    ('A', '3.2.1', 'Ved fokus', 'Ingen uventede ændringer når et felt får fokus'),
    ('A', '3.2.2', 'Ved input', 'Formularer ændrer ikke kontekst uden varsel'),
    ('A', '3.3.1', 'Fejlidentifikation', 'Formularfejl beskrives i tekst ved feltet'),
    ('A', '3.3.2', 'Labels eller instruktioner', 'Alle formularfelter har synlig label'),
    ('A', '4.1.2', 'Navn, rolle, værdi', 'Komponenter (modals, dropdowns) eksponeres korrekt til skærmlæsere'),
    ('AA', '1.2.4', 'Undertekster (live)', 'Live-videoer har undertekster'),
    ('AA', '1.2.5', 'Audiobeskrivelse', 'Videoer har audiobeskrivelse'),
    ('AA', '1.3.5', 'Identificér inputformål', 'Felter som navn/e-mail understøtter autofyld'),
    ('AA', '1.4.3', 'Kontrast (minimum)', 'Tekstkcontrast mindst 4,5:1 (3:1 for stor tekst)'),
    ('AA', '1.4.4', 'Ændring af tekststørrelse', 'Teksten skaleres til 200 % uden tab af funktion'),
    ('AA', '1.4.5', 'Billeder af tekst', 'Rigtig tekst frem for tekst i billeder'),
    ('AA', '1.4.10', 'Reflow', 'Ingen vandret scroll ved 320 px bredde / 400 % zoom'),
    ('AA', '1.4.11', 'Kontrast af ikke-tekst', 'Knapper, ikoner og felter har mindst 3:1 kontrast'),
    ('AA', '1.4.12', 'Tekstmellemrum', 'Side fungerer med brugerjusteret linje-/afstand'),
    ('AA', '1.4.13', 'Indhold ved hover/fokus', 'Tooltips kan afvises og holdes'),
    ('AA', '2.4.5', 'Mange måder', 'Flere veje at finde sider på (menu, søgning, oversigt)'),
    ('AA', '2.4.6', 'Overskrifter og labels', 'Beskrivende overskrifter og feltlabels'),
    ('AA', '2.4.7', 'Synlighed af fokus', 'Tastaturfokus er tydeligt synligt'),
    ('AA', '2.5.3', 'Etiket i navn', 'Synlig label indgår i det tilgængelige navn'),
    ('AA', '2.5.4', 'Bevægelsesaktivering', 'Bevægelser (ryst) kan slås fra'),
    ('AA', '3.1.2', 'Delvis sprogangivelse', 'Ord/snit på andre sprog er markeret med lang'),
    ('AA', '3.2.3', 'Konsistent navigation', 'Navigationen ligger det samme sted på alle sider'),
    ('AA', '3.2.4', 'Konsistent identifikation', 'Samme funktion har samme ikon/tekst overalt'),
    ('AA', '3.3.3', 'Fejlforslag', 'Fejl kommer med forslag til løsning når muligt'),
    ('AA', '3.3.4', 'Fejlforebyggelse (juridisk/finansiel)', 'Vigtige indsendelser kan gennemgås eller annulleres'),
    ('AA', '4.1.3', 'Statusbeskeder', 'Dynamiske beskeder læses op (aria-live)'),
    # --- new in 2.2 ---
    ('AA', '2.4.11', 'Fokus er ikke skjult (NY I 2.2)', 'Fokus er aldrig helt skjult bag sticky headers/modals'),
    ('AA', '2.5.7', 'Alternative pegemetoder (NY I 2.2)', 'Drag-and-drop virker også med klik'),
    ('AA', '2.5.8', 'Størrelse af målområde (NY I 2.2)', 'Klikbare flader er mindst ca. 24×24 px'),
    ('AA', '3.2.6', 'Konsistent hjælp (NY I 2.2)', 'Hjælp/kontakt ligger samme sted på alle sider'),
    ('AA', '3.3.7', 'Gentagelser undgås (NY I 2.2)', 'Allerede oplyste info skal ikke tastes igen'),
    ('AA', '3.3.8', 'Login uden kognitiv test (NY I 2.2)', 'Login kræver ikke at huske/løse puslespil; alternativ findes'),
]
NEW_22 = [c for c in CHECKS if 'NY' in c[2]]

rows_a = ''.join(
    f'<tr><td>{n}</td><td>{t}</td><td>{d}</td></tr>'
    for lv, n, t, d in CHECKS if lv == 'A')
rows_aa_old = ''.join(
    f'<tr><td>{n}</td><td>{t}</td><td>{d}</td></tr>'
    for lv, n, t, d in CHECKS if lv == 'AA' and 'NY' not in t)
rows_new = ''.join(
    f'<tr class="new22"><td>{n}</td><td>{t}</td><td>{d}</td></tr>'
    for lv, n, t, d in NEW_22)

html = f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WCAG 2.2-kravene på dansk — komplet liste &amp; tjekliste (2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="WCAG 2.2-kravene på dansk — komplet liste">
<meta property="og:description" content="Alle WCAG 2.2-succeskriterier på et sted — inklusive de ni nye i 2.2 — med en kort forklaring af hver og en gratis måde at tjekke din side på.">
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
  .compare {{ width:100%; border-collapse:collapse; font-size:0.88rem; margin:1rem 0 2rem; }}
  .compare th, .compare td {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); font-size:0.85rem; text-transform:uppercase; letter-spacing:0.03em; }}
  tr.new22 td {{ background:rgba(46,160,67,0.08); }}
  .lvl-badge {{ display:inline-block; font-size:0.72rem; padding:2px 8px; border-radius:999px; background:var(--color-accent); color:#fff; margin-right:8px; vertical-align:middle; }}
  @media (max-width:640px) {{ .compare {{ font-size:0.82rem; }} .compare th:nth-child(3), .compare td:nth-child(3) {{ display:none; }} }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">TILGÆNGELIGHED &middot; WCAG 2.2 &middot; TJEKLISTE</div>
    <h1>WCAG 2.2-kravene<br>på dansk</h1>
    <p class="subtitle">Hele listen af succeskriterier på niveau A og AA — de 50 krav som tilgængelighedsloven (EAA) og offentlige myndigheder i praksis måler efter. De seks krav på A/AA-niveau der er <strong>nye i 2.2</strong>, er markeret grønt.</p>
    <div class="hero-cta">
      <a href="/scan-da" class="btn-primary">Tjek din side mod kravene gratis &rarr;</a>
      <a href="#listen" class="btn-secondary">Spring til listen</a>
    </div>
    <p class="hero-note">Opdateret {TODAY[:4]} &middot; 50 kriterier (A + AA)</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Sådan bruger du listen</h2>
    <div class="problem-cards">
      <div class="card"><h3>1️⃣ Scan automatisk</h3><p>Cirka 80 % af de fejl, der faktisk klages over, kan maskinen finde: kontrast, alt-tekster, labels, sprog. Brug den <a href="/scan-da">gratis scanner</a>.</p></div>
      <div class="card"><h3>2️⃣ Gennemgå manuelt</h3><p>Tastatnavigation, fokusorden og skærmlæser kan ikke automatiseres fuldstændigt. Tab dig igennem din side én gang med denne liste ved siden af.</p></div>
      <div class="card"><h3>3️⃣ Dokumentér</h3><p>Lav en <a href="/tilgaengelighedserklaering-generator-da">tilgængelighedserklæring</a> når problemerne er rettet — den er påkrævet under tilgængelighedsloven.</p></div>
    </div>
  </div>
</section>

<section class="products" id="listen">
  <div class="container">
    <span class="lvl-badge">NYE I 2.2</span> De kriterier på A/AA-niveau der kom til i WCAG 2.2 (to yderligere nye krav findes kun på AAA-niveau):
    <table class="compare">
      <thead><tr><th>Nr.</th><th>Krav</th><th>Hvad det betyder i praksis</th></tr></thead>
      <tbody>{rows_new}</tbody>
    </table>

    <span class="lvl-badge">NIVEAU A</span> Grundkravene — uden dem kan mange slet ikke bruge siden:
    <table class="compare">
      <thead><tr><th>Nr.</th><th>Krav</th><th>Hvad det betyder i praksis</th></tr></thead>
      <tbody>{rows_a}</tbody>
    </table>

    <span class="lvl-badge">NIVEAU AA</span> Standardkravene — det lovgivningen og kontrakter peger på (de gamle fra 2.0/2.1):
    <table class="compare">
      <thead><tr><th>Nr.</th><th>Krav</th><th>Hvad det betyder i praksis</th></tr></thead>
      <tbody>{rows_aa_old}</tbody>
    </table>

    <p style="font-size:0.85rem;color:var(--color-text-muted);">Listen viser niveau A og AA (50 kriterier). WCAG 2.2 indeholder derudover 37 AAA-kriterier, som næsten aldrig er lov-påkrævet i deres helhed. Kriterienumrene svarer til W3C's officielle nummerering, så du kan slå detaljerne op direkte hos W3C.</p>
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

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/wcag-22-aendringer" style="color:var(--color-accent);">Hvad er ændret i WCAG 2.2?</a> &middot; <a href="/da/blog/wcag-kontrast-checker" style="color:var(--color-accent);">Kontrastchecker</a> &middot; <a href="/da/blog/eaa-tjekliste-2026" style="color:var(--color-accent);">EAA-tjekliste</a> &middot; <a href="/tilgaengelighedserklaering-generator-da" style="color:var(--color-accent);">Erklæringsgenerator</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/scan-da">EAA-scanner</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/da/blog/wcag-22-aendringer">WCAG 2.2-ændringer</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = os.path.join(SITE, f'da/blog/{SLUG}.html')
with open(out, 'w') as f:
    f.write(html)

# self-checks
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

# sanity on counts
n_a = len([c for c in CHECKS if c[0] == 'A'])
n_aa = len(CHECKS) - n_a
print(f'Checklist rows: A={n_a}, AA={n_aa}, of which new-in-2.2={len(NEW_22)}')

# --- cross-link from wcag-22-aendringer (both languages if present) ---
for src_rel in ('da/blog/wcag-22-aendringer.html', 'blog/wcag-22-what-changes.html'):
    src_path = os.path.join(SITE, src_rel)
    if not os.path.exists(src_path):
        print('cross-link source missing:', src_rel)
        continue
    x = open(src_path).read()
    if SLUG not in x:
        x = x.replace('</body>', '<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="' + URL + '" style="color:var(--color-accent);">WCAG 2.2-kravene på dansk — komplet tjekliste</a></p></div>\n</body>', 1)
        open(src_path, 'w').write(x)
        print(src_rel + ': related line added')
    else:
        print(src_rel + ': already linked')

# --- llms.txt ---
ll = os.path.join(ROOT, 'site/llms.txt')
l = open(ll).read()
if '/da/blog/' + SLUG not in l:
    open(ll, 'a').write('- [WCAG 2.2-kravene pa dansk](https://hermes-passiv.pages.dev/da/blog/wcag-22-krav-liste): Complete Danish WCAG 2.2 A/AA criteria checklist including the nine new-in-2.2 requirements.\n')
    print('llms.txt: entry added')
else:
    print('llms.txt already up to date')

# --- sitemap (idempotent) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = f'<url>\n    <loc>{URL}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>0.8</priority>\n  </url>\n  '
    c = c.replace('</urlset>', entry + '</urlset>')
    open(sm, 'w').write(c)
    print('sitemap: URL added,', c.count('<loc'), 'urls total')
else:
    print('sitemap: URL already present,', c.count('<loc'), 'urls total')
xml.dom.minidom.parse(sm)
print('sitemap parses as XML')

print('\nDone:', out)
