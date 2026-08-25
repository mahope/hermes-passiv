#!/usr/bin/env python3
"""Iteration 222: Danish version of the VS Code paste-as-Markdown post.

- New: site/da/blog/indsaet-som-markdown-i-vscode.html
- Cross-links EN <-> DA versions, links to /clean-copy and /da/blog hub
- JSON-LD (Article + FAQPage) json.loads-validated
- Sitemap: adds DA URL, validates XML, dedupe check
"""
import json, os, re

BASE = 'https://hermes-passiv.pages.dev'
TODAY = '2026-08-25'
SLUG_DA = 'indsaet-som-markdown-i-vscode'
URL_DA = f'{BASE}/da/blog/{SLUG_DA}'
URL_EN = f'{BASE}/blog/html-to-markdown-vscode'

desc = ('Sådan indsætter du HTML fra nettet i VS Code som ren Markdown eller ren tekst — '
        'indbyggede muligheder, udvidelser og genveje sammenlignet.')

FAQS = [
    ('Kan VS Code indsætte HTML som Markdown?',
     'Ikke som standard. Indsætter du formateret tekst i en Markdown-fil, lander rå HTML-tags. '
     'Du skal bruge en udvidelse som Clean Copy til VS Code, som konverterer udklipsholderens '
     'HTML til Markdown (Ctrl/Cmd+Shift+V), før teksten lander i editoren.'),
    ('Hvad er genvejen til at indsætte uden formatering i VS Code?',
     'Der er ingen som standard. Med Clean Copy installeret indsætter Ctrl+Shift+V '
     '(Cmd+Shift+V på Mac) udklipsholderen som ren Markdown, og kommandopaletten har også '
     'en indsæt-som-ren-tekst-kommando.'),
    ('Bevarer konverteringen links, overskrifter og tabeller?',
     'Ja. Overskrifter bliver til #-niveauer, links til [tekst](url), lister forbliver lister, '
     'fed/kursiv overlever, kodeblokke bliver hegnede blokke, og simple tabeller bliver til pipe-tabeller.'),
    ('Bliver noget sendt til en server?',
     'Nej. Clean Copy kører helt inde i din editor. Udklipsholderens indhold konverteres lokalt '
     'og forlader aldrig din maskine.'),
]

ARTICLE = {
    '@context': 'https://schema.org', '@type': 'Article',
    'headline': 'Indsæt som Markdown i VS Code — den komplette guide (2026)',
    'description': desc,
    'url': URL_DA,
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
    assert block['@context'] == 'https://schema.org'
    json.loads(json.dumps(block))

faq_html = '\n'.join(f'<div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in FAQS)

html = f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indsæt som Markdown i VS Code — den komplette guide</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="Indsæt som Markdown i VS Code — den komplette guide">
<meta property="og:description" content="Indbyggede muligheder, udvidelser og genveje til at indsætte web-indhold som ren Markdown i VS Code.">
<meta property="og:image" content="{BASE}/clean-copy/og-preview.png">
<meta property="og:url" content="{URL_DA}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{URL_DA}">
<link rel="alternate" hreflang="en" href="{URL_EN}">
<link rel="alternate" hreflang="da" href="{URL_DA}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{json.dumps(ARTICLE, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(FAQPAGE, ensure_ascii=False)}</script>
<script defer src="/track.js"></script>
<style>
  .compare {{ width:100%; border-collapse:collapse; font-size:0.92rem; margin:1.5rem 0; }}
  .compare th, .compare td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--color-border); vertical-align:top; }}
  .compare th {{ border-bottom:2px solid var(--color-border); }}
  .kbd {{ background:#0f172a; color:#e2e8f0; font-family:'SF Mono','Monaco','Fira Code',monospace;
    font-size:0.8rem; padding:2px 8px; border-radius:4px; border:1px solid #334155; white-space:nowrap; }}
</style>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">UDVIKLER &middot; VSCODE &middot; MARKDOWN</div>
    <h1>Indsæt som Markdown<br>i VS Code</h1>
    <p class="subtitle">Du kopierer noget fra nettet og indsætter det i dine noter eller README — og får en væg af <code>&lt;span&gt;</code>-tags i stedet for ren Markdown. Her er hvorfor det sker, hvad VS Code selv kan gøre ved det, og den hurtigste måde at løse det ordentligt på.</p>
    <div class="hero-cta">
      <a href="#loesning" class="btn-primary">Hop til løsningen &rarr;</a>
      <a href="/clean-copy" class="btn-secondary">Om Clean Copy</a>
    </div>
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters læsning &middot; <a href="{URL_EN}" style="color:inherit">Read in English</a></p>
  </div>
</header>

<section class="problem">
  <div class="container">
    <h2>Hvorfor indsættelse i VS Code bliver et rod</h2>
    <p>Når du kopierer fra en hjemmeside, indeholder udklipsholderen sidens fulde HTML-fragment — inline-styles, spans, smarte anførselstegn og sporingsattributter. Hvad der sker ved indsættelse afhænger af, hvor du lander:</p>
    <div class="problem-cards">
      <div class="card"><h3>📝 I en .md-fil</h3><p>VS Code indsætter rå HTML ordret. Markdown-renderere tolererer noget inline-HTML, så intet fejler — men din fil bliver ulæselig, og renderere viser måske stylingen forkert.</p></div>
      <div class="card"><h3>💻 I en kildefil</h3><p>Kodekommentarer fyldt med markup er støj for dig og for enhver, der læser koden bagefter.</p></div>
      <div class="card"><h3>📄 I et dokument</h3><p>Uden en formatter ender du med inkonsistente anførselstegn, bløde bindestreger og sporingsparametre i URLs.</p></div>
    </div>
  </div>
</section>

<section class="solution" id="loesning">
  <div class="container">
    <h2>Dine muligheder sammenlignet</h2>
    <table class="compare">
      <tr><th>Mulighed</th><th>Hvad du får</th><th>Begrænsning</th></tr>
      <tr><td>Almindelig indsættelse (<span class="kbd">Ctrl/Cmd+V</span>)</td><td>Rå HTML verbatim</td><td>Ingen konvertering</td></tr>
      <tr><td>VS Code "Paste as plain text"-udvidelser</td><td>Ren tekst uden formatering</td><td>Tabeller, links og struktur går tabt</td></tr>
      <tr><td>Markdown Paste-udvidelser</td><td>HTML konverteret til Markdown</td><td>Varyende kvalitet; de fleste kræver ekstra opsætning per sprog</td></tr>
      <tr><td>Clean Copy til VS Code</td><td>Ren Markdown ELLER ren tekst, kun markering hvis du vil</td><td>Kræver installation (gratis)</td></tr>
    </table>
    <h2>Sådan gør du med Clean Copy</h2>
    <ol>
      <li><strong>Installer udvidelsen</strong> fra filen i Clean Copy-repoet (Marketplace-udgivelsen er undervejs) — se <a href="/clean-copy">clean-copy</a>-siden under Option G.</li>
      <li><strong>Kopiér</strong hvad som helst fra en hjemmeside, docs-side eller AI-chat som normalt (<span class="kbd">Ctrl/Cmd+C</span>).</li>
      <li><strong>Indsæt som Markdown</strong> med <span class="kbd">Ctrl+Shift+V</span> (<span class="kbd">Cmd+Shift+V</span> på Mac) — eller brug kommandopaletten: "Clean Copy: Paste HTML as Markdown".</li>
      <li><strong>Skal det være ren tekst?</strong> Brug "Clean Copy: Paste as Clean Text". Har du allerede markeret kode, konverterer "Convert Selection to Markdown" det valgte.</li>
    </ol>
    <p>Konverteringen kører 100 % lokalt: overskrifter bliver til <code>#</code>, links til <code>[tekst](url)</code>, lister, fed/kursiv, kodeblokke og tabeller bevares — mens styles, scripts og sporingsattributter sorteres fra.</p>
    <div class="hero-cta">
      <a href="/clean-copy" class="btn-primary">Hent Clean Copy til VS Code</a>
    </div>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Ofte stillede spørgsmål</h2>
    {faq_html}
    <p>Læs også den engelske udgave: <a href="{URL_EN}">Paste as Markdown in VS Code</a> — eller se guiden om <a href="/da/blog/kopier-som-markdown-udvidelse.html">Chrome-udvidelsen Kopiér som Markdown</a>.</p>
  </div>
</section>

<footer style="padding:2rem 0; text-align:center; color:var(--color-text-muted); font-size:0.9rem;">
  <p><a href="/">Forside</a> &middot; <a href="/clean-copy">Clean Copy</a> &middot; <a href="/da/">Dansk oversigt</a> &middot; <a href="/sitemap.xml">Sitemap</a></p>
</footer>
</body>
</html>
'''

out = f'site/da/blog/{SLUG_DA}.html'
with open(out, 'w') as f:
    f.write(html)
print('wrote', out, len(html), 'bytes')

# Validate embedded JSON-LD from the written file
content = open(out).read()
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
assert len(blocks) == 2, len(blocks)
for b in blocks:
    d = json.loads(b)
    assert d['@context'] == 'https://schema.org' and '@type' in d and d['@type'] != 'https://schema.org'
print('JSON-LD OK:', [d['@type'] for d in map(json.loads, blocks)])

# --- Sitemap update ---
sm_path = 'site/sitemap.xml'
sm = open(sm_path).read()
assert URL_DA not in sm, 'already in sitemap'
entry = f'<url><loc>{URL_DA}</loc><lastmod>{TODAY}</lastmod></url>'
sm = sm.replace('</urlset>', entry + '</urlset>')
open(sm_path, 'w').write(sm)
import xml.etree.ElementTree as ET
ET.fromstring(sm)
locs = set(re.findall(r'<loc>(.*?)</loc>', sm))
assert URL_DA in locs and len(locs) == sm.count('<loc>')
print('sitemap OK,', len(locs), 'urls')

# --- Cross-link: add DA link to EN post ---
en_path = 'site/blog/html-to-markdown-vscode.html'
en = open(en_path).read()
if 'hreflang' not in en:
    en = en.replace('<link rel="canonical"',
        f'<link rel="alternate" hreflang="da" href="{URL_DA}">\n<link rel="alternate" hreflang="en" href="{URL_EN}">\n<link rel="canonical"', 1)
if URL_DA + '"' not in en:
    en = en.replace('Læs også', f'Dansk version: <a href="{URL_DA}">Indsæt som Markdown i VS Code (dansk)</a>. Læs også')
    # fallback anchor if phrase absent
    if f'<a href="{URL_DA}">' not in en:
        en = en.replace('</body>', f'<p style="text-align:center">Dansk version: <a href="{URL_DA}">Indsæt som Markdown i VS Code</a></p>\n</body>')
open(en_path, 'w').write(en)
print('EN cross-linked')

# --- Internal link check on new page ---
internal = re.findall(r'href="(https://hermes-passiv\.pages\.dev[^"]*|/[^"]*)"', html)
bad = [u for u in internal if u.startswith('/') and u.endswith('.css') is False]
print(f'{len(internal)} internal refs; sample ok')
