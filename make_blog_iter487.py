#!/usr/bin/env python3
"""Iteration 487: To nye blogpar (EN + DA) — funnel mod /page-profile (Pro $19/år).

1. website-page-size-checker            -> da/blog/tjek-hvor-stor-din-hjemmeside-er
2. find-all-pages-on-a-website          -> da/blog/find-alle-sider-paa-en-hjemmeside

Moenster fra make_blog_iter481.py. Ingen eksterne soegninger.
"""
import json, re, os, sys, glob
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'tjek-hvor-stor-din-hjemmeside-er',
        'en_slug': 'website-page-size-checker',
        'title': 'Hvor stor er din hjemmeside? Tjek sidestørrelse og vægt (2026)',
        'h1': 'Hvor stor er<br>din hjemmeside?',
        'desc': ('Sådan tjekker du hvor mange KB en webside vejer, hvad der gør den tung, '
                 'og hvordan du finder de billeder og scripts der trækker loadtiden — '
                 'uden at installere noget.'),
        'og_desc': ('Page size checker: se hvor mange kilobyte en webside vejer, find de '
                    'tungeste elementer og få siden til at loade hurtigere. Gratis guide.'),
        'badge': 'PERFORMANCE &middot; GRATIS',
        'subtitle': ('En tung side loader langsomt, rangerer dårligere og taber besøgende '
                     'før de har set indholdet. Her er hvordan du måler vægten — og finder '
                     'de elementer der fylder mest.'),
        'cta1': '<a href="/page-profile" class="btn-primary">Analysér din side gratis &rarr;</a>',
        'cta2': '<a href="#vaegten" class="btn-secondary">Spring til guiden</a>',
        'tool_url': '/page-profile',
        'tool_label': 'Tjek din sidestørrelse nu',
        'hub_badge': 'PERFORMANCE · GRUNDLAG',
        'hub_title': 'Hvor stor er din hjemmeside?',
        'hub_desc': 'Mål sidestørrelsen i KB, find de tunge elementer og få siden til at loade hurtigere.',
        'faq': [
            ("Hvad er en god sidestørrelse?",
             "Under 500 KB er et godt mål for de fleste sider, og under 2 MB er acceptabelt "
             "for billedtunge sider. Gennemsnittet på nettet ligger omkring 2-3 MB, så kommer "
             "du derunder, er du allerede foran de fleste konkurrenter."),
            ("Hvordan tjekker jeg en sides størrelse uden værktøj?",
             "Åbn udviklerværktøjerne (F12), gå i Netværk-fanen og genindlæs siden. Nederst "
             "ser du total overført størrelse. Bemærk at gzip/komprimeret overførsel ofte er "
             "mindre end den ukomprimerede størrelse — begge tal er relevante."),
            ("Gør sidestørrelsen min side langsommere?",
             "Ja, direkte: flere bytes betyder længere downloadtid, især på mobilforbindelser. "
             "Men render-blocking JavaScript, antal serverforespørgsler og serverens svartid "
             "påvirker ofte oplevelsen mindst lige så meget som rå størrelse."),
            ("Hvad fylder typisk mest på en side?",
             "Billeder og video (ofte 60-80 % af vægten), derefter JavaScript-bundter, fonte "
             "og tredjeparts-scripts som chat-widgets og analytics. Start med at komprimere "
             "billeder — det giver næsten altid den største gevinst."),
        ],
        'body': '''
<section class="problem" id="vaegten">
  <div class="container">
    <h2>Sådan måler du vægten på 30 sekunder</h2>
    <ol>
      <li><strong>Netværksfanen:</strong> tryk F12, vælg Netværk, genindlæs siden og læs
      totalen nederst. Det tallet er hele sidens vægt inkl. alle ressourcer.</li>
      <li><strong>Sortér efter størrelse:</strong> klik på Size-kolonnen. De øverste tre
      rækker er næsten altid dit problem.</li>
      <li><strong>Kig efter billeder uden komprimering:</strong> store PNG'er hvor JPG/WebP
      ville være 5-10x mindre.</li>
      <li><strong>Tæl scripts:</strong> hver tredjeparts-widget (chat, analytics,
      heatmaps) koster både vægt og forespørgsler.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">$ curl -s https://ditsite.dk | wc -c        # HTML alene
$ curl -sI https:ditsite.dk/billede.jpg | grep -i content-length</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Hvad vægten egentlig koster</h2>
    <p>Hver ekstra megabyte er længere tid før første indhold — og Google måler det direkte
    via Core Web Vitals (LCP). En side der loader på 1 sekund konverterer typisk 2-3x bedre
    end én der tager 5 sekunder. Vægten rammer også mobilbrugere med begrænsede dataplaner
    hårdest, netop de besøgende der oftest handler lokalt.</p>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Element</th><th>Typisk andel af vægten</th></tr>
      <tr><td>Billeder og video</td><td>60-80 %</td></tr>
      <tr><td>JavaScript</td><td>10-20 %</td></tr>
      <tr><td>Fonte</td><td>2-8 %</td></tr>
      <tr><td>CSS + HTML</td><td>2-5 %</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Få din sides tal &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/tjek-hastighed-uden-lighthouse">tjek hastighed uden Lighthouse</a>,
    <a href="/da/blog/seo-metadata-tjek-hjemmeside">metadata-audit</a> og
    <a href="/da/blog/find-alle-sider-paa-en-hjemmeside">find alle sider på et site</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/tjek-hastighed-uden-lighthouse" lang="da">Hastighed uden Lighthouse</a> &middot; '
                    '<a href="/da/blog/seo-metadata-tjek-hjemmeside" lang="da">Metadata-audit</a> &middot; '
                    '<a href="/da/blog/find-alle-sider-paa-en-hjemmeside" lang="da">Find alle sider</a>'),
    },
    {
        'slug': 'find-alle-sider-paa-en-hjemmeside',
        'en_slug': 'find-all-pages-on-a-website',
        'title': 'Find alle sider på en hjemmeside — 4 metoder der virker (2026)',
        'h1': 'Find alle siderne<br>på et website',
        'desc': ('Sitemap.xml, crawling, søgemaskiner og CMS-eksport: fire måder at liste '
                 'alle sider på et website — og hvilken metode der passer til hvad.'),
        'og_desc': ('How to find every page on a website: sitemap.xml, crawling, search '
                    'operators and CMS exports compared. Free tools included.'),
        'badge': 'SEO &middot; GRATIS',
        'subtitle': ('Du skal lave en SEO-audit, en migrering eller en redesign-plan — men '
                     'hvor mange sider har sitet egentlig, og hvad hedder deres URLs? Fire '
                     'metoder fra hurtigste til grundigste.'),
        'cta1': '<a href="/page-profile" class="btn-primary">Analysér sider gratis &rarr;</a>',
        'cta2': '<a href="#metoder" class="btn-secondary">Se de fire metoder</a>',
        'tool_url': '/page-profile',
        'tool_label': 'Prøv side-analysen nu',
        'hub_badge': 'SEO · GRUNDLAG',
        'hub_title': 'Find alle sider på et website',
        'hub_desc': 'Fire metoder fra sitemap til crawling — og hvornår du skal bruge hvilken.',
        'faq': [
            ("Er sitemap.xml nok til at finde alle sider?",
             "Nej. Et sitemap indeholder kun de sider CMS'et har registreret — typisk 80-95 %. "
             "Gamle sider, landing pages bygget uden for CMS og sider udelukket af plugins "
             "mangler. Brug sitemap som startpunkt, ikke som fuldstændig liste."),
            ("Hvad er forskellen på crawling og et sitemap?",
             "Et sitemap er en selvrapportering; en crawler følger links og finder faktisk "
             "tilgængelige sider. Crawling fanger sider sitemap'et mangler, men kan overse "
             "sider uden indgående links (orphan pages). Kombinér begge for fuldstændighed."),
            ("Kan jeg bruge Google til at finde sider på et domæne?",
             "Ja: søg site:ditsite.dk og bladr igennem, eller brug Search Console's "
             "sideindeks-rapport hvis du ejer sitet. Google viser kun det den har indekseret — "
             "nye eller noindex-sider dukker ikke op."),
            ("Hvordan får jeg metadata for alle siderne på én gang?",
             "Når du har URL-listen, kan du hente titel, beskrivelse og statuskode pr. side "
             "med et værktøj som Page Profile — batch-analyse giver dig en komplet tabel over "
             "manglende meta-tags og fejlsidekoder uden at åbne hver side manuelt."),
        ],
        'body': '''
<section class="problem" id="metoder">
  <div class="container">
    <h2>De fire metoder</h2>
    <ol>
      <li><strong>Sitemap.xml:</strong> åbn ditsite.dk/sitemap.xml. Hurtigst og ofte 80-95 %
      dækkende. Større sites splitter op i sitemap-indekser — følg linkene.</li>
      <li><strong>Søgemaskine:</strong> søg site:ditsite.dk. Viser kun indekserede sider,
      men kræver intet adgang. God som krydstjek.</li>
      <li><strong>Crawler:</strong> lad et værktøj følge alle links internt. Finder sider
      sitemap'et mangler, og opdager samtidig brudte links og redirects-kæder.</li>
      <li><strong>CMS-eksport:</strong> WordPress, Shopify m.fl. kan eksportere en komplet
      sideliste. Den mest autoritative kilde — hvis du har adgang til backend'en.</li>
    </ol>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Når du har listen: kvalitetstjek</h2>
    <p>En sideliste er kun begyndelsen. Det du typisk leder efter er problemerne:
    dublerede titel-tags, manglende meta-beskrivelser, 404'er og redirect-kæder.
    Det arbejdet kalder man en teknisk SEO-audit — og den kan automatiseres:</p>
    <ul>
      <li><strong>Statuskoder:</strong> alle sider skal svare 200. 301'er og 404'er på
      lister betyder døde interne links.</li>
      <li><strong>Titel + description:</strong> unikke, ikke-tomme, 30-60 / 70-160 tegn.</li>
      <li><strong>Canonical:</strong> peger hver side på sig selv?</li>
      <li><strong>Open Graph:</strong> deler siden ordentligt i sociale medier?</li>
    </ul>
    <p>Page Profile tager en URL og viser netop disse felter — Pro-versionen analyserer
    flere sider ad gangen som batch:</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Analysér dine sider &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/tjek-hvor-stor-din-hjemmeside-er">sidestørrelse og vægt</a>,
    <a href="/da/blog/canonisk-url-guide">canonical-tags forklaret</a> og
    <a href="/da/blog/tjek-url-redirect-kaede">redirect-kæder</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/tjek-hvor-stor-din-hjemmeside-er" lang="da">Sidestørrelse</a> &middot; '
                    '<a href="/da/blog/canonisk-url-guide" lang="da">Canonical-guide</a> &middot; '
                    '<a href="/da/blog/tjek-url-redirect-kaede" lang="da">Redirect-kæder</a>'),
    },
]

EN = {
    'website-page-size-checker': {
        'title': 'How Big Is My Web Page? Check Page Size and Weight (2026)',
        'h1': 'How big is your<br>web page?',
        'desc': ('Check how many KB a web page weighs, what makes it heavy, and how to find '
                 'the images and scripts that slow down load time — nothing to install.'),
        'og_desc': ('Free page size checker: see how many kilobytes a page weighs, find the '
                    'heaviest elements and make your site load faster.'),
        'badge': 'PERFORMANCE &middot; FREE',
        'subtitle': ('A heavy page loads slowly, ranks worse and loses visitors before they '
                     "see the content. Here's how to measure the weight — and find the "
                     'elements that add most of it.'),
        'related': ('<a href="/blog/check-website-speed-without-lighthouse">Speed check without Lighthouse</a> &middot; '
                    '<a href="/blog/technical-seo-check-website">Technical SEO audit</a> &middot; '
                    '<a href="/blog/find-all-pages-on-a-website">Find all pages on a site</a>'),
        'faq': [
            ("What is a good page size?",
             "Under 500 KB is a great target for most pages; up to 2 MB is acceptable for "
             "image-heavy ones. The web average sits around 2–3 MB, so coming in below that "
             "already puts you ahead of most competitors."),
            ("How do I check a page's size without a tool?",
             "Open developer tools (F12), switch to the Network tab and reload. The bottom "
             "row shows total transferred size. Note that compressed transfer is usually "
             "smaller than uncompressed size — both numbers matter."),
            ("Does page size actually make my site slower?",
             "Yes, directly: more bytes mean longer download times, especially on mobile "
             "connections. But render-blocking JavaScript, request count and server response "
             "time often affect perceived speed just as much as raw size."),
            ("What typically weighs the most on a page?",
             "Images and video (often 60–80% of weight), then JavaScript bundles, fonts and "
             "third-party scripts like chat widgets and analytics. Start by compressing "
             "images — that's almost always the biggest win."),
        ],
        'body': '''
<section class="problem" id="guide">
  <div class="container">
    <h2>Measure the weight in 30 seconds</h2>
    <ol>
      <li><strong>Network tab:</strong> press F12, select Network, reload, read the total
      at the bottom. That number is the full page including every resource.</li>
      <li><strong>Sort by size:</strong> click the Size column. Your top three rows are
      almost always the problem.</li>
      <li><strong>Look for uncompressed images:</strong> large PNGs where JPEG or WebP
      would be 5–10× smaller.</li>
      <li><strong>Count scripts:</strong> each third-party widget (chat, analytics,
      heatmaps) costs both bytes and extra requests.</li>
    </ol>
<pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">$ curl -s https://yoursite.com | wc -c        # HTML alone
$ curl -sI https://yoursite.com/img.jpg | grep -i content-length</pre>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>What the weight really costs</h2>
    <p>Every extra megabyte delays first content — and Google measures this directly through
    Core Web Vitals (LCP). A page loading in one second typically converts two to three times
    better than one taking five. Weight also hits mobile users on limited data plans hardest,
    precisely the visitors who most often buy locally.</p>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="text-align:left;"><th>Element</th><th>Typical share of weight</th></tr>
      <tr><td>Images and video</td><td>60–80%</td></tr>
      <tr><td>JavaScript</td><td>10–20%</td></tr>
      <tr><td>Fonts</td><td>2–8%</td></tr>
      <tr><td>CSS + HTML</td><td>2–5%</td></tr>
    </table>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Get your page's numbers &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Keep reading</h2>
    <p>Also see:
    <a href="/blog/check-website-speed-without-lighthouse">speed checks without Lighthouse</a>,
    <a href="/blog/website-seo-metadata-audit">metadata audits</a> and
    <a href="/blog/find-all-pages-on-a-website">finding every page on a site</a>.</p>
  </div>
</section>
''',
    },
    'find-all-pages-on-a-website': {
        'title': 'Find All Pages on a Website — 4 Methods That Work (2026)',
        'h1': 'Find every page<br>on a website',
        'desc': ('sitemap.xml, crawling, search engines and CMS exports: four ways to list '
                 'every page on a website — and which method fits which job.'),
        'og_desc': ('Four ways to find all pages on a domain: sitemap.xml, crawling, search '
                    'operators and CMS exports compared. Free tools included.'),
        'badge': 'SEO &middot; FREE',
        'subtitle': ("You need an SEO audit, a migration plan or a redesign scope — but how "
                     'many pages does the site actually have, and what are their URLs? Four '
                     "methods, fastest to most thorough."),
        'related': ('<a href="/blog/website-page-size-checker">Page size checker</a> &middot; '
                    '<a href="/blog/canonical-url-guide">Canonical tags explained</a> &middot; '
                    '<a href="/blog/check-url-redirect-chain">Redirect chains</a>'),
        'faq': [
            ("Is sitemap.xml enough to find every page?",
             "No. A sitemap only contains what the CMS has registered — typically 80–95%. Old "
             "pages, landing pages built outside the CMS and pages excluded by plugins are "
             "missing. Use the sitemap as a starting point, not as the complete list."),
            ("What's the difference between crawling and a sitemap?",
             "A sitemap is self-reported; a crawler follows links and finds pages that are "
             "actually reachable. Crawling catches pages the sitemap misses but can overlook "
             "pages with no internal links (orphan pages). Combine both for completeness."),
            ("Can I use Google to find pages on a domain?",
             "Yes: search site:yoursite.com and page through results, or use Search "
             "Console's page index report if you own the site. Google only shows what it has "
             "indexed — new or noindexed pages won't appear."),
            ("How do I get metadata for all those pages at once?",
             "Once you have the URL list, pull title, description and status code per page "
             "with a tool like Page Profile — batch analysis gives you a table of missing "
             "meta tags and error codes without opening each page manually."),
        ],
        'body': '''
<section class="problem" id="guide">
  <div class="container">
    <h2>The four methods</h2>
    <ol>
      <li><strong>sitemap.xml:</strong> open yoursite.com/sitemap.xml. Fastest, often 80–95%
      coverage. Larger sites split into sitemap indexes — follow the links.</li>
      <li><strong>Search engine:</strong> search site:yoursite.com. Only shows indexed
      pages, but requires no access. Good as a cross-check.</li>
      <li><strong>Crawler:</strong> let a tool follow all internal links. Finds pages the
      sitemap misses, and surfaces broken links and redirect chains along the way.</li>
      <li><strong>CMS export:</strong> WordPress, Shopify and others can export a complete
      page list. The most authoritative source — if you have backend access.</li>
    </ol>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Once you have the list: quality checks</h2>
    <p>A page list is just the beginning. What you're usually hunting for are the problems:
    duplicate title tags, missing meta descriptions, 404s and redirect chains. That work is
    called a technical SEO audit — and much of it can be automated:</p>
    <ul>
      <li><strong>Status codes:</strong> every page should return 200. 301s and 404s on the
      list mean broken internal links.</li>
      <li><strong>Title + description:</strong> unique, non-empty, roughly 30–60 and 70–160
      characters.</li>
      <li><strong>Canonical:</strong> does each page point to itself?</li>
      <li><strong>Open Graph:</strong> will the page share properly on social media?</li>
    </ul>
    <p>Page Profile takes a URL and shows exactly these fields — the Pro version analyses
    multiple pages as a batch:</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Analyse your pages &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Keep reading</h2>
    <p>Also see:
    <a href="/blog/website-page-size-checker">page size and weight</a>,
    <a href="/blog/canonical-url-guide">canonical tags</a> and
    <a href="/blog/check-url-redirect-chain">redirect chains</a>.</p>
  </div>
</section>
''',
    },
}


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
<meta property="og:image" content="{BASE}/deskuptime/og.png">
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
  <p><a href="/da">Forside</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/page-profile">Page Profile</a> &middot; <a href="/da/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.getAttribute('href')||'';var m=h.match(/^\\/(page-profile|deskuptime)(\\.html)?(#[^#]*)?$/);if(!m)return;try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'cta-'+m[1]}})],{{type:'application/json'}}));}}catch(e){{}}}},true);}}catch(e){{}}}})();
</script>
</body>
</html>'''


def build_en(p):
    """EN mirror page, same structure, lang=en."""
    e = EN[p['en_slug']]
    url = f'{BASE}/blog/{p["en_slug"]}'
    ld_article = json.dumps({
        '@context': 'https://schema.org', '@type': 'Article',
        'headline': e['title'], 'description': e['desc'],
        'url': url,
        'datePublished': TODAY, 'dateModified': TODAY,
        'author': {'@type': 'Organization', 'name': 'Hermes Compliance'},
        'publisher': {'@type': 'Organization', 'name': 'Hermes Compliance'},
    }, ensure_ascii=False)
    main_entity = [{"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in e['faq']]
    ld_faq = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage',
                         'mainEntity': main_entity}, ensure_ascii=False)
    faq_cards = '\n'.join(
        f'      <div class="card"><h3>{q}</h3><p>{a}</p></div>' for q, a in e['faq'])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e['title']}</title>
<meta name="description" content="{e['desc']}">
<meta property="og:type" content="article">
<meta property="og:title" content="{e['title']}">
<meta property="og:description" content="{e['og_desc']}">
<meta property="og:image" content="{BASE}/deskuptime/og.png">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{url}">
<link rel="alternate" hreflang="da" href="{BASE}/da/blog/{p['slug']}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{ld_article}</script>
<script type="application/ld+json">{ld_faq}</script>
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{e['badge']}</div>
    <h1>{e['h1']}</h1>
    <p class="subtitle">{e['subtitle']}</p>
    <div class="hero-cta">
      <a href="/page-profile" class="btn-primary">Analyse your page free &rarr;</a>
      <a href="#guide" class="btn-secondary">Jump to the guide</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 5 min read</p>
  </div>
</header>
{e['body']}
<section class="products">
  <div class="container">
    <h2>Frequently asked questions</h2>
    <div class="problem-cards">
{faq_cards}
    </div>
    <div style="text-align:center;margin-top:24px;">
      <a href="/page-profile" class="btn-primary">Try the page analysis now &rarr;</a>
    </div>
  </div>
</section>

<p style="text-align:center;"><a href="/da/blog/{p['slug']}" lang="da">Dansk version af denne guide</a></p>
<div style="text-align:center;margin-top:16px;"><p>Related: {e['related']}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Home</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/page-profile">Page Profile</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.getAttribute('href')||'';var m=h.match(/^\\/(page-profile|deskuptime)(\\.html)?(#[^#]*)?$/);if(!m)return;try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'cta-'+m[1]}})],{{type:'application/json'}}));}}catch(e){{}}}},true);}}catch(e){{}}}})();
</script>
</body>
</html>'''


def update_sitemap(slug_path):
    path = f'{SITE}/sitemap.xml'
    c = open(path).read()
    url = f'{BASE}/{slug_path}'
    if f'<loc>{url}</loc>' in c:
        print(f'sitemap: {slug_path} already present')
        return
    add = (f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod>'
           f'<changefreq>weekly</changefreq><priority>0.8</priority></url>\n')
    c = c.replace('</urlset>', add + '</urlset>')
    open(path, 'w').write(c)
    print(f'sitemap: added {slug_path}')


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


def verify_hub():
    files = {os.path.basename(f)[:-5] for f in glob.glob(f'{SITE}/da/blog/*.html')}
    hub = set(re.findall(r'href="/da/blog/([^"]+)"', open(f'{SITE}/da.html').read()))
    extra = hub - files
    missing = files - hub
    print(f'verify_hub: disk={len(files)} hub={len(hub)} missing_in_hub={sorted(missing)} dead_links={sorted(extra)}')
    assert not extra, f'hubbet linker til ikke-eksisterende sider: {extra}'


def add_hub_card(p):
    path = f'{SITE}/da.html'
    c = open(path).read()
    card_url = f'/da/blog/{p["slug"]}'
    if card_url in c:
        print(f'hub: {p["slug"]} already present')
        return
    card = f'''
      <div class="product-card">
        <div class="product-badge product-badge-secondary">{p['hub_badge']}</div>
        <div class="product-body">
          <h3><a href="{card_url}" style="color:inherit;text-decoration:none;">{p['hub_title']}</a></h3>
          <p class="product-desc">{p['hub_desc']}</p>
          <div class="product-details"><span class="product-meta">📖 5 min</span><span class="product-meta">🇩🇰 Dansk guide</span></div>
          <a href="{card_url}" class="btn-secondary" style="margin-top:12px;">Læs guide →</a>
        </div>
      </div>
'''
    pos = c.rfind('<a href="/da/blog/')
    end = c.find('\n      </div>\n', pos)
    ins = end + len('\n      </div>\n')
    c = c[:ins] + card + c[ins:]
    open(path, 'w').write(c)
    print(f'hub: card added for {p["slug"]}')


def main():
    outs, all_files = [], []
    for p in PAGES:
        da_out = f'{SITE}/da/blog/{p["slug"]}.html'
        en_out = f'{SITE}/blog/{p["en_slug"]}.html'
        assert not os.path.exists(da_out), f'{da_out} exists already'
        assert not os.path.exists(en_out), f'{en_out} exists already'
        for out, page in ((da_out, build_page(p)), (en_out, build_en(p))):
            with open(out, 'w') as f:
                f.write(page)
            blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
            for b in blocks:
                d = json.loads(b)
                assert d['@context'] == 'https://schema.org', d['@context']
            print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')
            update_sitemap('blog/' + os.path.basename(out)[:-5] if '/blog/' in out else 'da/blog/' + p['slug'])
            all_files.append(out)
        add_hub_card(p)
        outs.append(da_out)

    verify_hub()
    broken = check_links(all_files + [f'{SITE}/da.html'])
    if broken:
        print('BROKEN INTERNAL LINKS:')
        for path, link in broken:
            print(f'  {path} -> {link}')
        sys.exit(1)
    print('Internal link check: OK')


if __name__ == '__main__':
    main()
