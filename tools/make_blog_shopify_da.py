#!/usr/bin/env python3
"""Iteration 453: Danish mirror of the Shopify EAA guide.

site/blog/shopify-eaa-accessibility.html -> site/da/blog/shopify-tilgaengelighed-eaa.html
House template, Article + FAQPage JSON-LD, validated before and after writing,
hreflang sets added on BOTH sides, hreflang_pairs.json updated, idempotent
sitemap add, blog index (DA list) entry, reciprocal cross-link from the EN
post's related-guides block.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-26'
ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
EN_SLUG = 'shopify-eaa-accessibility'
SLUG = 'shopify-tilgaengelighed-eaa'
URL = f'{BASE}/da/blog/{SLUG}'
EN_URL = f'{BASE}/blog/{EN_SLUG}'

desc = ('Gør din Shopify-webshop compliant med European Accessibility Act og '
        'WCAG 2.1 AA: tema-indstillinger, Liquid-retter, app-risici, checkout '
        'og en gratis scannings-workflow — trin for trin på dansk.')

FAQS = [
    ('Gælder EAA små Shopify-butikker?',
     'Ja for e-handel med forbrugertjenester, også mikrovirksomheder — i modsætning '
     'til flere andre EAA-kategorier er der ingen generel small-business-befrielse '
     'for webshops. Byrden skalerer med størrelse, men pligterne findes.'),
    ('Er Shopify selv ansvarlig for tilgængeligheden?',
     'Platformen leverer compliant infrastruktur og fornuftige standardtemaer, men '
     'det er butiksindehaveren, der ansvar for sit konfigurerede tema, sit indhold '
     'og sine apps. Juridisk ligger ansvaret hos den, der leverer tjenesten til '
     'forbrugeren.'),
    ('Gør tilgængeligheds-widgets min butik compliant?',
     'Nej. Overlays ændrer DOM\'en efter load og kan ikke rette kontrast i billeder, '
     'ødelagte flows eller indholdsproblemer. Flere europæiske forbrugermyndigheder '
     'har frarådet at markedsføre dem som compliance. Ret årsagerne i stedet.'),
    ('Hvad med mine review-popups og app-widgets?',
     'De tælles med som en del af din tjeneste. Gennemgå hver apps kundevendte '
     'grænseflade ligesom dit tema, og udskift apps hvis leverandøren ikke vil rette '
     'tilgængelighedsfejl.'),
    ('Hvor lang tid tager det typisk?',
     'En butik på et vedligeholdt OS 2.0-tema: 1-3 dage til indstillinger, alt-tekster, '
     'Liquid-retter og test. Butikker på gamle vintage-temaer skal som regel have et '
     'temaskift, og det er det større projekt.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Shopify og tilgængelighed: gør din webshop EAA-compliant',
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

faq_html = '\n      '.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS)

html = f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Shopify og tilgængelighed: bliv EAA-compliant (guide 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Hermes Passiv">
<meta property="og:title" content="Shopify og tilgængelighed: bliv EAA-compliant">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{BASE}/cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{URL}">
<link rel="alternate" hreflang="x-default" href="{EN_URL}">
<link rel="alternate" hreflang="da" href="{URL}">
<link rel="alternate" hreflang="en" href="{EN_URL}">
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
    <div class="badge">SHOPIFY &middot; TILGÆNGELIGHED &middot; EAA</div>
    <h1>Shopify og tilgængelighed:<br>bliv EAA-compliant</h1>
    <p class="subtitle">Praktisk compliance-guide for Shopify-butikker og bureauer: hvad European Accessibility Act kræver, hvor Shopify-butikker typisk fejler, og hvilke retter du kan lave uden at røre kode.</p>
    <div class="hero-cta">
      <a href="#indhold" class="btn-primary">Læs guiden</a>
      <a href="/scan-da" class="btn-secondary">Scan din butik gratis &rarr;</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 7 minutters læsning</p>
  </div>
</header>

<section class="problem" id="indhold">
  <div class="container">
    <h2>Hvorfor Shopify og EAA hænger sammen</h2>
    <p>Enhver Shopify-butik der sælger til EU-forbrugere er omfattet af European Accessibility Act, som har gældt siden 28. juni 2025 (fristen for nye tjenester: 28. juni 2026). Det gælder dropshipping, print-on-demand og D2C-mærker. Det tekniske benchmark er EN 301 549 / WCAG 2.1 niveau AA, og håndhævelsen er national: tilsynsmyndigheder kan kræve afhjælpning, suspendere ikke-compliante tjenester og udstede bøder. For butiksindehaveren er den praktiske risiko dog mere nærliggende: accessible butikker konverterer bedre, rangerer bedre og kræves i stigende grad af indkøbere og markedspladser.</p>
    <div class="problem-cards">
      <div class="card"><h3>⚖️ Juridisk omfang</h3><p>E-handel med forbrugsvarer og -tjenester er eksplicit nævnt i EAA. Salg til EU udløser reglerne — der kræves intat EU-etablering.</p></div>
      <div class="card"><h3>📈 Konvertering</h3><p>Tilgængelighedsretter overlapper tungt med konverteringsoptimering: læsbar tekst, synligt fokus, keyboard-venlige flows, tydelige fejlbeskeder.</p></div>
      <div class="card"><h3>🛡️ Risiko</h3><p>Amerikanske ADA-kravbreve citerer i stigende grad WCAG uanset platform. En EAA-compliant butik er også meget sikrere dér.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvor Shopify-butikker typisk fejler</h2>
    <p>De fleste tilgængelighedsfejl kommer fra fire kilder: temakvalitet, apps, butikkens eget indhold og den hostede checkout du ikke fuldt styrer.</p>
    <div class="problem-cards">
      <div class="card"><h3>🎨 Temaer</h3><p>Gamle eller tunge tilpassede temaer har kontrastfejl (lysegrå udsalgsbadges), ikonknapper uden labels og manglende fokus-stile. Gratis standardtemaer som Dawn er et markant bedre udgangspunkt end de fleste betalte temaer.</p></div>
      <div class="card"><h3>🔌 Apps</h3><p>Hver app injicerer sine egne widgets — review-popups, upsell-slidere, chat-bobler. De skiber rutinemæssigt duplikerede ID'er, unlabelled kontroller og keyboard-fælder. Hver app skal tjekkes for sig.</p></div>
      <div class="card"><h3>✍️ Indhold</h3><p>Produktbilleder uden alt-tekst, "køb nu"-linkspams, overskrifter brugt som styling i stedet for struktur. Største volumenkategori på de fleste butikker.</p></div>
      <div class="card"><h3>🛒 Checkout</h3><p>Shopifys hostede checkout er stort set uden for din kontrol. Den lever rimeligt godt op til basisstandarderne; din pligt er læselig branding (ingen lavkontrast-farver) og accessible cart/drawer-flows i dit tema.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Retter i tema-indstillingerne — uden kode</h2>
    <p>Moderne Online Store 2.0-temaer eksponerer de fleste mekaniske retter som indstillinger:</p>
    <table class="compare">
      <thead><tr><th>Område</th><th>Hvad du gør</th></tr></thead>
      <tbody>
        <tr><td>Tekst og farve</td><td>Forøg tekststørrelsen og mørk farven til kontrasten klarer 4,5:1 overalt — tjek announcement bar, udsalgsbadges og footer separat</td></tr>
        <tr><td>Alt-tekster</td><td>Udfyld alt-tekst på produktbilleder i admin (varianter arver); dekorative billeder får tom <code>alt=""</code></td></tr>
        <tr><td>Fokus og bevægelse</td><td>Behold fokus-outline via <code>:focus-visible</code>; slå autospillende carousels fra eller giv pause-knap</td></tr>
        <tr><td>Navigation</td><td>Mobilmenu åbner ved tryk og lukkes med Escape; rigtige nav-elementer; skip-to-content i header.liquid</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Liquid-retter for udviklere</h2>
    <p>Redigerer du Liquid-skabeloner, så gå denne tjekliste igennem én gang pr. tema:</p>
    <p><strong>Formularlabels:</strong> nyhedsbrevsblokke og søgefelder renderes ofte som placeholder-only inputs. Tilføj rigtige <code>&lt;label&gt;</code>-elementer koblet via for/id — WCAG 3.3.2 og en af de mest almindelige scannerfund.</p>
    <p><strong>Ikonknapper:</strong> cart-toggle, antal-trin, luk-ikoner skal have aria-label. En knap der kun render'er et SVG er usynlig for hjælpemiddelteknologi.</p>
    <p><strong>Duplikerede ID'er:</strong> section rendering i loops gentager ofte <code>id="Section-..."</code>. Det bryder label-kobling og skærmlæsernavigation.</p>
    <p><strong>Overskrifthierarki:</strong> én h1 pr. side. Sektionkomponenter må ikke hardkode h2, når de allerede ligger inde i en komponent der emitter én.</p>
    <p><strong>Announcement bars og modals:</strong> dismissible, tilgængelige med tastatur, korrekt fokus-fældning mens de er åbne, og fokus returneres ved lukning.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>App-audit og checkout</h2>
    <p>To Shopify-specifikke skridt de fleste guider springer over:</p>
    <p><strong>App-audit:</strong> list alle installerede apps der renderer kundevendt UI. Fjern dem du ikke aktivt bruger (de loader stadig scripts). Tab gennem hver resterende apps widget på en live side: når du noget uden synligt fokus eller label, så omkonfigurér eller udskift appen. Undgå overlay-/tilgængeligheds-apps som compliance-strategi — de gør ikke butiken compliant, og flere europæiske forbrugerorganer har offentligt kritiseret dem.</p>
    <p><strong>Checkout-konfiguration:</strong> vælg logo/farvekombinationer der passer kontrastkravene, skriv meningsfulde sidetitler, og test hele rejsen (kurv → checkout → kvittering) kun med tastatur.</p>
    <p><strong>Dokumentér:</strong> publicér en tilgængelighedserklæring med conformansstatus, kendte begrænsninger (fx en specifik app) og en kontaktkanal. Under EAA er det forventet, ikke valgfrit.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Verificering i fem skridt</h2>
    <p>En realistisk verificeringsloop for en Shopify-butik tager en halv dag:</p>
    <p><strong>Trin 1 — automatisk scanning</strong> af forsiden, en kollektionsside, et produkt, søgeresultater og cart-drawer. Forvent 5-20 mekaniske fund første gang.</p>
    <p><strong>Trin 2 — ret og genscan</strong> tema-indstillinger og Liquid-fejl til de automatiske fund er væk.</p>
    <p><strong>Trin 3 — keyboard-gennemgang</strong> af browse → læg i kurv → checkout-start. Alt der kræver mus er en fejl under WCAG 2.1.2.</p>
    <p><strong>Trin 4 — skærmlæser-spotcheck</strong> af ét produktflow med VoiceOver eller NVDA — lyt efter unlabelled kontroller.</p>
    <p><strong>Trin 5 — kør igen efter hver temaoopdatering og ny app.</strong> Regressioner kommer lydløst med opdateringer.</p>
    <div style="text-align:center;margin-top:24px;">
      <a href="/scan-da" class="btn-primary">Scan din Shopify-butik gratis &rarr;</a>
      &nbsp;&nbsp;
      <a href="/da/blog/eaa-tjekliste-2026" class="btn-secondary">EAA-tjekliste &rarr;</a>
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
    <div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/tilgaengeligheds-overlays-eaa" style="color:var(--color-accent);">Overlays og EAA</a> &middot; <a href="/da/blog/pris-tilgaengelighedsgennemgang" style="color:var(--color-accent);">Pris på tilgængelighedsgennemgang</a> &middot; <a href="/da/blog/wcag-22-aendringer" style="color:var(--color-accent);">WCAG 2.2-ændringer</a></p></div>
  </div>
</section>

<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/scan-da">EAA-scanner</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/blog">Blog (EN)</a> &middot; <a href="{EN_URL}">Engelsk version</a></p>
  <p>Mahope © 2026 · Praktisk EU-compliance for små webbureauer</p>
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
    if ref.startswith('/api') or ref in ('/sitemap.xml', '/style.css', '/track.js', '/blog', '/free-tools'):
        continue
    p = os.path.join(ROOT, 'site', ref.lstrip('/') + '.html')
    if not os.path.exists(p):
        missing.append(ref)
assert not missing, missing
print('All internal link targets exist:', len(set(refs)), 'checked')
assert not [r for r in refs if r.endswith('.html')], 'raw .html link found'
print('No .html links')

# --- hreflang on the EN mirror (idempotent) ---
en_path = os.path.join(SITE, f'blog/{EN_SLUG}.html')
e = open(en_path).read()
hl_set = ('<link rel="alternate" hreflang="x-default" href="%s">\n'
          '<link rel="alternate" hreflang="da" href="%s">\n'
          '<link rel="alternate" hreflang="en" href="%s">' % (EN_URL, URL, EN_URL))
if 'hreflang="da"' not in e:
    e = e.replace('<link rel="canonical" href="%s">' % EN_URL,
                  '<link rel="canonical" href="%s">\n%s' % (EN_URL, hl_set))
    open(en_path, 'w').write(e)
    print('EN mirror: hreflang set added')
else:
    print('EN mirror: hreflang already present')

# --- hreflang_pairs.json ---
pf = os.path.join(SITE, 'hreflang_pairs.json')
pairs = json.load(open(pf))
if EN_SLUG not in pairs:
    pairs[EN_SLUG] = SLUG
    open(pf, 'w').write(json.dumps(pairs, indent=1, ensure_ascii=False) + '\n')
    print('hreflang_pairs.json updated (%d pairs)' % len(pairs))
else:
    print('hreflang_pairs.json already has pair')

# --- sitemap (idempotent) ---
sm = os.path.join(SITE, 'sitemap.xml')
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = ('<url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n'
             '    <priority>0.8</priority>\n  </url>\n  ' % (URL, TODAY))
    c = c.replace('</urlset>', entry + '</urlset>')
    open(sm, 'w').write(c)
    print('sitemap entry added')
else:
    print('URL already in sitemap, skipping')
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

# --- blog index: DA section ---
idx = os.path.join(SITE, 'blog/index.html')
x = open(idx).read()
if SLUG not in x:
    li = ('<li style="margin-bottom:14px"><a href="/da/blog/%s" style="color:var(--color-accent);text-decoration:none">'
          'Shopify og tilgængelighed: bliv EAA-compliant</a></li>' % SLUG)
    x = x.replace('</ul>\n</section>', li + '\n</ul>\n</section>', 1) \
        if x.count('</ul>\n</section>') else x
    # safer: insert right after the last existing /da/blog/ index entry line
    lines = x.split('\n')
    last = max(i for i, ln in enumerate(lines) if '/da/blog/' in ln and '<li' in ln)
    lines.insert(last + 1, li)
    x = '\n'.join(lines)
    open(idx, 'w').write(x)
    print('blog index: DA entry added')
else:
    print('blog index: already present')

# --- reciprocal cross-link from EN post ---
src = os.path.join(SITE, f'blog/{EN_SLUG}.html')
s = open(src).read()
if SLUG not in s:
    anchor = '<a href="/blog/accessibility-audit-cost"'
    add = '<div style="text-align:center;margin-top:16px;"><p>Dansk version: <a href="%s" style="color:var(--color-accent);">Shopify og tilgængelighed: bliv EAA-compliant</a></p></div>\n' % URL
    s = s.replace('<footer class="site-footer">', add + '<footer class="site-footer">', 1)
    open(src, 'w').write(s)
    print('EN post: Danish cross-link added')
else:
    print('EN post: cross-link already present')

print('\nDone:', out)
