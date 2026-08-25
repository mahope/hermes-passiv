#!/usr/bin/env python3
"""Iteration 258: To danske spejle af EN-posts (moenster fra iter255-257).

1. developer-text-tools             -> da/blog/7-gratis-dev-tekstvaerktoejer
2. table-alignment-html-to-markdown -> da/blog/tabeljustering-html-til-markdown
"""
import json, re, os, sys
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': '7-gratis-dev-tekstvaerktoejer',
        'en_slug': 'developer-text-tools',
        'title': '7 gratis tekstværktøjer til udviklere — uden login, 100 % i browseren',
        'h1': '7 gratis tekstværktøjer<br>til udviklere',
        'desc': ('Ordoptæller, JSON-formatter, tekst-diff, case-konverter, Base64, '
                 'URL-encoder og hash-generator. Alle kører udelukkende i din '
                 'browser — ingen upload, ingen konto, ingen grænser.'),
        'og_desc': ('Syv gratis browserbaserede værktøjer til udviklere: ordtælling, '
                    'JSON, diff, case, Base64, URL og hash. Alt kører client-side.'),
        'badge': 'UDVIKLERVÆRKTØJ &middot; GRATIS',
        'subtitle': ('De fleste gratis online-værktøjer sender dine data til en server. '
                     'Det er et problem, når data er følsomme — API-nøgler, config-filer, '
                     'private strenge. De syv værktøjer her deler ét princip: alt kører '
                     'i din browser, intet forlader din maskine.'),
        'cta1': '<a href="/word-counter" class="btn-primary">Prøv det første værktøj &rarr;</a>',
        'cta2': '<a href="#vaerktoejerne" class="btn-secondary">Se alle syv</a>',
        'tool_url': '/json-formatter',
        'tool_label': 'Åbn JSON-formatteren',
        'faq': [
            ("Hvor finder jeg gratis udviklerværktøjer uden tilmelding?",
             "Hermes Passiv tilbyder syv gratis browserbaserede værktøjer: ordtæller, "
             "JSON-formatter og -validator, tekst-diff, case-konverter, Base64-"
             "encoder/decoder, URL-encoder/decoder og hash-generator. Hvert værktøj "
             "kører 100 % client-side — intet uploades."),
            ("Er det sikkert at bruge dem med følsomme data?",
             "Ja. Alle værktøjer kører udelukkende i din browser. Tekst sendes aldrig "
             "til en server, så du kan trygt bruge dem med API-nøgler, config-filer, "
             "adgangskoder (til hashing) og andre følsomme strenge."),
            ("Skal jeg oprette en konto?",
             "Nej. Ingen konto, ingen e-mail, ingen tilmelding. Alle værktøjer er "
             "gratis og ubegrænsede — klik på linket og begynd at bruge dem med det samme."),
            ("Virker værktøjerne offline?",
             "Ja, når siden er loadet. Hvert værktøj er selvstændig HTML med inline "
             "JavaScript — du kan gemme siden og fortsætte offline."),
        ],
        'body': '''
<section class="products" id="vaerktoejerne">
  <div class="container">
    <h2>De syv værktøjer</h2>
    <div class="problem-cards">
      <div class="card"><h3><a href="/word-counter">1. Ordoptæller</a></h3>
      <p>Ord, tegn, sætninger, afsnit og stavelser. Estimeret læsetid og Flesch-
      læsbarhedsscore. Det grundlæggende skriveværktøj til blogindlæg, copy og
      dokumentation.</p></div>
      <div class="card"><h3><a href="/json-formatter">2. JSON-formatter &amp; validator</a></h3>
      <p>Pæn-udskriv, minify og valider JSON med præcise fejlmeddelelser med linje
      og kolonne. Fang syntaksfejl før de når din API.</p></div>
      <div class="card"><h3><a href="/text-diff">3. Tekst-diff</a></h3>
      <p>Sammenlign to tekster og se forskellene linje for linje. Nyttigt til
      ændringslogge, konfigurationer og gennemgang af genereret indhold.</p></div>
      <div class="card"><h3><a href="/case-converter">4. Case-konverter</a></h3>
      <p>camelCase, snake_case, kebab-case, UPPER, Title — konvertér mellem alle
      konventionerne på ét klik. Stop med at rette store bogstaver i hånden.</p></div>
      <div class="card"><h3><a href="/base64-encoder-decoder">5. Base64 encoder/decoder</a></h3>
      <p>Kod og afkod Base64 lokalt — også nyttigt til JWT-inspektion, hvor du ikke
      vil sende tokenet til et fremmed site.</p></div>
      <div class="card"><h3><a href="/url-encoder-decoder">6. URL-encoder/decoder</a></h3>
      <p>Percent-encoding af query-parametre og stier — og afkodning af de
      kryptiske links du får tilsendt.</p></div>
      <div class="card"><h3><a href="/hash-generator">7. Hash-generator</a></h3>
      <p>SHA-256, SHA-1 og MD5 direkte i browseren. Verificér checksums og byg
      fingerprint-lister uden at indsættet forlader din maskine.</p></div>
    </div>
    <div style="text-align:center;margin-top:20px;">
      <a href="/free-tools" class="btn-primary">Se alle gratis værktøjer &rarr;</a>
    </div>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Hvorfor client-side?</h2>
    <ol>
      <li><strong>Privatliv:</strong> følsomme strenge (nøgler, tokens) sendes
      aldrig over netværket.</li>
      <li><strong>Hastighed:</strong> ingen upload-ventetid — resultatet vises,
      mens du taster.</li>
      <li><strong>Ingen begrænsninger:</strong> ingen kvoter, ingen paywall, ingen
      "opret konto for at se resultatet".</li>
    </ol>
    <p>Læs også:
    <a href="/da/blog/html-til-markdown-konverter">HTML til markdown-konverteren</a>,
    <a href="/da/blog/url-til-markdown-konverter">URL til markdown</a> og
    <a href="/da/blog/ren-tekst-fra-hjemmeside">ren tekst fra en hjemmeside</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/html-til-markdown-konverter" lang="da">HTML til markdown</a> &middot; '
                    '<a href="/da/blog/kopier-som-markdown-udvidelse" lang="da">Kopiér som markdown</a> &middot; '
                    '<a href="/da/blog/ren-tekst-fra-hjemmeside" lang="da">Ren tekst fra hjemmeside</a>'),
    },
    {
        'slug': 'tabeljustering-html-til-markdown',
        'en_slug': 'table-alignment-html-to-markdown',
        'title': 'Bevar kolonnejustering når HTML-tabeller bliver til markdown (2026)',
        'h1': 'Kolonnejustering<br>i markdown-tabeller',
        'desc': ('Markdown-tabeller kan udtrykke venstre-, højre- og centerjustering — '
                 'men de fleste konvertere smider informationen væk. Sådan bærer du den '
                 'med gennem konverteringen.'),
        'og_desc': ('Kolonnestyring i HTML går tabt i de fleste markdown-konverteringer. '
                    'Sådan bevarer du venstre/højre/center-justering korrekt.'),
        'badge': 'RENGØR TEKST &middot; MARKDOWN',
        'subtitle': ('En HTML-tabel med align="right" på tal-kolonnerne ser forkert ud i '
                     'markdown efter konvertering: alt bliver venstrejusteret. Markdown '
                     'understøtter faktisk justering via kolonneoverskrifternes colons — '
                     'men kun hvis konvertereren skriver dem rigtigt.'),
        'cta1': '<a href="/clean-copy-tool" class="btn-primary">Prøv konverteren &rarr;</a>',
        'cta2': '<a href="#syntaks" class="btn-secondary">Se syntaksen</a>',
        'tool_url': '/clean-copy-tool',
        'tool_label': 'Konvertér en tabel nu',
        'faq': [
            ("Hvordan justerer man kolonner i en markdown-tabel?",
             "Med colons i separatorlinjen under overskrifterne: |:---| venstrejusterer, "
             "|---:| højrejusterer og |:---:| centrerer kolonnen. Uden colons bliver "
             "kolonnen venstrejusteret som standard."),
            ("Hvorfor mister mine tal-kolonner deres justering?",
             "Fordi de fleste konverterere skriver separatorlinjen som |---|---| uden at "
             "læse HTML'ens align-attribut. Clean Copy aflæser alignment fra CSS og "
             "attributter og skriver colons korrekt."),
            ("Understøtter GitHub colons i tabeller?",
             "Ja. GitHub Flavored Markdown, CommonMark-udvidelser, Notion og Obsidian "
             "respekterer alle justerings-colons. Ældre parseverktøjer ignorerer dem "
             "nogle gange, men tabellen vises stadig korrekt."),
            ("Kan jeg se justeringen i selve markdown-filen?",
             "Ja — det står i kildekoden. En højrejusteret kolonne har |---:| i "
             "separatorlinjen, så justeringen er dokumenteret i filen og ikke kun i "
             "renderen."),
        ],
        'body': '''
<section class="problem" id="syntaks">
  <div class="container">
    <h2>Syntaksen: colons i separatorlinjen</h2>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">| Vare     | Antal | Pris     |
|:---------|------:|:--------:|
| Tastatur |     2 | 399,00   |
| Mus      |     1 | 249,50   |</pre>
    <p><code>|:---|</code> = venstre &middot; <code>|---:|</code> = højre &middot;
    <code>|:---:|</code> = centreret. Tal-kolonner læses bedst højrejusteret —
    cifrene skal stå under hinanden.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy-tool" class="btn-primary">Test med din egen tabel &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan bevarer Clean Copy justeringen</h2>
    <ol>
      <li>Aflæser <code>align</code>-attributten og CSS <code>text-align</code> på
      hver celle i HTML-tabellen.</li>
      <li>Oversætter til colons i separatorlinjen — højrejusterede celler giver
      <code>---:</code>, centrerede giver <code>:--:</code>.</li>
      <li>Resultatet renderes med samme justering som originalen i GitHub, Notion,
      Obsidian og alle GFM-kompatible renderere.</li>
    </ol>
    <p>Læs videre:
    <a href="/da/blog/html-til-markdown-konverter">den komplette HTML-til-markdown-guide</a>,
    <a href="/da/blog/kopier-tabel-hjemmeside-til-notion">tabeller ind i Notion</a> og
    <a href="/da/blog/kopier-tabel-hjemmeside-til-airtable">tabeller ind i Airtable</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/html-til-markdown-konverter" lang="da">HTML til markdown</a> &middot; '
                    '<a href="/da/blog/kopier-tabel-hjemmeside-til-notion" lang="da">Tabeller til Notion</a> &middot; '
                    '<a href="/da/blog/kopier-tabel-hjemmeside-til-airtable" lang="da">Tabeller til Airtable</a>'),
    },
]


def build_page(p):
    url = f'{BASE}/da/blog/{p["slug"]}'
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': p['title'], 'description': p['desc'],
        'url': url,
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
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
<link rel="alternate" hreflang="en" href="{BASE}/blog/{p['en_slug']}">
<link rel="alternate" hreflang="da" href="{url}">
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
  <p><a href="/da">Forside</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/scan-da">Scanner</a> &middot; <a href="/da/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.href;if(h&&h.indexOf('chromewebstore.google.com')>-1){{try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'store-click'}})],{{type:'application/json'}}));}}catch(e){{}}}}}},true);}}catch(e){{}}}})();
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
           f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(path, 'w').write(c)
    print(f'sitemap: added {slug}')


def add_hreflang_pair(en_slug, da_path):
    en_f = f'{SITE}/blog/{en_slug}.html'
    da_url = f'{BASE}/{da_path}'
    en = open(en_f).read()
    if f'hreflang="da" href="{da_url}"' not in en:
        # remove any stale x-default-only duplicates first is not needed; just append pair
        en = en.replace('</head>',
                        f'<link rel="alternate" hreflang="en" href="{BASE}/blog/{en_slug}">\n'
                        f'<link rel="alternate" hreflang="da" href="{da_url}">\n</head>')
        print(f'{en_slug}: hreflang pair added')
    else:
        print(f'{en_slug}: hreflang already present')
    if 'Dansk version af denne guide' not in en and f'href="/{da_path}"' not in en:
        done = False
        for anchor in ('<footer style="padding:32px 24px;">', '<footer class="site-footer;">',
                       '<footer'):
            if anchor in en:
                en = en.replace(anchor,
                    f'<p><a href="/{da_path}" lang="da">Dansk version af denne guide</a></p>\n{anchor}', 1)
                done = True
                break
        if done:
            print(f'{en_slug}: DA cross-link added')
        else:
            print(f'{en_slug}: WARNING no footer anchor found')
    open(en_f, 'w').write(en)


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
    outs, en_files = [], []
    for p in PAGES:
        out = f'{SITE}/da/blog/{p["slug"]}.html'
        page = build_page(p)
        with open(out, 'w') as f:
            f.write(page)
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
        for b in blocks:
            d = json.loads(b)
            assert d['@context'] == 'https://schema.org', d['@context']
        print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')
        update_sitemap(p['slug'])
        add_hreflang_pair(p['en_slug'], f'da/blog/{p["slug"]}')
        outs.append(out)
        en_files.append(f'{SITE}/blog/{p["en_slug"]}.html')

    broken = check_links(outs + en_files)
    if broken:
        print('BROKEN INTERNAL LINKS:')
        for path, link in broken:
            print(f'  {path} -> {link}')
        sys.exit(1)
    print('Internal link check: OK')


if __name__ == '__main__':
    main()
