#!/usr/bin/env python3
"""Iteration 256: Tre danske spejle af EN-posts.

1. copy-table-website-to-google-sheets -> da/blog/kopier-tabel-til-google-sheets
2. nis2-incident-report-checklist      -> da/blog/nis2-haendelsesrapport-skabelon
3. gdpr-vs-nis2-overlap                -> da/blog/gdpr-vs-nis2-overlap

Samme moenster som iter255: Article+FAQ JSON-LD, hreflang-par begge veje,
krydslink fra EN-post, sitemap-opdatering, intern linkcheck.
"""
import json, re, os, sys
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'kopier-tabel-til-google-sheets',
        'en_slug': 'copy-table-website-to-google-sheets',
        'title': 'Kopiér en tabel fra en hjemmeside til Google Sheets (2026-guide)',
        'h1': 'Kopiér tabel<br>til Google Sheets',
        'desc': ('Sådan kopierer du en tabel fra en hjemmeside direkte ind i Google '
                 'Sheets — uden at rækker og kolonner smelter sammen. To klik med '
                 'gratis værktøj.'),
        'og_desc': ('Prissider, statistik og tabeller direkte ind i Sheets med korrekt '
                    'struktur. Den 2-klik-metode der bevarer alle rækker og kolonner.'),
        'badge': 'RENGØR TEKST &middot; TABELLER',
        'subtitle': ('Prissider, ligatabeller og offentlig statistik: at få dem ind i '
                     'Google Sheets ender normalt i én kæmpe tekstblok eller timers '
                     'genindtastning. Her er metoden der bevarer strukturen.'),
        'cta1': '<a href="/clean-copy-tool" class="btn-primary">Prøv tabel-værktøjet &rarr;</a>',
        'cta2': '<a href="#metode" class="btn-secondary">Se metoden</a>',
        'tool_url': '/clean-copy-tool',
        'tool_label': 'Prøv Clean Copy tabel-tilstand',
        'faq': [
            ("Hvorfor kollapser tabellen når jeg indsætter den?",
             "Fordi markering med musen ofte fanger omkringliggende afsnit, reklamer "
             "og billedtekster sammen med tabellen. Sheets modtager så en blanding af "
             "tekst der ikke kan parses som rækker og kolonner."),
            ("Virker det også med PDF-tabeller?",
             "Nej — PDF'er indeholder ikke rigtige HTML-tabeller. Til PDF bruger du en "
             "anden fremgangsmåde; se vores guide til at kopiere tabeller fra PDF til Excel."),
            ("Kan jeg bruge det i Firefox?",
             "Ja. Clean Copy findes som udvidelse til både Chrome og Firefox, og "
             "tabel-tilstanden fungerer ens i begge browsere."),
            ("Er værktøjet gratis?",
             "Kernen er gratis: ren tekst, markdown og tabelkopi. Pro-versionen tilføjer "
             "brugerdefinerede regler for de sider du bruger hver dag."),
        ],
        'body': '''
<section class="problem">
  <div class="container">
    <h2>Hvorfor de sædvanlige metoder fejler</h2>
    <ul>
      <li><strong>Markér og kopiér</strong> — træk-markering fanger ofte afsnit, annoncer
      og billedtekster. Indsat i Sheets smelter alt sammen til nogle få overbelastede celler.</li>
      <li><strong>Skærmbillede + OCR</strong> — OCR introducerer fejl, og et tal med forkert
      ciffer er værre end intet tal.</li>
      <li><strong>Genindtastning</strong> — fint til tre rækker. Ubrugeligt til et datasæt
      på 200 rækker.</li>
    </ul>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy-tool" class="btn-primary">Test tabel-tilstanden nu &rarr;</a>
    </div>
  </div>
</section>

<section class="products" id="metode">
  <div class="container">
    <h2>Løsningen: to klik</h2>
    <ol>
      <li>Installér den gratis Clean Copy-udvidelse til Chrome eller Firefox.</li>
      <li>Højreklik på tabellen og vælg <em>Kopiér tabel</em> — udvidelsen finder det
      rigtige &lt;table&gt;-element under markøren.</li>
      <li>Indsæt i Google Sheets med Ctrl+V / Cmd+V. Hver række bliver en række,
      hver kolonne en kolonne.</li>
    </ol>
    <p>Til bulk kan CLI'en tage en hel URL og outputte CSV direkte:
    se vores guide til <a href="/da/blog/tilgaengelighedsscanner-cli"
    style="color:var(--color-accent);">kommandolinjeværktøjerne</a>.</p>
    <p>Læs også: <a href="/da/blog/kopier-tabel-til-excel">tabeller til Excel</a>,
    <a href="/da/blog/kopier-tabel-hjemmeside-til-notion">tabeller til Notion</a> og
    <a href="/da/blog/kopier-tabel-fra-pdf">tabeller fra PDF</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/kopier-tabel-til-excel" lang="da">Tabeller til Excel</a> &middot; '
                    '<a href="/da/blog/kopier-tabel-hjemmeside-til-notion" lang="da">Tabeller til Notion</a> &middot; '
                    '<a href="/da/blog/kopier-tabel-fra-pdf" lang="da">Tabeller fra PDF</a>'),
    },
    {
        'slug': 'nis2-haendelsesrapport-skabelon',
        'en_slug': 'nis2-incident-report-checklist',
        'title': 'NIS2-hændelsesrapport: tjekliste og skabelon til små virksomheder',
        'h1': 'NIS2-Hændelses­rapport:<br>Tjekliste &amp; skabelon',
        'desc': ('Hvad skal dokumenteres når en sikkerhedshændelse indtræffer — og hvordan '
                 'rapporteres det under NIS2? Tjekliste med frister og seks afsnit.'),
        'og_desc': ('24-timers varsling, slutr rapport inden for én måned og seks obligatoriske '
                    'afsnit. Skabelonen du skal have klar FØR hændelsen kommer.'),
        'badge': 'NIS2 &middot; SKABELON',
        'subtitle': ('NIS2 artikel 21 kræver processer for hændelseshåndtering og -rapportering. '
                     'Selv små virksomheder under størrelsestærsklen møder kravet via kundernes '
                     'kontrakter. Her er hvad der skal dokumenteres — og hvornår.'),
        'cta1': '<a href="/nis2-check-da" class="btn-primary">Tag selvvurderingen &rarr;</a>',
        'cta2': '<a href="#afsnit" class="btn-secondary">Se de 6 afsnit</a>',
        'tool_url': '/nis2-check-da',
        'tool_label': 'Tjek jeres beredskab gratis',
        'faq': [
            ("Hvor hurtigt skal vi rapportere?",
             "Tidlig varsling inden for 24 timer efter I bliver klar over hændelsen. Det er "
             "ikke en detaljeret rapport — kun besked om at noget er sket, hvilke systemer "
             "er berørt, og hvad I gør. Slutrapporten skal inden for én måned."),
            ("Gælder det os, selvom vi er under tærsklen?",
             "Ofte ja — via kontrakter. Kunder der selv er dækket af NIS2 stiller krav om, "
             "at deres leverandører kan demonstrere hændelsesberedskab."),
            ("Findes der et officielt format?",
             "Nej, men myndighederne forventer et minimumssæt af afsnit. Med en skabelon "
             "klar på forhånd er forskellen mellem panik og rolig håndtering stor."),
            ("Hvem skal have rapporten?",
             "Det nationale CSIRT, berørte kunder — og jeres egen ledelse, som under NIS2 "
             "kan holdes personligt ansvarlig for cybersikkerheden."),
        ],
        'body': '''
<section class="problem">
  <div class="container">
    <h2>Fristerne</h2>
    <ul>
      <li><strong>24 timer:</strong> tidlig varsling til CSIRT — kort besked, ikke analyse.</li>
      <li><strong>72 timer:</strong> supplerende information om hændelsens art og alvor.</li>
      <li><strong>1 måned:</strong> slutrapport med rodårsagsanalyse, konsekvensvurdering
      og forebyggende foranstaltninger.</li>
    </ul>
    <div style="text-align:center;margin-top:20px;">
      <a href="/nis2-check-da" class="btn-primary">Har I planen? Test jer selv &rarr;</a>
    </div>
  </div>
</section>

<section class="products" id="afsnit">
  <div class="container">
    <h2>Rapportens seks afsnit</h2>
    <ol>
      <li><strong>Sammendrag (ét afsnit)</strong> — hvad skete der, hvornår, hvilke systemer,
      status nu. Skrevet til ikke-teknikere.</li>
      <li><strong>Tidslinje</strong> — opdagelse, indgreb, kommunikation — med klokkeslæt.</li>
      <li><strong>Konsekvens</strong> — berørte data, kunder og tjenester; nedetid og omfang.</li>
      <li><strong>Inddæmning</strong> — hvilke foranstaltninger stoppede spredningen, hvornår.</li>
      <li><strong>Rodårsag</strong> — teknisk og organisatorisk; hvad muliggjorde hændelsen.</li>
      <li><strong>Forebyggelse</strong> — konkrete tiltag, ejerskab og deadlines.</li>
    </ol>
    <p>Udskriv listen og læg den i beredskabsmappen — når noget sker, udfyldes afsnittene
    i rækkefølge. Læs også:
    <a href="/da/blog/nis2-beredskabstjek-2026">NIS2-beredskabet i fem trin</a> og
    <a href="/da/blog/nis2-leverandoerkaede-sikkerhed">sikkerhed i leverandørkæden</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/nis2-beredskabstjek-2026" lang="da">Beredskabstjek 2026</a> &middot; '
                    '<a href="/da/blog/nis2-leverandoerkaede-sikkerhed" lang="da">Leverandørkæde</a> &middot; '
                    '<a href="/da/blog/gratis-nis2-vaerktoejer" lang="da">Gratis NIS2-værktøjer</a>'),
    },
    {
        'slug': 'gdpr-vs-nis2-overlap-da',
        'en_slug': 'gdpr-vs-nis2-overlap',
        'title': 'GDPR vs NIS2: hvor de overlapper — og hvor de ikke gør',
        'h1': 'GDPR vs NIS2:<br>Hvor overlapper de?',
        'desc': ('To EU-regværker, én lille virksomhed. Hvad GDPR og NIS2 har til fælles, '
                 'hvor de adskiller sig, og hvordan ét dokumentsæt dækker begge.'),
        'og_desc': ('NIS2\'s sikkerhedskrav er stort set en operationel udfoldelse af GDPR '
                    'artikel 32. Dokumentér én gang — brug som dokumentation under begge.'),
        'badge': 'GDPR + NIS2 &middot; OVERSIGT',
        'subtitle': ('Den mest almindelige fejl er at behandle GDPR og NIS2 som to separate '
                     'projekter. Det fordobler arbejdet og garanterer at sporene driver fra '
                     'hinanden. De fleste af NIS2\'s krav er allerede dækket af GDPR art. 32 — '
                     'hvis I dokumenterer det rigtigt.'),
        'cta1': '<a href="/free-tools" class="btn-primary">Hent gratis skabeloner &rarr;</a>',
        'cta2': '<a href="#overlap" class="btn-secondary">Se overlapningen</a>',
        'tool_url': '/free-tools',
        'tool_label': 'Gratis compliance-skabeloner',
        'faq': [
            ("Er vi omfattet af begge?",
             "GDPR gælder enhver der behandler persondata — altså også jer. NIS2 rammer "
             "direkte mellemstore og store virksomheder i 18 sektorer, men kravene når "
             "mindre leverandører via kundernes kontrakter og indkøbspørgeskemaer."),
            ("Hvad præcis overlapper?",
             "NIS2 artikel 21 udfolder hvad GDPR artikel 32 allerede kræver: risikoanalyse, "
             "hændelseshåndtering, kontinuitet, leverandørkædesikkerhed, adgangskontrol og MFA. "
             "Ét ordentligt dokumentsæt tjener som bevis under begge."),
            ("Hvad er forskelligt?",
             "Rapporteringsfristerne (24/72 timer til CSIRT), ledelsens personlige ansvar, "
             "og at GDPR handler om persondata mens NIS2 handler om driftssikkerhed generelt."),
            ("Hvor starter vi?",
             "Med ét fælles dokumentsæt: risikovurdering, hændelsesplan, leverandørliste og "
             "adgangsstyring. Vores gratis skabeloner dækker kernen af begge regværker."),
        ],
        'body': '''
<section class="problem" id="overlap">
  <div class="container">
    <h2>Hvad der overlapper</h2>
    <table style="width:100%;border-collapse:collapse;font-size:0.92rem;">
      <tr><th style="text-align:left;padding:8px;border-bottom:2px solid var(--color-border);">Krav</th>
          <th style="text-align:left;padding:8px;border-bottom:2px solid var(--color-border);">GDPR</th>
          <th style="text-align:left;padding:8px;border-bottom:2px solid var(--color-border);">NIS2</th></tr>
      <tr><td style="padding:8px;border-bottom:1px solid var(--color-border);">Risikoanalyse</td><td>Art. 32</td><td>Art. 21</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid var(--color-border);">Hændelseshåndtering</td><td>Art. 33 (databrud)</td><td>Art. 21+23</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid var(--color-border);">Leverandørkæde</td><td>Art. 28 (DBA)</td><td>Art. 21</td></tr>
      <tr><td style="padding:8px;border-bottom:1px solid var(--color-border);">Kryptering / MFA</td><td>Art. 32</td><td>Art. 21</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/free-tools" class="btn-primary">Hent skabelonerne gratis &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan undgår du dobbeltarbejde</h2>
    <ol>
      <li>Dokumentér sikkerhedsforanstaltningerne ÉN gang — med jeres faktiske praksis.</li>
      <li>Lad samme leverandørliste og DBA'er tjene begge regværker.</li>
      <li>Én hændelsesplan med to rapporteringsben: databrud til Datatilsynet,
      hændelser til CSIRT.</li>
      <li>Før ét årligt review der dækker begge lovgivninger.</li>
    </ol>
    <p>Læs videre:
    <a href="/da/blog/gdpr-hjemmeside-tjekliste">GDPR-tjeklisten til hjemmesider</a>,
    <a href="/da/blog/dbbaftale-webbureau">DBA-aftalen for bureauer</a> og
    <a href="/da/blog/nis2-beredskabstjek-2026">NIS2-beredskabet</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/gdpr-hjemmeside-tjekliste" lang="da">GDPR-tjekliste</a> &middot; '
                    '<a href="/da/blog/nis2-beredskabstjek-2026" lang="da">NIS2-beredskab</a> &middot; '
                    '<a href="/da/blog/dbbaftale-webbureau" lang="da">DBA-aftale</a>'),
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
    <p class="hero-note">Opdateret august 2026 &middot; 7 minutters læsning</p>
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
    da_f = f'{SITE}/{da_path}.html'
    en = open(en_f).read()
    da_url = f'{BASE}/{da_path}'
    if f'hreflang="da" href="{da_url}"' not in en:
        en = en.replace('</head>',
                        f'<link rel="alternate" hreflang="en" href="{BASE}/blog/{en_slug}">\n'
                        f'<link rel="alternate" hreflang="da" href="{da_url}">\n</head>')
        print(f'{en_slug}: hreflang pair added')
    else:
        print(f'{en_slug}: hreflang already present')
    if 'Dansk version af denne guide' not in en:
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
