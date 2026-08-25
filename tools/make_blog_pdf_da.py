#!/usr/bin/env python3
"""Iteration 233: DA blogpost — kopier en tabel fra en PDF (og indsæt i Excel).

Ny post: site/blog/kopier-tabel-fra-pdf.html
- Samme house-template som resten af serien (hero, steps, compare, FAQ)
- Article + FAQPage JSON-LD, valideret foer og efter skrivning
- Sitemap opdateres kun hvis URL'en ikke allerede findes (idempotent)
- Krydslinks: til Excel/Sheets/Notion-soesterposter + reciprokke links fra
  Excel-posten og Sheets-posten.
"""
import json, os, re

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
URL = f'{BASE}/blog/kopier-tabel-fra-pdf'

desc = ('Kopier en tabel fra en PDF og indsaet den i Excel eller Google Sheets '
        'med roekker og kolonner intakte — uden OCR-fejl og uden at skrive alt ind igen.')

FAQS = [
    ('Hvorfor bliver tabellen rod, naar jeg kopierer direkte fra en PDF?',
     'En PDF gemmer tekst som positionerede blokke, ikke som en tabel. Naar du '
     'markerer og kopierer, faar du ofte hver kolonne som sin egen linje — al '
     'indhold fra roekke 1, derefter alt fra roekke 2. Derfor skal teksten '
     'ombygges til en rigtig tabel, foer den kan indsaettes.'),
    ('Kan jeg undgaa at bruge OCR?',
     'Ja i de fleste tilfaelde. Hvis PDF-en er genereret digitalt (fx fra Excel '
     'eller et rapportvaerktoej), staar teksten allerede i filen. Clean Copy '
     'genopbygger tabellen ud fra sidens struktur i stedet for at laese pixels.'),
    ('Hvordan goer jeg med en scannet PDF?',
     'Scannede PDF\'er indeholder billeder, ikke tekst — der kraeves OCR '
     '(fx Adobe Acrobat eller et online-OCR). Tjek altid tallene bagefter; '
     'OCR fejler typisk paa netop cifre.'),
    ('Virker det ogsaa med Google Sheets?',
     'Ja. Indholdet paa udklipsholderen er almindelig tabelstruktur, saa den '
     'indsaettes korrekt i Google Sheets, Excel, Numbers og LibreOffice Calc.'),
    ('Kommer mine data ud af browseren?',
     'Nej. Clean Copy koerer helt lokalt i din browser. Tabellen forlader ikke '
     'din maskine, foer du selv indsætter den et sted.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Sådan kopierer du en tabel fra en PDF ind i Excel (kolonner intakte)',
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
<title>Kopiér en tabel fra en PDF ind i Excel (guide 2026)</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Kopiér en tabel fra en PDF ind i Excel">
<meta property="og:description" content="Få tabellen fra PDF'en over i Excel med rækker og kolonner intakte — uden OCR-fejl og uden at skrive alt ind manuelt.">
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
    <div class="badge">PDF &middot; EXCEL &middot; TABELLER</div>
    <h1>Kopiér en tabel fra en PDF<br>ind i Excel</h1>
    <p class="subtitle">Årsrapporter, kvartalsregnskaber, offentlige statistikker — tabellerne ligger låst inde i PDF'er. Markér og kopier giver næsten altid én lang tekstklump. Her er vejen rundt, hvor kolonnerne lander der, hvor de skal.</p>
    <div class="hero-cta">
      <a href="#how" class="btn-primary">Vis mig fremgangsmåden &rarr;</a>
      <a href="/clean-copy" class="btn-secondary">Om Clean Copy</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 4 minutters læsning</p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Hvorfor de sædvanlige metoder fejler</h2>
    <p>Problemet er ikke Excel — det er udklipsholderen. En PDF har ingen rigtig tabelstruktur at give videre.</p>
    <div class="problem-cards">
      <div class="card"><h3>📋 Direkte kopiering ødelægger strukturen</h3><p>PDF-visningen gendanner teksten i læserækkefølge, ikke tabelrækkefølge. Resultatet er typisk alle værdierne kolonnevis stablet i én celle pr. linje.</p></div>
      <div class="card"><h3>📸 Skærmbillede + OCR = talfejl</h3><p>OCR læser pixels, og netop cifre rammer den oftest. En enkelt forkert digit i et regnskab er værre end ingen data.</p></div>
      <div class="card"><h3>⌨️ Manuelt genindtastning holder ikke</h3><p>Til tre rækker, ja. Til en 40-siders årsrapport med tyve tabeller, nej.</p></div>
    </div>
  </div>
</section>

<section class="products" id="how">
  <div class="container">
    <h2>Fremgangsmåden: åbn PDF'en i browseren</h2>
    <p>Når en PDF vises i Chrome eller Firefox, står teksten som rigtig tekst på siden — og der kan <a href="/clean-copy" style="color:var(--color-accent);">Clean Copy</a>-udvidelsen arbejde med den. Udvidelsen har en dedikeret Kopiér tabel-tilstand, der finder tabellen under markøren og lægger ægte tabelstruktur på udklipsholderen.</p>

    <h3 style="margin-top:24px;">1. Installér</h3>
    <pre class="cmd"><code>Chrome Web Store eller Firefox Add-ons — søg på "Clean Copy", installér, færdig.</code></pre>

    <h3 style="margin-top:24px;">2. Åbn PDF'en i browseren</h3>
    <pre class="cmd"><code>Træk PDF-filen ind i et Chrome- eller Firefox-vindue,
og scroll hen til tabellen.</code></pre>

    <h3 style="margin-top:24px;">3. Kopiér tabellen</h3>
    <pre class="cmd"><code>Klik et vilkårligt sted i tabellen, klik på
Clean Copy-ikonet og vælg "Copy table".</code></pre>

    <h3 style="margin-top:24px;">4. Indsæt i Excel</h3>
    <pre class="cmd"><code>Klik på celle A1 og tryk Ctrl+V (Cmd+V på Mac).
Hver værdi lander i sin egen celle — overskrifter inkluderet.</code></pre>

    <div class="problem-cards">
      <div class="card"><h3>✅ Celler forbliver celler</h3><p>Udklipsholderen indeholder rigtig tabelstruktur, så Excel mapper hver værdi korrekt.</p></div>
      <div class="card"><h3>🧹 Intet rod med i købet</h3><p>Ingen sidehoveder, sidefodnummer eller løbende tekst — kun den tabel, du pegede på.</p></div>
      <div class="card"><h3>🔁 Fungerer også andre steder</h3><p>Samme indsætning virker i Google Sheets, Numbers og LibreOffice Calc.</p></div>
    </div>
  </div>
</section>

<section class="products" id="options">
  <div class="container">
    <h2>Dine muligheder sammenlignet</h2>
    <table class="compare">
      <thead>
        <tr><th>Metode</th><th>Bevarer struktur?</th><th>Hage</th></tr>
      </thead>
      <tbody>
        <tr><td>Markér + kopiér fra PDF-læser</td><td>Sjældent</td><td>Tekst kommer i læserækkefølge, kolonner kollapser</td></tr>
        <tr><td>Skærmbillede + OCR</td><td>Efter oprydning</td><td>Talfejl er svære at spotte</td></tr>
        <tr><td>Acrobat "Eksportér til regneark"</td><td>Ja</td><td>Kræver betalt abonnement; langsommelig ved mange tabeller</td></tr>
        <tr><td>Excel-datafanen "Fra PDF"</td><td>Ja</td><td>Kræver Microsoft 365; sløver ved komplekse layout</td></tr>
        <tr>
          <td><a href="/clean-copy" style="color:var(--color-accent);">Clean Copy — Kopiér tabel</a></td>
          <td>Ja</td>
          <td>Gratis browserudvidelse krævet; PDF'en åbnes i browseren</td>
        </tr>
      </tbody>
    </table>
    <p>Har du Microsoft 365 eller Acrobat, kan de indbyggede eksportfunktioner være fine til enkelte store tabeller. Til hurtige kopieringer — og til gratis — er browservejen den enkleste.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    <div class="problem-cards">
      {faq_html}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/clean-copy" class="btn-primary">Hent Clean Copy gratis &rarr;</a>
    </div>
  </div>
</section>

<div style="text-align:center;margin-top:16px;"><p>Relateret: <a href="/blog/copy-table-from-website-to-excel" style="color:var(--color-accent);">Kopiér en tabel fra en hjemmeside til Excel</a> &middot; <a href="/blog/copy-table-website-to-google-sheets" style="color:var(--color-accent);">Tabel fra hjemmeside til Google Sheets (EN)</a> &middot; <a href="/blog/kopier-tabel-hjemmeside-til-excel" style="color:var(--color-accent);">Tabel fra hjemmeside til Excel (DA)</a></p></div>
<footer style="padding:32px 24px;">
  <p><a href="/"> &larr; Forside</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/free-tools">Gratis vaerktoejer</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>
'''

out = '/Users/madsholstjensen/hermes-passiv/site/blog/kopier-tabel-fra-pdf.html'
with open(out, 'w') as f:
    f.write(html)

# --- validate JSON-LD ---
content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, f'expected 2 JSON-LD blocks, got {len(blocks)}'
for i, b in enumerate(blocks):
    parsed = json.loads(b)
    assert parsed['@context'] == 'https://schema.org', parsed['@context']
    print(f'JSON-LD block {i+1}: OK (@type={parsed["@type"]})')

# --- validate internal link targets exist ---
for ref in [
    'site/clean-copy.html',
    'site/blog/copy-table-from-website-to-excel.html',
    'site/blog/copy-table-website-to-google-sheets.html',
    'site/blog/kopier-tabel-hjemmeside-til-excel.html',
]:
    p = os.path.join('/Users/madsholstjensen/hermes-passiv', ref)
    assert os.path.exists(p), p
print('All internal link targets exist')

# --- sitemap (idempotent) ---
sm = '/Users/madsholstjensen/hermes-passiv/site/sitemap.xml'
c = open(sm).read()
if URL + '</loc>' not in c:
    entry = f'<url><loc>{URL}</loc><lastmod>{TODAY}</lastmod></url>'
    c = c.replace('</urlset>', f'{entry}</urlset>')
    open(sm, 'w').write(c)
else:
    print('URL already in sitemap, skipping')
import xml.dom.minidom
xml.dom.minidom.parse(sm)
print('sitemap parses as XML,', c.count('<loc'), 'urls')

# --- reciprocal cross-links ---
def add_related(path, slug, label):
    x = open(path).read()
    if slug in x:
        return False
    x = x.replace('</body>', f'<div style="text-align:center;margin-top:16px;"><p>Related: <a href="{URL}" style="color:var(--color-accent);">{label}</a></p></div>\n</body>', 1)
    open(path, 'w').write(x)
    return True

for path, label in [
    ('site/blog/copy-table-from-website-to-excel.html', 'Kopier en tabel fra en PDF til Excel'),
    ('site/blog/copy-table-website-to-google-sheets.html', 'Copy a Table From a PDF Into Excel'),
    ('site/blog/copy-table-website-to-notion.html', 'Copy a Table From a PDF Into Excel'),
]:
    full = os.path.join('/Users/madsholstjensen/hermes-passiv', path)
    changed = add_related(full, 'kopier-tabel-fra-pdf', label)
    print(f'{path}: {"cross-linked" if changed else "already linked"}')

print('\nDone:', out)
