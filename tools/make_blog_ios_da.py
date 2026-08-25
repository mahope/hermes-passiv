#!/usr/bin/env python3
"""Iteration 239: Danish mirror of iteration 238's iOS blog post.

Ny post: site/da/blog/kopier-tabel-iphone-ipad.html (DA-modstykke til EN
copy-table-website-iphone-ipad). House-template, Article + FAQPage JSON-LD,
idempotent: sitemap dedupe, krydslink fra EN-posten, relateret-linje,
sitemap-validering og intern linktjek.
"""
import json, os, re, xml.dom.minidom

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')
SLUG = 'kopier-tabel-iphone-ipad'
URL = f'{BASE}/da/blog/{SLUG}'

desc = ('Sådan kopierer du en tabel fra en hjemmeside på iPhone og iPad — og får den '
        'ind i Noter, Numbers, Excel eller Notion med rækker og kolonner intakte. Gratis '
        'Safari-bookmarklet-metode uden app.')

FAQS = [
    ('Kan man kopiere en tabel fra en hjemmeside på en iPhone?',
     'Ja. Tricket er et Safari-bookmarklet: gem en vilkårlig side som bogmærke, redigér '
     'den og indsæt Clean Copy-bookmarklet-adressen. Åbn siden med tabellen, tryk på '
     'bogmærket — tabellen kopieres som ren Markdown, klar til at sætte ind hvor som '
     'helst som rækker og kolonner.'),
    ('Hvorfor bliver min tabel én klat tekst i Noter?',
     'En almindelig kopiering tager ren tekst uden skilletegn, så iOS kan ikke se, hvor '
     'én celle slutter og den næste begynder. Kopierer du selve tabel-elementet som '
     'Markdown, bevares række- og kolonnegrænserne — og apps som Notion, Obsidian og '
     'Craft læser dem tilbage til en ægte struktur.'),
    ('Virker det i Chrome eller Firefox på iOS?',
     'Ja — alle browsere på iPhone og iPad bruger WebKit under motorhjelmen, og '
     'bookmarklet-metoden virker overalt hvor bogmærker kan redigeres. I de fleste iOS-'
     'browsere betyder det, at du tilføjer et bogmærke manuelt og erstatter adressen, '
     'præcis som i Safari.'),
    ('Kan jeg få tabellen ind i Excel eller Numbers på iPad?',
     'Kopiér tabellen med bookmarklet\'et, åbn Numbers eller Excel, tryk på den første '
     'målcelle og indsæt. Tabelindhold i udklipsholderen fordeles automatisk i celler — '
     'tjek kolonnerækkefølgen inden du sætter ind.'),
    ('Bliver noget sendt til en server?',
     'Nej. Bookmarklet\'et kører helt inde i din browser. Tabellen forlader ikke din '
     'enhed, før du selv sætter den ind der, hvor den skal bruges.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Kopiér en tabel fra en hjemmeside på iPhone & iPad (rækker og kolonner intakte)',
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
<title>Kopier en tabel fra en hjemmeside på iPhone &amp; iPad (Guide 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Kopier en tabel fra en hjemmeside på iPhone &amp; iPad">
<meta property="og:description" content="Få en webtabel ind i Noter, Numbers, Excel eller Notion på iOS med rækker og kolonner intakte. Gratis Safari-bookmarklet-metode.">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
<meta property="og:url" content="{URL}">
<meta name="twitter:card" content="summary_large_image">
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
  pre.cmd {{
    background:#0f172a; color:#e2e8f0; padding:14px 16px; border-radius:8px;
    overflow-x:auto; font-size:0.85rem; line-height:1.6; margin:0.8rem 0;
  }}
  pre.cmd code {{ font-family:'SF Mono','Monaco','Fira Code',monospace; }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">IOS &middot; SAFARI &middot; TABELLER</div>
    <h1>Kopier en tabel fra nettet<br>på iPhone &amp; iPad</h1>
    <p class="subtitle">Prissider, sammenligningstabeller, sportsstatistik — dataene ligger klar i Safari på telefonen. Men langtryk-kopiér giver dig én klump tekst, og iOS Safari har ingen extension-butik som på computer. Her er den gratis metode der bevarer hver række og kolonne.</p>
    <div class="hero-cta">
      <a href="#saadan" class="btn-primary">Se fremgangsmåden &rarr;</a>
      <a href="/clean-copy-bookmarklet" class="btn-secondary">Hent bookmarklet'et</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 4 minutters læsning</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Hvorfor det normalt mislykkes på iOS</h2>
    <p>Problemet er ikke din iPhone — det er det, der når ud til udklipsholderen.</p>
    <div class="problem-cards">
      <div class="card"><h3>👆 Langtryk vælger kun én celle</h3><p>iOS markerer den enkelte celle du trykker på — ikke hele tabellen, og at trække markeringen hen over en tabel er højest usikkert.</p></div>
      <div class="card"><h3>🧱 Ren tekst har ingen struktur</h3><p>Selv når du får valgt hele tabellen, ankommer den som tekst uden skilletegn. Apps kan ikke se, hvor én kolonne slutter og næste begynder.</p></div>
      <div class="card"><h3>🚫 Ingen desktop-udvidelser</h3><p>Safari på iOS understøtter web-udvidelser først fra iOS 15, og installationen er intet som de one-click-butikker på computer. De fleste gider ikke.</p></div>
    </div>
  </div>
</section>

<section class="products" id="saadan">
  <div class="container">
    <h2>Fremgangsmåden: et Safari-bookmarklet</h2>
    <p>Det gratis <a href="/clean-copy-bookmarklet" style="color:var(--color-accent);">Clean Copy-bookmarklet</a> konverterer præcis den tabel du peger på til ren Markdown — ingen installation, ingen konto, virker i Safari på enhver iPhone eller iPad.</p>

    <h3 style="margin-top:24px;">1. Opret bogmærket (én gang)</h3>
    <pre class="cmd"><code>Åbn Clean Copy-bookmarklet-siden i Safari.
Kopiér bookmarklet-linket.
Tryk Del → Tilføj bogmærke → gem det
(hvilken som helst side fungerer som pladsholder).</code></pre>

    <h3 style="margin-top:24px;">2. Redigér bogmærkets adresse</h3>
    <pre class="cmd"><code>Åbn Bogmærker, find det nye bogmærke,
tryk Redigér og erstat adressefeltet med
det kopierede bookmarklet-link. Gem.</code></pre>

    <h3 style="margin-top:24px;">3. Kopiér tabellen</h3>
    <pre class="cmd"><code>Åbn siden med tabellen i Safari.
Skriv bogmærkets navn i adresfeltet
og tryk på det. Vælg "Copy as Markdown".
Hele tabellen ligger nu på udklipsholderen.</code></pre>

    <h3 style="margin-top:24px;">4. Sæt ind hvor som helst</h3>
    <pre class="cmd"><code>Noter / Craft / Obsidian: indsæt som det er.
Numbers / Excel: tryk på første målcelle og indsæt —
hver værdi lander i sin egen celle.
Notion: indsæt i en databasevisning for rækker + egenskaber.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Strukturen overlever</h3><p>Clean Copy læser den ægte HTML-<code>&lt;table&gt;</code>, så hver <code>&lt;td&gt;</code> lander, hvor den hører hjemme.</p></div>
      <div class="card"><h3>🧹 Ingen junk-rækker</h3><p>Ingen annoncer, cookiebannere eller billedtekster — kun tabellen du pegede på.</p></div>
      <div class="card"><h3>🔐 Intet forlader din enhed</h3><p>Konverteringen kører inde i Safari selv. Ingen server, ingen upload — virker også bag login.</p></div>
    </div>
  </div>
</section>

<section class="products" id="muligheder">
  <div class="container">
    <h2>Dine muligheder sammenlignet</h2>
    <table class="compare">
      <thead>
        <tr><th>Metode</th><th>Bevarer struktur?</th><th>Bagefter</th></tr>
      </thead>
      <tbody>
        <tr><td>Langtryk + Kopiér</td><td>Nej</td><td>Vælger én celle; markering på tværs kollapser til tekst</td></tr>
        <tr><td>Skærmbillede + OCR</td><td>Efter oprydning</td><td>Talfejl er svære at spotte på små skærme</td></tr>
        <tr><td>"Åbn i Excel"-flows</td><td>Nogle gange</td><td>Kun hvor sitet selv tilbyder eksport</td></tr>
        <tr><td>Tredjeparts scanner-apps</td><td>Ofte</td><td>Betalte, opsætning pr. app, privatlivsspørgsmål</td></tr>
        <tr>
          <td><a href="/clean-copy-bookmarklet" style="color:var(--color-accent);">Clean Copy-bookmarklet — Copy as Markdown</a></td>
          <td>Ja</td>
          <td>Én manuel redigering af bogmærket</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy-bookmarklet" class="btn-primary">Hent det gratis bookmarklet &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/da/blog/kopier-tabel-til-excel" style="color:var(--color-accent);">Tabel fra hjemmeside til Excel</a> &middot; <a href="/blog/copy-table-website-to-notion" lang="en" style="color:var(--color-accent);">Table Into Notion</a> &middot; <a href="/da/blog/indsæt-uden-formatering-i-chrome" style="color:var(--color-accent);">Indsæt uden formatering</a> &middot; <a href="/da/blog/html-til-markdown-konverter" style="color:var(--color-accent);">HTML til Markdown-konverter</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Forside</a> &middot; <a href="/clean-copy-tool">Oprydningsværktøjet</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/copy-clean-guide">Guide-samling</a></p>
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

content = open(out).read()
assert '</pre-code>' not in content, 'stray tag found'

# --- validate JSON-LD ---
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print('JSON-LD block', i + 1, 'OK (@type=%s)' % parsed['@type'])

# --- validate internal link targets exist ---
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

# --- sitemap (idempotent) ---
sm = os.path.join(ROOT, 'site/sitemap.xml')
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = f'<url><loc>{URL}</loc><lastmod>{TODAY}</lastmod></url>'
    c = c.replace('</urlset>', f'{entry}</urlset>')
else:
    print('URL already in sitemap, skipping')
open(sm, 'w').write(c)
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

# --- cross-link from the EN post: Danish version note ---
en_path = os.path.join(SITE, 'blog/copy-table-website-iphone-ipad.html')
en = open(en_path).read()
if '/da/blog/' + SLUG not in en:
    old = '<footer style="padding:32px 24px;">\n  <p><a href="/"> &larr; Home</a>'
    assert old in en, 'EN footer anchor not found'
    new = ('<p style="text-align:center;"><a href="/da/blog/' + SLUG +
           '" lang="da">Dansk version af denne guide</a></p>\n' + old)
    en = en.replace(old, new, 1)
    open(en_path, 'w').write(en)
    print('EN post: DA cross-link added')
else:
    print('EN post already links the DA version')

# --- related line on the DA Excel post ---
da_xl = os.path.join(SITE, 'da/blog/kopier-tabel-til-excel.html')
x = open(da_xl).read()
if SLUG not in x:
    x = x.replace('</body>', '<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="' + URL + '" style="color:var(--color-accent);">Kopier en tabel på iPhone &amp; iPad</a></p></div>\n</body>', 1)
    open(da_xl, 'w').write(x)
    print('DA excel post: related line added')
else:
    print('DA excel post already linked')

print('\nDone:', out)
