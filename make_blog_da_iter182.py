#!/usr/bin/env python3
"""Iteration 182: Danish blog post - how to test your release zip before shipping.

Practical QA guide (checklist + copy-paste commands) that surfaces Clean Copy.
Reuses the stable iter181 page pattern.
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGE = {
    'slug': 'test-din-zip-foer-release',
    'title': 'Sådan tester du din zip-fil, før du udgiver den',
    'h1': 'Test Din Zip-Fil,<br>Før Du Trykker Udgiv',
    'desc': ('En praktisk tjekliste: sådan åbner og verificerer du din udgivelses-zip, '
             'før brugerne ser den. Syv tjek, tre kommandoer du kan kopiere, og den '
             'ene parity-test der fanger gamle filer i pakken.'),
    'og_desc': ('Din testsuite tester kilden. Brugerne downloader zippen. Her er syv '
                'tjek der sikrer, at det er de samme filer — plus kommandoerne du kan '
                'kopiere direkte ind i dit bygge-script.'),
    'badge': 'QA &middot; RELEASE &middot; TJEKLISTE',
    'subtitle': ('Koden er testet, buildet er grønt — men har du faktisk set indholdet '
                 'af den zip-fil, brugerne downloader? Her er en tjekliste med syv '
                 'tjek og de præcise kommandoer, du kan køre på 30 sekunder.'),
    'cta1': ('<a href="/da/blog/release-integrity-hvad-er-det" class="btn-primary">'
             'Læs casen bag tjeklisten &rarr;</a>'),
    'cta2': '<a href="#tjekliste" class="btn-secondary">Spring til tjeklisten</a>',
    'tool_url': '/da/blog/indsæt-uden-formatering-i-chrome',
    'tool_label': 'Prøv Clean Copy gratis',
    'faq': [
        ("Hvorfor skal jeg teste zip-filen, når mine tests allerede er grønne?",
         "Fordi dine tests kører mod kildekoden — ikke mod artefaktet. Zip-filen er "
         "bygget af et separat trin, som kan pakke ældre filer, glemme nye eller "
         "medtage skrald. En test kan kun garantere det, den faktisk indlæser."),
        ("Hvad er en parity-test?",
         "En test der sammenligner filen i zippen med dens kilde byte-for-byte. Hvis "
         "de adskiller sig, fejler buildet. Det fanger den klassiske fejl hvor samme "
         "kode vedligeholdes to steder, og kopien bliver glemt ved en udgivelse."),
        ("Kan jeg automatisere tjeklisten?",
         "Ja — det er hele pointen. Læg kommandoerne i et script, og lad det køre som "
         "det sidste trin i dit bygge-script, før zips navngives og uploades. Hvis et "
         "tjek fejler, fejler buildet, og der kommer ingen udgivelse."),
        ("Hvad gør jeg, hvis jeg finder en gammel fil i zippen?",
         "Stop udgivelsen. Find ud af hvorfor filen afveg (manuel kopi? glemt build-trin?), "
         "ret årsagen — ikke kun symptomet — bump versionsnummeret, byg igen og kør "
         "hele tjeklisten én gang til på det nye artefakt."),
    ],
    'body': '''
<section class="problem" id="problem">
  <div class="container">
    <h2>Problemet: du tester noget andet end det, brugerne får</h2>
    <p>I vores eget projekt udgav vi to versioner af en browser-udvidelse, hvor
    zip-filen manglede de nyeste fejlrettelser — mens alle tests var grønne. Årsagen:
    testene læste kernekildekoden, zippen indeholdt en glemt manuel kopi.
    Hele historien står i
    <a href="/da/blog/release-integrity-hvad-er-det" style="color:var(--color-accent);">casen om release integrity</a>.</p>
    <p>Mønsteret er udbredt, fordi det føles sikkert: buildet virker, tests er grønne,
    så zips bygges sidst og hurtigt. Netop dét sidste trin er det eneste, brugerne
    egentlig rører ved.</p>
  </div>
</section>

<section class="products" id="tjekliste">
  <div class="container">
    <h2>Tjeklisten: syv tjek af din zip</h2>
    <ol>
      <li><strong>Pakket fra ren arbejdskopi?</strong> Byg aldrig fra en mappe med ucommitte ændringer eller uvedhæftede filer. Tjek status først.</li>
      <li><strong>Indeholder den præcis de forventede filer?</strong> Ingen ekstra filer (logs, cache, .DS_Store), ingen manglende.</li>
      <li><strong>Matcher indholdet kilden?</strong> Kør en parity-test: sammenlign hver fil i zippen med dens kilde byte-for-byte.</li>
      <li><strong>Er versionsnummeret korrekt alle steder?</strong> Manifest, package.json, om-fane — samme nummer, og det er højere end den forrige udgivelse.</li>
      <li><strong>Kan artefaktet starte?</strong> Udpak i en ren mappe og lad den reelle runtime (browser, Node, Python) indlæse dérfra — ikke fra din kilde-mappe.</li>
      <li><strong>Er filnavnet unikt?</strong> Navngiv med versionsnummer (<code>produkt-v1.3.7.zip</code>). En fil uden version i navnet bliver før eller siden forvekslet med en gammel.</li>
      <li><strong>Virket det, som brugeren oplever det?</strong> Efter udgivelse: download selve den offentlige fil og gentag tjek 3–5 mod den. Deploy kan fejle stille.</li>
    </ol>
  </div>
</section>

<section class="products" id="kommandoer">
  <div class="container">
    <h2>Tre kommandoer du kan kopiere</h2>
    <p><strong>1) Se præcis hvad zippen indeholder</strong> (fanger skrald og manglende filer):</p>
    <pre style="background:#0f172a;color:#e2e8f0;padding:14px;border-radius:8px;overflow-x:auto;font-size:13px;"><code>unzip -l produkt.zip | sort -k4</code></pre>
    <p style="margin-top:12px;"><strong>2) Parity-tjek: matcher filen i zippen kilden?</strong>
    Udpak i en temp-mappe og sammenlign:</p>
    <pre style="background:#0f172a;color:#e2e8f0;padding:14px;border-radius:8px;overflow-x:auto;font-size:13px;"><code>rm -rf /tmp/ziptest && mkdir /tmp/ziptest
unzip -q produkt.zip -d /tmp/ziptest
diff /tmp/ziptest/kernen.js src/kernen.js \\
  && echo "PARITY OK" || echo "PARITY FEJLEDE"</code></pre>
    <p style="margin-top:12px;"><strong>3) Versions-sweep: find gammelt versionsnummer i artefaktet:</strong></p>
    <pre style="background:#0f172a;color:#e2e8f0;padding:14px;border-radius:8px;overflow-x:auto;font-size:13px;"><code>grep -rn "1\\.3\\.6" /tmp/ziptest \\
  && echo "GAMMEL VERSION I PAKKEN" || echo "version OK"</code></pre>
    <p>Læg de tre trin i et script, og kald det fra dit bygge-script som det
    absolut sidste trin. Fejler ét tjek, fejler buildet — og der udgives ingenting.</p>
  </div>
</section>

<section class="products" id="laering">
  <div class="container">
    <h2>Den ene regel, der dækker det hele</h2>
    <p><strong>Test det, brugerne modtager.</strong> Alt andet — grønne tests, pæne
    builds, gode intentionslister — er om vejen, ikke målet. Én parity-test mod
    selve artefaktet had fanget vores fejl, før nogen bruger så den.</p>
    <p>Det samme princip gælder uden for software: det dokumentet kunden downloader,
    den fil der lægges op til markedspladsen, det billede siden viser — åbn det,
    se på det, verificér det efter udgivelsen. Det tager minutter og sparer
    tillid.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/da/blog/indsæt-uden-formatering-i-chrome" class="btn-primary">Prøv Clean Copy gratis &rarr;</a>
      &nbsp;
      <a href="/da/blog/release-integrity-hvad-er-det" class="btn-secondary">Casen bag tjeklisten</a>
    </div>
  </div>
</section>
'''.replace('had fanget', 'havde fanget'),
    'related': ('<a href="/da/blog/release-integrity-hvad-er-det" lang="da">Release integrity: casen</a> &middot; '
                '<a href="/da/blog/indsæt-uden-formatering-i-chrome" lang="da">Indsæt uden formatering i Chrome</a> &middot; '
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
    <p class="hero-note">Opdateret august 2026 &middot; 5 minutters læsning</p>
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
