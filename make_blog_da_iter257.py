#!/usr/bin/env python3
"""Iteration 257: Tre danske spejle af EN-posts (moenster fra iter255/256).

1. nis2-checklist-pdf              -> da/blog/nis2-tjekliste-25-punkter
2. copy-table-website-to-airtable  -> da/blog/kopier-tabel-hjemmeside-til-airtable
3. free-gdpr-document-generators   -> da/blog/gratis-gdpr-dokumentgeneratorer
"""
import json, re, os, sys
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'nis2-tjekliste-25-punkter',
        'en_slug': 'nis2-checklist-pdf',
        'title': 'NIS2-tjekliste: 25 punkter før din næste revision (PDF-klar)',
        'h1': 'NIS2-tjekliste:<br>25 punkter før revision',
        'desc': ('De 25 kontroller der dækker NIS2 artikel 21 — risikoanalyse, '
                 'hændelser, kontinuitet, leverandørkæde og mere. Print dem og gå '
                 'dem igennem før revisionen.'),
        'og_desc': ('Artikel 21 opdelt i 25 konkrete tjekpunkter med frister og beviskrav. '
                    'Udskriv tjeklisten og gennemgå den med ledelsen.'),
        'badge': 'NIS2 &middot; TJEKLISTE',
        'subtitle': ('NIS2 artikel 21 lyder abstrakt på papiret — men bliver til 25 konkrete '
                     'kontroller du kan sætte krydser i. Her er listen, organiseret efter '
                     'lovens ni områder, klar til print før næste kunde- eller revisionsmøde.'),
        'cta1': '<a href="/nis2-check-da" class="btn-primary">Tag selvvurderingen &rarr;</a>',
        'cta2': '<a href="#tjekliste" class="btn-secondary">Se tjeklisten</a>',
        'tool_url': '/nis2-check-da',
        'tool_label': 'Tjek jeres beredskab gratis',
        'faq': [
            ("Findes der en officiel NIS2-tjekliste som PDF?",
             "Nej. EU og de nationale myndigheder udgiver loven og vejledninger, men ingen "
             "autoriseret PDF-tjekliste. Denne liste er bygget direkte på artikel 21's "
             "tekst, så hver kontrol peger på et konkret stykke lov."),
            ("Faldt mit lille bureau egentlig under NIS2?",
             "Måske ikke direkte — men dine kunder gør, og de stiller krav videre via "
             "kontrakter og indkøbsspørgeskemaer. Tjeklisten er derfor også det rigtige "
             "svar på et kundespørgsmål."),
            ("Hvad sker der hvis vi ignorerer det?",
             "Direkte omfattede virksomheder risikerer bøder op til 10 mio. euro eller 2 % "
             "af globale omsætning. Indirekte er risikoen tabte kontrakter: kunder kan "
             "opsige aftaler uden dokumenteret beredskab."),
            ("Hvordan adskiller NIS2 sig fra GDPR?",
             "GDPR beskytter persondata; NIS2 handler om driftssikkerhed generelt. Stort "
             "set alt NIS2 kræver er dog allerede en udfoldelse af GDPR art. 32 — ét "
             "dokumentsæt kan dække begge."),
        ],
        'body': '''
<section class="problem" id="tjekliste">
  <div class="container">
    <h2>Tjeklisten — 9 områder, 25 kontroller</h2>
    <ol>
      <li><strong>Risikoanalyse &amp; IS-politik (art. 21(2)(a))</strong> — skriftlig politik,
      årlig risikovurdering, ejerskab hos ledelsen.</li>
      <li><strong>Hændelseshåndtering (21(2)(b))</strong> — plan, roller, rapporteringsfrister
      (24 t / 72 t / 1 måned), øvelse.</li>
      <li><strong>Forretningskontinuitet (21(2)(c))</strong> — backup-testet, gendannelsesplan,
      nedetidstærskler.</li>
      <li><strong>Leverandørkædesikkerhet (21(2)(d))</strong> — leverandørliste, DBA'er,
      exit-plan for kritiske systemer.</li>
      <li><strong>Anskaffelse &amp; vedligeholdelse (21(2)(e))</strong> — sikkerhed i
      indkøbskriterier, patch-rutine.</li>
      <li><strong>Effektvurdering (21(2)(f))</strong> — mål for hvor godt foranstaltningerne
      virker, ikke kun at de findes.</li>
      <li><strong>Cyberhygiejne &amp; træning (21(2)(g))</strong> — grundlæggende træning af alle,
      phishing-øvelser.</li>
      <li><strong>Kryptografi (21(2)(h))</strong> — kryptering undervejs og i hvile, nøglestyring.</li>
      <li><strong>HR, adgangsstyring &amp; aktiver (21(2)(i))</strong> — MFA, mindst mulige rettigheder,
      onboarding/offboarding-rutine.</li>
    </ol>
    <p>Punkt 10–25 udfylder hvert område: dokumentation og beviser for hver kontrol.
    Udskriftstip: brug browserens udskriv-funktion på denne side — layoutet holder som PDF.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/nis2-check-da" class="btn-primary">Svar på spørgsmålene interaktivt &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan bruger du den</h2>
    <ol>
      <li>Gennemgå listen én gang og markér hver linje grøn/gul/rød — ærligt.</li>
      <li>Røde linjer bliver til konkrete opgaver med ansvar og deadline.</li>
      <li>Gem resultatet: det ER jeres dokumentation når en kunde eller myndighed spørger.</li>
    </ol>
    <p>Læs videre:
    <a href="/da/blog/nis2-guide-da">NIS2-guiden til små virksomheder</a>,
    <a href="/da/blog/nis2-haendelsesrapport-skabelon">hændelsesrapport-skabelonen</a> og
    <a href="/da/blog/nis2-beredskabstjek-2026">beredskabstjekket i fem trin</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/nis2-guide-da" lang="da">NIS2-guiden</a> &middot; '
                    '<a href="/da/blog/nis2-haendelsesrapport-skabelon" lang="da">Hændelsesrapport</a> &middot; '
                    '<a href="/da/blog/gratis-nis2-vaerktoejer" lang="da">Gratis NIS2-værktøjer</a>'),
    },
    {
        'slug': 'kopier-tabel-hjemmeside-til-airtable',
        'en_slug': 'copy-table-website-to-airtable',
        'title': 'Kopiér en tabel fra en hjemmeside ind i Airtable (2026-guide)',
        'h1': 'Kopiér tabel<br>ind i Airtable',
        'desc': ('Sådan får du en tabel fra en hjemmeside ind i Airtable som rigtige '
                 'records — rækker forbliver records, kolonner forbliver felter. To klik.'),
        'og_desc': ('Markér-kopiér smelter cellerne sammen; CSV-rundture mister data. '
                    'Kopiér tabellen som markdown og indsæt direkte i Airtable.'),
        'badge': 'RENGØR TEKST &middot; AIRTABLE',
        'subtitle': ('Airtable er bygget til strukturerede data — men at få strukturerede data '
                     'IND i den er overraskende svært. Her er metoden der bevarer rækker, '
                     'kolonner og overskrifter uden rengøring bagefter.'),
        'cta1': '<a href="/clean-copy-tool" class="btn-primary">Prøv tabel-værktøjet &rarr;</a>',
        'cta2': '<a href="#metode" class="btn-secondary">Se metoden</a>',
        'tool_url': '/clean-copy-tool',
        'tool_label': 'Prøv Clean Copy tabel-tilstand',
        'faq': [
            ("Hvordan kopierer jeg en tabel ind i Airtable?",
             "Kopiér tabellen som markdown med Clean Copy (højreklik → Kopiér som markdown "
             "over tabellen), og indsæt derefter direkte i et Airtable-grid. Hver række "
             "bliver en record, hver kolonne et felt."),
            ("Hvorfor ender indsættelsen i én kolonne?",
             "Fordi Airtable modtog ren tekst uden struktur — tabs og linjeskift blev ikke "
             "genkendt som cellegrænser. Markdown-tabeller genkendes derimod korrekt."),
            ("Kan jeg indsætte direkte i en eksisterende base?",
             "Ja. Sørg for at kolonnerækkefølgen matcher felttypene, så tal lander som tal "
             "og datoer som datoer. Ellers opret Airtable nye felter automatisk."),
            ("Virker det bag login?",
             "Ja — Clean Copy kører i browseren og læser siden som den ser ud for dig, også "
             "bag login. Intet sendes til nogen server."),
        ],
        'body': '''
<section class="problem">
  <div class="container">
    <h2>Hvorfor de sædvanlige metoder fejler</h2>
    <ul>
      <li><strong>Markér og kopiér tekst</strong> — fanger ekstra indhold, og cellerne
      kollapser til ét felt pr. række.</li>
      <li><strong>Skærmbillede + OCR</strong> — cifre med én forkert digit er værre end
      manglende data.</li>
      <li><strong>CSV-download + import</strong> — kun hvor sitet selv tilbyder eksport;
      formatering går tabt.</li>
      <li><strong>Browser-table-scrapere</strong> — opsætning pr. site, og de stritter imod
      bag login.</li>
    </ul>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy-tool" class="btn-primary">Test metoden nu &rarr;</a>
    </div>
  </div>
</section>

<section class="products" id="metode">
  <div class="container">
    <h2>Løsningen: to klik</h2>
    <ol>
      <li>Installér den gratis Clean Copy-udvidelse til Chrome eller Firefox.</li>
      <li>Højreklik på tabellen og vælg <em>Kopiér som markdown</em> — du får en ren
      markdown-tabel med alle rækker og kolonner.</li>
      <li>Indsæt i Airtable: rækker bliver records, kolonner bliver felter, overskriften
      bliver feltnavne.</li>
    </ol>
    <p>Ingen junk-rækker fra annoncer eller billedtekster, og det virker også på sider
    bag login. Læs også:
    <a href="/da/blog/kopier-tabel-til-excel">tabeller til Excel</a>,
    <a href="/da/blog/kopier-tabel-til-google-sheets">tabeller til Google Sheets</a> og
    <a href="/da/blog/kopier-tabel-hjemmeside-til-notion">tabeller til Notion</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/kopier-tabel-til-excel" lang="da">Tabeller til Excel</a> &middot; '
                    '<a href="/da/blog/kopier-tabel-til-google-sheets" lang="da">Tabeller til Sheets</a> &middot; '
                    '<a href="/da/blog/kopier-tabel-hjemmeside-til-notion" lang="da">Tabeller til Notion</a>'),
    },
    {
        'slug': 'gratis-gdpr-dokumentgeneratorer',
        'en_slug': 'free-gdpr-document-generators',
        'title': 'Gratis GDPR-dokumentgeneratorer: privatlivspolitik, DBA og register',
        'h1': 'Gratis GDPR-<br>dokumentgeneratorer',
        'desc': ('Privatlivspolitik, databehandleraftale og register over behandlingsaktiviteter '
                 '— tre gratis generatorer der kører 100 % i browseren. Ingen konto, intet '
                 'sendes til servere.'),
        'og_desc': ('Tre dokumenter dækker størstedelen af en lille hjemmesides GDPR-eksponering. '
                    'Generér dem i løbet af en eftermiddag — helt i browseren.'),
        'badge': 'GDPR &middot; GRATIS VÆRKTØJER',
        'subtitle': ('En lille virksomhed behøver typisk tre GDPR-dokumenter: en privatlivspolitik '
                     '(art. 13/14), en databehandleraftale (art. 28) og et register over '
                     'behandlingsaktiviteter (art. 30). Ingen af delene kræver juridisk software — '
                     'her er generatorerne, og hvornår en skabelon faktisk ikke rækker.'),
        'cta1': '<a href="/privacy-notice-generator-da" class="btn-primary">Generér privatlivspolitik &rarr;</a>',
        'cta2': '<a href="#workflow" class="btn-secondary">Se arbejdsgangen</a>',
        'tool_url': '/privacy-notice-generator-da',
        'tool_label': 'Start med privatlivspolitikken',
        'faq': [
            ("Hvilke dokumenter skal en lille hjemmeside have?",
             "Tre: en privatlivspolitik (hvad I samler og hvorfor), databehandleraftaler med "
             "leverandører der behandler persondata for jer, og et register over "
             "behandlingsaktiviteter — det første Datatilsynet beder om."),
            ("Sendes mine oplysninger til en server?",
             "Nej. Alle tre generatorer kører udelukkende i din browser. Der er ingen konto, "
             "ingen logning, og outputtet er dit at redigere og udgive."),
            ("Hvornår er en skabelon bedre end en generator?",
             "Når jeres situation er usædvanlig og I vil styre formuleringerne selv. "
             "Generatorerne er hurtigere og lader dig ikke springe obligatoriske felter over; "
             "skabeloner giver fuld kontrol."),
            ("Hvornår skal jeg have en advokat?",
             "Ved behandling på tværs af grænser uden for EU, særlige datakategorier i større "
             "omfang, eller hvis Datatilsynet allerede har henvendt sig. Til almindelige "
             "formularer, nyhedsbreve og analytics rækker udfyldte dokumenter."),
        ],
        'body': '''
<section class="problem">
  <div class="container">
    <h2>De tre generatorer</h2>
    <ul>
      <li><strong><a href="/privacy-notice-generator-da">Privatlivspolitik</a></strong> — går igennem
      formål, retsgrundlag, modtagere, opbevaring og dine rettigheder, og producerer en komplet
      art. 13/14-politik klar til udgivelse.</li>
      <li><strong><a href="/dpa-generator-da">Databehandleraftale</a></strong> — art. 28-aftale med
      sikkerhedsforanstaltninger, underbehandlere og revisionsrettigheder. Til nye leverandører
      eller som jeres egne vilkår over for kunder.</li>
      <li><strong><a href="/ropa-generator-da">Register over behandlingsaktiviteter</a></strong> —
      art. 30-register aktivitet for aktivitet, eksporteret som pæn tabel du kan give til en
      myndighed eller en kundes indkøbsafdeling.</li>
    </ul>
    <div style="text-align:center;margin-top:20px;">
      <a href="/ropa-generator-da" class="btn-primary">Byg registeret &rarr;</a>
    </div>
  </div>
</section>

<section class="products" id="workflow">
  <div class="container">
    <h2>Arbejdsgang der tager én eftermiddag</h2>
    <ol>
      <li>List alle systemer der rører persondata — formularer, analytics, e-mail, hosting.</li>
      <li>Generér privatlivspolitikken ud fra listen og udgiv den.</li>
      <li>Generér eller anmod om en DBA fra hver leverandør der mangler en.</li>
      <li>Opret hver enkelt system som én række i registeret.</li>
      <li>Tjek igen når et nyt værktøj tilføjes — sæt kvartalspåmindelse.</li>
    </ol>
    <p>Samlet indsats: to til fire timer, én gang, plus lidt løbende vedligehold.
    Læs videre:
    <a href="/da/blog/gdpr-hjemmeside-tjekliste">GDPR-tjeklisten til hjemmesider</a>,
    <a href="/da/blog/dbbaftale-webbureau">DBA-aftalen for bureauer</a> og
    <a href="/da/blog/gdpr-boeder-2026">bøderne i 2026</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/gdpr-hjemmeside-tjekliste" lang="da">GDPR-tjekliste</a> &middot; '
                    '<a href="/da/blog/dbbaftale-webbureau" lang="da">DBA-aftale</a> &middot; '
                    '<a href="/da/blog/gdpr-boeder-2026" lang="da">GDPR-bøder 2026</a>'),
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
    da_url = f'{BASE}/{da_path}'
    en = open(en_f).read()
    if f'hreflang="da" href="{da_url}"' not in en:
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
