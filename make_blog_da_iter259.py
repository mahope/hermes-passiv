#!/usr/bin/env python3
"""Iteration 259: Tre danske spejle af EN-posts (moenster fra iter255-258).

1. building-html-to-markdown-converter -> da/blog/byg-en-html-til-markdown-konverter
2. html-to-markdown-cli                -> da/blog/html-til-markdown-cli
3. cmp-comparison-2026                 -> da/blog/cmp-sammenligning-2026
"""
import json, re, os, sys
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'byg-en-html-til-markdown-konverter',
        'en_slug': 'building-html-to-markdown-converter',
        'title': 'Byg din egen HTML til markdown-konverter — feltguide (2026)',
        'h1': 'Byg en HTML til<br>markdown-konverter',
        'desc': ('Sådan bygger du en HTML til markdown-konverter der håndterer lister, '
                 'tabeller med pipes og blokcitater — de tre steder hvor naive '
                 'konvertere fejler. Med kodeeksempler.'),
        'og_desc': ('Feltguide til at bygge en HTML-til-markdown-konverter: lister, tabeller '
                    'med escapede pipes, blokcitater og kanttilfældene der ødelægger '
                    'simple regex-løsninger.'),
        'badge': 'UDVIKLER &middot; MARKDOWN',
        'subtitle': ('At konvertere HTML til markdown lyder som et regexp-job — indtil du møder '
                     'indlejrede lister, tabeller hvis indhold selv indeholder pipes, og '
                     'blokcitater i flere niveauer. Her er reglerne din konverter skal følge, '
                     'og faldgruberne den skal overleve.'),
        'cta1': '<a href="/clean-copy-tool" class="btn-primary">Se en færdig konverter &rarr;</a>',
        'cta2': '<a href="#regler" class="btn-secondary">Spring til reglerne</a>',
        'tool_url': '/clean-copy-tool',
        'tool_label': 'Prøv konverteren uden at bygge selv',
        'faq': [
            ("Skal jeg skrive min egen konverter?",
             "Hvis du bare skal konvertere indhold lejlighedsvis: nej, brug en færdig "
             "løsning (Clean Copy, turndown.js eller pandoc). Byg selv kun hvis du har "
             "specielle krav — fx en bestemt frontend i CI eller egne markdown-dialekter."),
            ("Hvorfor fejler regex-baserede konvertere på tabeller?",
             "Fordi markdown-tabeller bruger | som kolonneafgrænser. En tabelcelle der "
             "indeholder teksten \"pris | moms\" ødelægger tabellen, medmindre pipen "
             "escapes som \\|. Naive konvertere glemmer det."),
            ("Hvad med indlejrede lister?",
             "HTML tillader vilkårlig dybde; markdown bruger indrykning. Hvert niveau "
             "skal indrykkes konsistent (typisk 2 eller 4 mellemrum), og blandede "
             "ordnede/uordnede lister kræver at man holder styr på nummereringen."),
            ("Hvor svært er blokcitater?",
             "Enkelte niveauer er lette (&gt; foran linjen). Flere niveauer kræver "
             "&gt;&gt;, og citater der indeholder lister eller overskrifter skal have "
             "præfikset på hver eneste linje — også tomme."),
        ],
        'body': '''
<section class="problem" id="regler">
  <div class="container">
    <h2>De tre regler din konverter skal følge</h2>
    <ol>
      <li><strong>Lister:</strong> gå rekursivt gennem &lt;ol&gt;/&lt;ul&gt;. Indryk hvert
      niveau med to mellemrum pr. dybde, og bevar nummerering ved ordnede lister
      (start-attributten tælles med).</li>
      <li><strong>Tabeller med pipes:</strong> escape alle <code>|</code> i celletekst
      som <code>\\|</code>, før cellerne samles med nye pipes. Uden det ødelægger én
      pipe i én celle hele tabellen.</li>
      <li><strong>Blokcitater:</strong> præfiks hver linje i citatet med
      <code>&gt; </code> — inklusive tomme linjer og indhold af under-elementer.
      Niveauer adskilles med ekstra <code>&gt;</code>.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">&lt;td&gt;pris | moms&lt;/td&gt;
→ | pris \\| moms |     # rigtigt
→ | pris | moms |     # forkert: tabellen knækker</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Faldgruber udover de tre</h2>
    <ul>
      <li><strong>Tomme elementer:</strong> &lt;p&gt;&lt;/p&gt; må ikke blive til en
      løs stjerne eller hash.</li>
      <li><strong>Inline-formattering:</strong> fed/kursiv/kode skal mappes hver for sig,
      og indlejret kode må ikke parses videre (ingen fed inde i <code>kode</code>).</li>
      <li><strong>Entiteter:</strong> &amp;amp;, &amp;lt;, &amp;nbsp; skal afkodes — men
      kun ét niveau.</li>
      <li><strong>Hvide mellemrum:</strong> HTML kollapser dem, markdown gør ikke.
      Trim og normalisér inden output.</li>
    </ul>
    <p>Vil du se resultatet i praksis? Clean Copy bruger samme regler i sin
    HTML-til-markdown-kerne — prøv den på din egen tekst:</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy-tool" class="btn-primary">Test konverteren nu &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/html-til-markdown-konverter">den komplette HTML-til-markdown-guide</a>,
    <a href="/da/blog/html-til-markdown-cli">CLI-versionen til terminalen</a> og
    <a href="/da/blog/tabeljustering-html-til-markdown">kolonnejustering i tabeller</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/html-til-markdown-konverter" lang="da">HTML til markdown</a> &middot; '
                    '<a href="/da/blog/html-til-markdown-cli" lang="da">HTML til markdown i CLI</a> &middot; '
                    '<a href="/da/blog/tabeljustering-html-til-markdown" lang="da">Kolonnejustering</a>'),
    },
    {
        'slug': 'html-til-markdown-cli',
        'en_slug': 'html-to-markdown-cli',
        'title': 'HTML til markdown fra terminalen — komplet guide 2026',
        'h1': 'HTML til markdown<br>i terminalen',
        'desc': ('Konvertér HTML til markdown direkte fra kommandolinjen: fil, stdin eller '
                 'URL med én kommando. Scriptbart, offline, nul afhængigheder — klar til CI.'),
        'og_desc': ('Én kommando, tre inputs: fil, pipe eller URL. Sådan konverterer du HTML '
                    'til markdown i terminalen — scriptbar ende-til-ende, intet forlader '
                    'din maskine.'),
        'badge': 'UDVIKLER &middot; CLI',
        'subtitle': ('Web-værktøjer er fine til én fil. Men når du skal konvertere hundrede '
                     'dokumenter i et pipeline-job, skal det kunne scriptes: fil ind, '
                     'markdown ud, ingen browser, ingen upload. Sådan gør du det med '
                     'én kommando.'),
        'cta1': '<a href="/clean-copy#cli" class="btn-primary">Hent CLI\'en &rarr;</a>',
        'cta2': '<a href="#kommandoer" class="btn-secondary">Se kommandoerne</a>',
        'tool_url': '/clean-copy#cli',
        'tool_label': 'Installationsinstrukser og eksempler',
        'faq': [
            ("Hvordan konverterer jeg HTML til markdown fra kommandolinjen?",
             "Med Clean Copy CLI: clean-copy convert side.html -o side.md. Værktøjet "
             "læser også stdin og URL'er, så curl -s https://eksempel.dk | clean-copy "
             "convert - > side.md virker direkte."),
            ("Kan jeg pipe curl-output gennem konverteren?",
             "Ja. Konverteren læser stdin når input-filen er '-' eller udelades: "
             "curl -s <url> | clean-copy convert - . Det gør den velegnet til one-liners "
             "og shell-scripts."),
            ("Virker det i CI-pipelines?",
             "Ja. CLI'en er en enkelt statisk fil uden runtime-afhængigheder, så den kan "
             "ligge i repoet og køres fra GitHub Actions eller ethvert andet CI-system "
             "uden installation."),
            ("Bliver links, overskrifter og tabeller bevaret?",
             "Ja. Overskrifter mappes til #-niveauer, links til [tekst](url)-formatet, "
             "tabeller til pipe-tabeller inklusive kolonnejustering, og lister med "
             "korrekt indrykning."),
            ("Bliver noget uploaded til en server?",
             "Nej. Konverteringen sker 100 % lokalt på din maskine. Det betyder også at "
             "værktøjet virker offline og bag strenge firewalls."),
        ],
        'body': '''
<section class="problem" id="kommandoer">
  <div class="container">
    <h2>Én kommando, tre inputs</h2>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;"># Fra fil
clean-copy convert dokument.html -o dokument.md

# Fra stdin (pipe)
curl -s https://eksempel.dk/artikel | clean-copy convert - &gt; artikel.md

# Direkte fra URL
clean-copy convert https://eksempel.dk/artikel -o artikel.md</pre>
    <p>Samme konverteringskerne som browserudvidelsen: overskrifter, links, lister,
    tabeller (inklusive justering) og kodeblokke kommer igennem intakt.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvorfor terminalen?</h2>
    <div class="problem-cards">
      <div class="card"><h3>Scriptbart ende-til-ende</h3><p>Batch-konvertér et helt katalog
      med en for-loop. Kombinér med grep, jq og git i pipelines.</p></div>
      <div class="card"><h3>Intet forlader maskinen</h3><p>Konverteringen kører lokalt —
      fint til interne dokumenter og kundeunderlag under tavshedspligt.</p></div>
      <div class="card"><h3>Nul afhængigheder</h3><p>Én statisk fil. Ingen npm install,
      ingen virtuel environment, ingen Node eller Python på build-serveren.</p></div>
      <div class="card"><h3>Klar til CI</h3><p>Læg filen i repoet og kald den fra GitHub
      Actions — der findes en færdig action til netop det.</p></div>
    </div>
    <p>Læs videre:
    <a href="/da/blog/html-til-markdown-konverter">web-guiden til HTML-til-markdown</a>,
    <a href="/da/blog/byg-en-html-til-markdown-konverter">hvordan man bygger sin egen konverter</a> og
    <a href="/da/blog/7-gratis-dev-tekstvaerktoejer">syv gratis tekstværktøjer til udviklere</a>.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/clean-copy#cli" class="btn-primary">Hent CLI'en &rarr;</a>
    </div>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/html-til-markdown-konverter" lang="da">HTML til markdown</a> &middot; '
                    '<a href="/da/blog/byg-en-html-til-markdown-konverter" lang="da">Byg din egen konverter</a> &middot; '
                    '<a href="/da/blog/7-gratis-dev-tekstvaerktoejer" lang="da">Gratis dev-værktøjer</a>'),
    },
    {
        'slug': 'cmp-sammenligning-2026',
        'en_slug': 'cmp-comparison-2026',
        'title': 'CMP-sammenligning 2026: De bedste cookie-samtykkeplatforme til EU',
        'h1': 'CMP-sammenligning<br>for EU-websteder',
        'desc': ('Cookiebot, CookieYes, Iubenda, Osano, Complianz og Quantcast sammenlignet '
                 'på pris, Google Consent Mode v2, tilgængelighed og egnethed til bureauer.'),
        'og_desc': ('Syv cookie-samtykkeplatforme (CMP) sammenlignet for EU-websteder: pris, '
                    'Consent Mode v2, WCAG-krav og hvad der passer bedst til bureauer med '
                    'flere kunder.'),
        'badge': 'GDPR &middot; COOKIES',
        'subtitle': ('Et EU-websted med analytics eller annoncer skal have gyldigt samtykke '
                     'før cookies sættes — ePrivacydirektivet plus GDPR kræver det, og '
                     'Google Consent Mode v2 kræver signalerne. Men hvilken CMP skal du '
                     'vælge? Syv platforme gennemgået.'),
        'cta1': '<a href="/cookie-check" class="btn-primary">Tjek dit cookie-setup &rarr;</a>',
        'cta2': '<a href="#tabellen" class="btn-secondary">Se sammenligningen</a>',
        'tool_url': '/cookie-check',
        'tool_label': 'Scan dine cookies gratis',
        'faq': [
            ("Hvad er en CMP, og hvorfor skal jeg bruge én?",
             "En Consent Management Platform indhenter, lagrer og dokumenterer brugernes "
             "samtykke til cookies. Uden gyldigt samtykke før sporing sætter du bødedygtige "
             "cookies i strid med ePrivacydirektivet og GDPR — og Google Consent Mode v2 "
             "fungerer ikke korrekt uden signalerne."),
            ("Hvilken CMP er bedst til et lille bureau med flere klienter?",
             "Complianz (WordPress) eller CookieYes: begge har multi-site-styring til "
             "rimelige priser. Cookiebot er solid men dyr pr. domæne, så regnestykket "
             "vender først ved få klienter."),
            ("Kan jeg bruge en gratis CMP på kundesider?",
             "Quantcast Choice er gratis og GDPR-gyldig, men uden support og med begrænset "
             "tilpasning. Til betalte kundeleverancer anbefales en betalt plan — support og "
             "dokumentation er en del af det du sælger."),
            ("Understøtter alle CMP'er Google Consent Mode v2?",
             "Nej. Tjek det aktivt før valg: Consent Mode v2 kræves af Google Ads og "
             "Analytics 4 i EØS fra marts 2024. Alle syv platforme her understøtter v2, "
             "men implementeringens kvalitet varierer."),
            ("Kræver EAA at cookiebannere er tilgængelige?",
             "Ja. Det europæiske tilgængelighedsloven omfatter e-handel og webtjenester — "
             "et banner der ikke kan betjenes med tastatur eller skærmlæser er både en "
             "EAA-overtrædelse OG et ugyldigt samtykke."),
        ],
        'body': '''
<section class="problem" id="tabellen">
  <div class="container">
    <h2>Platformene sammenlignet</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Platform</th><th>Pris (ca.)</th><th>Bedst til</th></tr>
      <tr><td><strong>Cookiebot</strong> (Usercentrics)</td><td>fra ~29 €/md</td><td>Store sites, streng juridisk dokumentation</td></tr>
      <tr><td><strong>CookieYes</strong></td><td>gratis / fra ~$10/md</td><td>SMB og bureauer med multi-site</td></tr>
      <tr><td><strong>Iubenda</strong></td><td>fra ~9 €/md</td><td>Italienske/europæiske SMB'er, alt-i-én compliance</td></tr>
      <tr><td><strong>Osano</strong></td><td>fra ~$35/md</td><td>Mellemstore virksomheder, vendor management</td></tr>
      <tr><td><strong>Complianz</strong></td><td>gratis / ~€59/år</td><td>WordPress-sites og bureauer</td></tr>
      <tr><td><strong>Quantcast Choice</strong></td><td>gratis (TCF)</td><td>Publikationssites med annonceindtægter</td></tr>
    </table>
    <p>Priser er vejledende og kan ændres — tjek leverandørens aktuelle prismodel før valg.</p>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Hvad der afgør valget</h2>
    <ol>
      <li><strong>Juridisk dækning:</strong> TCF-certificering hvis du bruger annoncer;
      egen logik er fint til ren analytics.</li>
      <li><strong>Consent Mode v2:</strong> nødvendigt for Google Ads/GA4 i EØS —
      test signallerne efter installation.</li>
      <li><strong>Tilgængelighed:</strong> banneret skal opfylde WCAG 2.1 AA (EAA).
      Test med tastatur og skærmlæser.</li>
      <li><strong>Dokumentation:</strong> du skal kunne vise hvornår samtykket blev givet.
      Logning er en del af produktet.</li>
    </ol>
    <p>Uanset valg: scan sitet bagefter og se om cookies faktisk respekterer samtykket.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/cookie-check" class="btn-primary">Scan dine cookies gratis &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/gdpr-hjemmeside-tjekliste">GDPR-tjeklisten til hjemmesiden</a>,
    <a href="/da/blog/gdpr-boeder-2026">GDPR-bøder i 2026</a> og
    <a href="/da/blog/gratis-gdpr-dokumentgeneratorer">gratis GDPR-dokumentgeneratorer</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/gdpr-hjemmeside-tjekliste" lang="da">GDPR-tjekliste</a> &middot; '
                    '<a href="/da/blog/gdpr-boeder-2026" lang="da">GDPR-bøder 2026</a> &middot; '
                    '<a href="/da/blog/gratis-gdpr-dokumentgeneratorer" lang="da">Dokumentgeneratorer</a>'),
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


def add_hub_card(p):
    path = f'{SITE}/da.html'
    c = open(path).read()
    card_url = f'/da/blog/{p["slug"]}'
    if card_url in c:
        print(f'hub: {p["slug"]} already present')
        return
    badge = {'byg-en-html-til-markdown-konverter': 'UDVIKLER · MARKDOWN',
             'html-til-markdown-cli': 'UDVIKLER · TERMINAL',
             'cmp-sammenligning-2026': 'GDPR · COOKIES'}[p['slug']]
    desc = {'byg-en-html-til-markdown-konverter':
            'Reglerne din egen konverter skal følge: lister, tabeller med escapede pipes og blokcitater — med kodeeksempler.',
            'html-til-markdown-cli':
            'Konvertér HTML til markdown fra terminalen: fil, stdin eller URL med én kommando — scriptbart og offline-klar.',
            'cmp-sammenligning-2026':
            'Cookiebot, CookieYes, Iubenda, Osano, Complianz og Quantcast sammenlignet på pris, Consent Mode v2 og bureau-egnethed.'}[p['slug']]
    title_short = {'byg-en-html-til-markdown-konverter': 'Byg en HTML-til-markdown-konverter',
                   'html-til-markdown-cli': "HTML til markdown i terminalen",
                   'cmp-sammenligning-2026': 'CMP-sammenligning 2026'}[p['slug']]
    card = f'''
      <div class="product-card">
        <div class="product-badge product-badge-secondary">{badge}</div>
        <div class="product-body">
          <h3><a href="{card_url}" style="color:inherit;text-decoration:none;">{title_short}</a></h3>
          <p class="product-desc">{desc}</p>
          <div class="product-details"><span class="product-meta">📖 5 min</span><span class="product-meta">🇩🇰 Dansk guide</span></div>
          <a href="{card_url}" class="btn-secondary" style="margin-top:12px;">Læs guide →</a>
        </div>
      </div>
'''
    idx = c.rfind('</div>')  # last closing of the grid — insert before it is fragile;
    # safer: insert before the comment/section end of the blog grid
    marker = c.find(card_url)  # unused
    # Insert after the previous known last card block: use last occurrence of '</div>\n\n      <div class="product-card">'
    # Fallback: append before closing of products grid via last '</div>' before 'product-grid'
    pos = c.rfind('<a href="/da/blog/')
    # find the end of that card's enclosing div: search forward for '\n      </div>\n'
    end = c.find('\n      </div>\n', pos)
    ins = end + len('\n      </div>\n')
    c = c[:ins] + card + c[ins:]
    open(path, 'w').write(c)
    print(f'hub: card added for {p["slug"]}')


def verify_hub():
    import glob
    files = {os.path.basename(f)[:-5] for f in glob.glob(f'{SITE}/da/blog/*.html')}
    hub = set(re.findall(r'href="/da/blog/([^"]+)"', open(f'{SITE}/da.html').read()))
    missing = files - hub
    extra = hub - files
    print(f'verify_hub: disk={len(files)} hub={len(hub)} missing_in_hub={sorted(missing)} dead_links={sorted(extra)}')
    assert not extra, f'hubbet linker til ikke-eksisterende sider: {extra}'
    return missing


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
        add_hub_card(p)
        outs.append(out)
        en_files.append(f'{SITE}/blog/{p["en_slug"]}.html')

    verify_hub()
    broken = check_links(outs + en_files + [f'{SITE}/da.html'])
    if broken:
        print('BROKEN INTERNAL LINKS:')
        for path, link in broken:
            print(f'  {path} -> {link}')
        sys.exit(1)
    print('Internal link check: OK')


if __name__ == '__main__':
    main()
