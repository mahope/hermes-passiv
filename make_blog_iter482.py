#!/usr/bin/env python3
"""Iteration 482: To nye Page Profile-blogpar (EN + DA) + DA-guide-arkiv.

1. website-metadata-audit-checklist        -> da/blog/seo-metadata-tjekliste-2026
2. compare-two-web-pages-seo               -> da/blog/sammenlign-to-sider-seo

Funnel mod /page-profile (Pro $19/år). Mønster fra make_blog_iter481.py.
Ingen eksterne soegninger.
"""
import json, re, os, sys, glob, html
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'seo-metadata-tjekliste-2026',
        'en_slug': 'website-metadata-audit-checklist',
        'title': 'SEO-metadata-tjekliste 2026: sådan auditerer du en hel side selv',
        'h1': 'Metadata-tjekliste<br>for 2026',
        'desc': ('Komplet tjekliste for titel, meta description, canonical, Open Graph og '
                 'struktureret data — og et gratis CLI-værktøj der checker det hele på '
                 'én kommando.'),
        'og_desc': ('Website metadata audit checklist: title tags, meta descriptions, '
                    'canonicals, Open Graph and JSON-LD — check them all with one free CLI command.'),
        'badge': 'SEO &middot; TJEKLISTE',
        'subtitle': ('Titlen er for lang. Description mangler. Canonicalen peger på sig selv '
                     'to gange. Metadata-fejl er de mest almindelige SEO-fejl — her er den '
                     'fulde liste, og hvordan du tjekker den automatisk.'),
        'cta1': '<a href="/page-profile" class="btn-primary">Prøv Page Profile gratis &rarr;</a>',
        'cta2': '<a href="#listen" class="btn-secondary">Spring til tjeklisten</a>',
        'tool_url': '/page-profile',
        'tool_label': 'Auditer dine metadata nu',
        'hub_badge': 'SEO · TJEKLISTE',
        'hub_title': 'SEO-metadata-tjekliste 2026',
        'hub_desc': 'Alt en side skal have af titel, description, canonical og Open Graph — tjekket med én CLI-kommando.',
        'faq': [
            ("Hvilke metadata er vigtigst for SEO i 2026?",
             "Title tag (50-60 tegn), meta description (120-158 tegn), kanonisk URL, "
             "viewport og Open Graph-tags. Title og description styrer visningen i "
             "søgeresultaterne; canonicalen forhindrer duplikeret indhold; OG-tags styrer "
             "delinger på LinkedIn og sociale medier."),
            ("Hvordan tjekker jeg metadata på mange sider hurtigt?",
             "Et CLI-værktøj som Page Profile tager en URL og returnerer hele profilen: "
             "titellængde, description, robots, canonical, OG-tags og struktureret data — "
             "som JSON eller HTML-rapport. Kør det pr. side eller i batch-tilstand over "
             "en URL-liste."),
            ("Hvad sker der hvis meta description mangler?",
             "Google genererer selv et uddrag fra sidens indhold — ofte dårligere end en "
             "skrevet description, men siden rangerer stadig. Manglende title tag er "
             "alvorligere: Google omskriver titlen fra overskrifter, hvilket typisk koster "
             "klikfrekvens."),
            ("Skal hver side have unik metadata?",
             "Ja. Identiske titles på to sider får Google til at vælge selv, hvilken der "
             "skal vises. En audit der sammenligner sider mod hinanden (fx "
             "sammenligningstilstand i Page Profile) fanger dubletter med det samme."),
        ],
        'body': '''
<section class="problem" id="listen">
  <div class="container">
    <h2>Tjeklisten: 12 punkter pr. side</h2>
    <ol>
      <li><strong>Title tag:</strong> findes, unik, 30-60 tegn, primært søgeord først.</li>
      <li><strong>Meta description:</strong> findes, 120-158 tegn, har et klart tilbud.</li>
      <li><strong>Canonical:</strong> én canonical, absolut URL, peger på sig selv (eller
      den foretrukne version).</li>
      <li><strong>Viewport:</strong> <code>width=device-width, initial-scale=1</code> — uden
      den ser mobilvisningen forkert ud.</li>
      <li><strong>Open Graph:</strong> og:title, og:description, og:image (1200×630) og
      og:url.</li>
      <li><strong>Twitter Card:</strong> summary_large_image med gyldigt billede.</li>
      <li><strong>Robots:</strong> ingen utilsigtet <code>noindex</code> eller
      <code>nofollow</code>.</li>
      <li><strong>Sprog:</strong> korrekt <code>&lt;html lang&gt;</code> og hreflang ved
      flersprogede sider.</li>
      <li><strong>Struktureret data:</strong> gyldig JSON-LD (Organization, Article,
      FAQPage efter indholdstype).</li>
      <li><strong>Overskriftshierarki:</strong> én H1, logisk H2/H3-struktur.</li>
      <li><strong>Billeder:</strong> alt-tekst på alle indholdsbilleder.</li>
      <li><strong>Dubletter:</strong> ingen to sider med identisk title eller description.</li>
    </ol>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Tjek alle 12 punkter med én kommando</h2>
    <p>Manuelt tjek tager 10-15 minutter pr. side og bliver glemt efter første redesign.
    Page Profile læser siden og scorer hvert punkt — som terminaloutput, JSON eller en
    HTML-rapport du kan sende til en kunde:</p>
    <pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">$ npx page-profile https://ditdomaene.dk/side
title       "Side titel her"          54 chars   OK
description 148 chars                            OK
canonical   https://ditdomaene.dk/side           OK
og:image    present (1200x630)                   OK
score       11/12                                WARN</pre>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Prøv det gratis i browseren &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/teknisk-seo-tjek-hjemmeside">teknisk SEO-tjek af hjemmesiden</a>,
    <a href="/da/blog/meta-tjekker">meta-tjekker guide</a> og
    <a href="/da/blog/canonisk-url-guide">canoniske URLs forklaret</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/teknisk-seo-tjek-hjemmeside" lang="da">Teknisk SEO-tjek</a> &middot; '
                    '<a href="/da/blog/meta-tjekker" lang="da">Meta-tjekker</a> &middot; '
                    '<a href="/da/blog/sammenlign-to-sider-seo" lang="da">Sammenlign to sider</a>'),
    },
    {
        'slug': 'sammenlign-to-sider-seo',
        'en_slug': 'compare-two-web-pages-seo',
        'title': 'Sammenlign to websider trin for trin — find forskellene før din konkurrent gør',
        'h1': 'Sammenlign to<br>sider side om side',
        'h1b': True,
        'desc': ('Sådan sammenligner du to websiders metadata, struktureret data og tekniske '
                 'SEO — før og efter et redesign, eller din side mod konkurrentens. Gratis '
                 'værktøj.'),
        'og_desc': ('Compare two web pages side by side: metadata, structured data and technical '
                    'SEO differences — before/after redesign or you vs a competitor. Free tool.'),
        'badge': 'SEO &middot; SAMMENLIGNING',
        'subtitle': ('Før/efter-et redesign: hvad ændrede sig egentlig? Eller din landingsside '
                     'mod konkurrentens: hvorfor rangerer de højere? Sammenligning af to '
                     'URLer svarer på begge dele på under et minut.'),
        'cta1': '<a href="/page-profile" class="btn-primary">Sammenlign to sider gratis &rarr;</a>',
        'cta2': '<a href="#hvornaar" class="btn-secondary">Hvornår giver det mening?</a>',
        'tool_url': '/page-profile',
        'tool_label': 'Kør en side-sammenligning nu',
        'hub_badge': 'SEO · SAMMENLIGNING',
        'hub_title': 'Sammenlign to websiders SEO',
        'hub_desc': 'Se forskellene i metadata, struktureret data og teknisk SEO mellem to URLs — før/efter redesign eller dig mod konkurrenten.',
        'faq': [
            ("Hvorfor sammenligne min side med en konkurrent?",
             "Fordi rangering er relativt. Når en konkurrent rangerer højere, ligger "
             "forskellen ofte i synlige ting: titlens søgeord, descriptionens klik-opfordring, "
             "manglende FAQ-schema eller en renere canonical-struktur. En side-by-side "
             "profil viser forskellene uden gætteri."),
            ("Hvad er den bedste måde at tjekke et redesign på?",
             "Tag en profil af hver vigtig side FØR lanceringen og gem den som JSON. Efter "
             "lanceringen kører du den igen og sammenligner. Det fanger tabte meta-tags, "
             "ændrede canonicals og ødelagt struktureret data — de klassiske "
             "redesign-taber der ellers opdages måneder senere i Search Console."),
            ("Kan jeg sammenligne flere sider end to?",
             "Ja. Batch-tilstand tager en liste af URLs og profilerer dem alle i ét kørsel — "
             "fx hele dit top-20 af landingssider. Output som HTML-rapport gør resultatet "
             "klar til at sende til en kunde eller kollega."),
            ("Kræver det installation?",
             "Nej. Du kan indsætte to URLs direkte i browser-værktøjet på page-profile-siden. "
             "Vil du automatisere det i CI, findes også en CLI-version og et gratis JSON-API."),
        ],
        'body': '''
<section class="problem" id="hvornaar">
  <div class="container">
    <h2>Tre situationer hvor sammenligning betaler sig</h2>
    <ol>
      <li><strong>Før/efter redesign:</strong> gem profiler af alle templates før
      lanceringsdagen. Efter: sammenlign. Tabte metadata opdages samme dag — ikke tre
      måneder senere via faldende trafik.</li>
      <li><strong>Dig mod konkurrenten:</strong> profiler deres landingsside og din. Se
      præcis hvad de har, som du mangler — schema, OG-billede, description-længde.</li>
      <li><strong>Konsolidering af duplikatindhold:</strong> to sider om emnet? Sammenlign
      canonicals og titles og beslut hvilken der skal være den kanoniske.</li>
    </ol>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Sådan gør du med Page Profile</h2>
    <ol>
      <li>Åbn <a href="/page-profile">page-profile</a> og indsæt URL #1 — du får hele
      metadata-profilen.</li>
      <li>Indsæt URL #2 i sammenligningstilstand. Værktøjet viser forskellene felt for
      felt: titler, descriptions, canonicals, Open Graph og struktureret data.</li>
      <li>Eksportér som HTML-rapport, hvis resultatet skal deles med en kunde.</li>
    </ol>
    <p>I CLI fungerer det samme med <code>npx page-profile &lt;url1&gt; &lt;url2&gt;</code>,
    og JSON-API'et lader dig bygge sammenligningen ind i din egen CI:</p>
    <pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">$ curl -s "https://hermes-passiv.pages.dev/api/profile?url=https://a.dk" | jq .score
$ curl -s "https://hermes-passiv.pages.dev/api/profile?url=https://b.dk" | jq .score</pre>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Start en sammenligning &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Læs videre</h2>
    <p>Læs også:
    <a href="/da/blog/seo-metadata-tjekliste-2026">den fulde metadata-tjekliste</a>,
    <a href="/da/blog/tjek-url-redirect-kaede">tjek redirect-kæder</a> og
    <a href="/da/blog/hreflang-guide-da">hreflang-guide på dansk</a>.</p>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/seo-metadata-tjekliste-2026" lang="da">Metadata-tjekliste</a> &middot; '
                    '<a href="/da/blog/tjek-url-redirect-kaede" lang="da">Redirect-kæder</a> &middot; '
                    '<a href="/da/blog/hreflang-guide-da" lang="da">Hreflang-guide</a>'),
    },
]

EN = {
    'website-metadata-audit-checklist': {
        'title': 'Website Metadata Audit Checklist (2026): Audit Any Page Yourself',
        'h1': 'The metadata audit<br>checklist for 2026',
        'desc': ('A complete checklist for title tags, meta descriptions, canonicals, Open '
                 'Graph and structured data — plus a free CLI tool that checks all of it in '
                 'one command.'),
        'og_desc': ('Website metadata audit checklist: title tags, meta descriptions, '
                    'canonicals, Open Graph and JSON-LD — check them all with one free CLI command.'),
        'badge': 'SEO &middot; CHECKLIST',
        'subtitle': ('The title is too long. The description is missing. The canonical points '
                     'at itself twice. Metadata errors are the most common SEO mistakes on the '
                     'web — here\'s the full list, and how to check it automatically.'),
        'related': ('<a href="/blog/technical-seo-check-website">Technical SEO check</a> &middot; '
                    '<a href="/blog/meta-tag-checker">Meta tag checker</a> &middot; '
                    '<a href="/blog/compare-two-web-pages-seo">Compare two pages</a>'),
        'faq': [
            ("Which metadata matters most for SEO in 2026?",
             "Title tag (50–60 characters), meta description (120–158 characters), canonical "
             "URL, viewport and Open Graph tags. Title and description control how your page "
             "appears in search results; the canonical prevents duplicate-content issues; OG "
             "tags control link previews on LinkedIn and social platforms."),
            ("How do I check metadata across many pages quickly?",
             "A CLI tool like Page Profile takes a URL and returns the full profile: title "
             "length, description, robots, canonical, OG tags and structured data — as JSON "
             "or an HTML report. Run it per page, or use batch mode over a list of URLs."),
            ("What happens if the meta description is missing?",
             "Google generates its own snippet from the page content — usually worse than a "
             "written one, but the page still ranks. A missing title tag is more serious: "
             "Google rewrites the title from headings, which typically costs click-through "
             "rate."),
            ("Should every page have unique metadata?",
             "Yes. Identical titles on two pages force Google to choose which to show. An "
             "audit that compares pages against each other (like comparison mode in Page "
             "Profile) catches duplicates immediately."),
        ],
        'body': '''
<section class="problem" id="guide">
  <div class="container">
    <h2>The checklist: 12 points per page</h2>
    <ol>
      <li><strong>Title tag:</strong> present, unique, 30–60 characters, primary keyword first.</li>
      <li><strong>Meta description:</strong> present, 120–158 characters, has a clear offer.</li>
      <li><strong>Canonical:</strong> exactly one, absolute URL, self-referencing (or pointing
      at the preferred version).</li>
      <li><strong>Viewport:</strong> <code>width=device-width, initial-scale=1</code> — without
      it mobile rendering breaks.</li>
      <li><strong>Open Graph:</strong> og:title, og:description, og:image (1200×630) and
      og:url.</li>
      <li><strong>Twitter Card:</strong> summary_large_image with a valid image.</li>
      <li><strong>Robots:</strong> no accidental <code>noindex</code> or <code>nofollow</code>.</li>
      <li><strong>Language:</strong> correct <code>&lt;html lang&gt;</code> plus hreflang on
      multilingual sites.</li>
      <li><strong>Structured data:</strong> valid JSON-LD (Organization, Article, FAQPage per
      content type).</li>
      <li><strong>Heading hierarchy:</strong> one H1, logical H2/H3 structure.</li>
      <li><strong>Images:</strong> alt text on every content image.</li>
      <li><strong>Duplicates:</strong> no two pages sharing identical titles or descriptions.</li>
    </ol>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>Check all 12 points with one command</h2>
    <p>A manual check takes 10–15 minutes per page and gets forgotten after the next
    redesign. Page Profile reads the page and scores every point — as terminal output,
    JSON, or an HTML report you can hand to a client:</p>
    <pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">$ npx page-profile https://yoursite.com/page
title       "Your page title here"    54 chars   OK
description 148 chars                            OK
canonical   https://yoursite.com/page            OK
og:image    present (1200x630)                   OK
score       11/12                                WARN</pre>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Try it free in the browser &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Read more</h2>
    <p>Also:
    <a href="/blog/technical-seo-check-website">technical SEO checks</a>,
    <a href="/blog/meta-tag-checker">the meta tag checker</a> and
    <a href="/blog/canonical-url-guide">canonical URLs explained</a>.</p>
  </div>
</section>
''',
    },
    'compare-two-web-pages-seo': {
        'title': 'Compare Two Web Pages Side by Side — Spot the Differences First',
        'h1': 'Compare two pages<br>side by side',
        'desc': ('How to compare two web pages\' metadata, structured data and technical SEO — '
                 'before and after a redesign, or your page against a competitor. Free tool.'),
        'og_desc': ('Compare two web pages side by side: metadata, structured data and technical '
                    'SEO differences — before/after redesign or you vs a competitor. Free tool.'),
        'badge': 'SEO &middot; COMPARISON',
        'subtitle': ('Before-and-after a redesign: what actually changed? Or your landing page '
                     'versus a competitor\'s: why do they rank higher? Comparing two URLs answers '
                     'both in under a minute.'),
        'related': ('<a href="/blog/website-metadata-audit-checklist">Metadata audit checklist</a> &middot; '
                    '<a href="/blog/check-url-redirect-chain">Redirect chain checks</a> &middot; '
                    '<a href="/blog/hreflang-guide">Hreflang guide</a>'),
        'faq': [
            ("Why compare my page against a competitor's?",
             "Because ranking is relative. When a competitor outranks you, the difference is "
             "often visible: keywords in the title, a stronger call to action in the "
             "description, missing FAQ schema, or a cleaner canonical structure. A side-by-side "
             "profile shows the gaps without guesswork."),
            ("What's the best way to verify a redesign didn't break anything?",
             "Profile every important template BEFORE launch and save it as JSON. After launch, "
             "profile again and compare. This catches lost meta tags, changed canonicals and "
             "broken structured data — the classic redesign losses otherwise discovered months "
             "later via dropping traffic in Search Console."),
            ("Can I compare more than two pages?",
             "Yes. Batch mode takes a list of URLs and profiles all of them in one run — say, "
             "your top 20 landing pages. Export as an HTML report when the results need to go "
             "to a client or colleague."),
            ("Do I need to install anything?",
             "No. Paste two URLs directly into the browser tool on the page-profile page. For "
             "CI automation there's also a CLI version and a free JSON API."),
        ],
        'body': '''
<section class="problem" id="guide">
  <div class="container">
    <h2>Three situations where comparing pays off</h2>
    <ol>
      <li><strong>Before/after a redesign:</strong> profile every template before launch day
      and save it. Afterwards: compare. Lost metadata gets caught the same day — not three
      months later via falling traffic.</li>
      <li><strong>You vs a competitor:</strong> profile their landing page and yours. See
      exactly what they have that you lack — schema, an OG image, description length.</li>
      <li><strong>Consolidating duplicate content:</strong> two pages on the topic? Compare
      canonicals and titles and decide which should be the canonical one.</li>
    </ol>
  </div>
</section>

<section class="problem">
  <div class="container">
    <h2>How to do it with Page Profile</h2>
    <ol>
      <li>Open <a href="/page-profile">page-profile</a> and paste in URL #1 — you get the full
      metadata profile.</li>
      <li>Paste URL #2 into comparison mode. The tool shows the differences field by field:
      titles, descriptions, canonicals, Open Graph and structured data.</li>
      <li>Export as an HTML report if the result needs to be shared with a client.</li>
    </ol>
    <p>In the CLI it works the same way with <code>npx page-profile &lt;url1&gt; &lt;url2&gt;</code>,
    and the JSON API lets you build comparisons into your own CI:</p>
    <pre style="background:#0f172a;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.9rem;">$ curl -s "https://hermes-passiv.pages.dev/api/profile?url=https://a.com" | jq .score
$ curl -s "https://hermes-passiv.pages.dev/api/profile?url=https://b.com" | jq .score</pre>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Run a comparison now &rarr;</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Read more</h2>
    <p>Also:
    <a href="/blog/website-metadata-audit-checklist">the full metadata checklist</a>,
    <a href="/blog/check-url-redirect-chain">checking redirect chains</a> and
    <a href="/blog/hreflang-guide">the hreflang guide</a>.</p>
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
<meta property="og:image" content="{BASE}/page-profile/og.png">
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
  <p><a href="/da">Forside</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/page-profile">Page Profile</a> &middot; <a href="/da/#guides">Guides</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});document.addEventListener('click',function(ev){{var a=ev.target&&ev.target.closest?ev.target.closest('a[href]'):null;if(!a)return;var h=a.href;if(h&&h.indexOf('chromewebstore.google.com')>-1){{try{{navigator.sendBeacon('/api/track',new Blob([JSON.stringify({{path:p,event:'store-click'}})],{{type:'application/json'}}));}}catch(e){{}}}}}},true);}}catch(e){{}}}})();
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
<meta property="og:image" content="{BASE}/page-profile/og.png">
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
      <a href="/page-profile" class="btn-primary">Try Page Profile free &rarr;</a>
      <a href="#guide" class="btn-secondary">Jump to the guide</a>
    </div>
    <p class="hero-note">Updated August 2026 &middot; 6 min read</p>
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
      <a href="/page-profile" class="btn-primary">Audit your metadata now &rarr;</a>
    </div>
  </div>
</section>

<p style="text-align:center;"><a href="/da/blog/{p['slug']}" lang="da">Danish version of this guide</a></p>
<div style="text-align:center;margin-top:16px;"><p>Related: {e['related']}</p></div>
<footer style="padding:32px 24px;">
  <p><a href="/">Home</a> &middot; <a href="/free-tools">Free tools</a> &middot; <a href="/page-profile">Page Profile</a> &middot; <a href="/#blog">Blog</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
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
        htmlc = open(path).read()
        for m in sorted(set(re.findall(r'href="(/[^"#]*?)"', htmlc))):
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


def add_blog_index(p):
    path = f'{SITE}/blog/index.html'
    c = open(path).read()
    li = (f'<li style="margin-bottom:20px"><a href="/blog/{p["en_slug"]}" '
          f'style="color:var(--color-accent);font-weight:600;text-decoration:none;'
          f'font-size:1.02rem">{html.escape(EN[p["en_slug"]]["title"])}</a><br>'
          f'<span style="color:var(--color-text-muted);font-size:0.88rem">'
          f'{html.escape(p["hub_desc"])}</span></li>\n')
    if f'/blog/{p["en_slug"]}"' in c:
        print(f'index: {p["en_slug"]} already present')
        return
    pos = c.find('<h2>Dev Tools &amp; Guides</h2>')
    if pos == -1:
        pos = c.find('<h2>Dev Tools & Guides</h2>')
    ul = c.find('</ul>', pos)
    c = c[:ul] + li + c[ul:]
    open(path, 'w').write(c)
    print(f'index: added {p["en_slug"]}')


def build_da_archive():
    """Generate /da/guides listing ALL DA blog posts, grouped by category."""
    out = f'{SITE}/da/guides.html'
    cats = {
        'Tilgængelighed & EAA': ['tilgaeng', 'eaa', 'wcag', 'bitv', 'tilgaengelighedserklaering', 'kontrast'],
        'GDPR & Cookies': ['gdpr', 'dbbaftale', 'cookie'],
        'NIS2': ['nis2'],
        'SEO & Website Health': ['seo', 'meta-', 'open-graph', 'hreflang', 'canonisk', 'redirect',
                                  'ssl', 'hastighed', 'site-health', 'http-headere', 'overvaag',
                                  'faa-besked', 'tjek-om-hjemmeside'],
        'Tekst & Tabeller': ['kopier', 'kopier-tabel', 'markdown', 'tabel', 'tekstvaerktoejer',
                              'indsæt', 'indsaet', 'chatgpt', 'url-til-markdown', 'html-tabel'],
        'Dev Tools': ['bugrapporter', 'fejlrapport', 'compliance-tjek-github-action', 'roegtest',
                       'release-integrity', 'zip-foer-release', 'ci-pipeline'],
    }
    files = sorted(glob.glob(f'{SITE}/da/blog/*.html'))
    sections = {}
    used = set()
    for cat, keys in cats.items():
        items = []
        for f in files:
            base = os.path.basename(f)[:-5]
            if base in used:
                continue
            if any(k in base for k in keys):
                title = re.search(r'<title>([^<]*)</title>', open(f).read())
                t = html.unescape(title.group(1)) if title else base
                t = re.sub(r'\s*\(.*?2026?\)\s*$', '', t).strip()
                items.append((base, t))
                used.add(base)
        if items:
            sections[cat] = items
    rest = [(os.path.basename(f)[:-5],
             html.unescape(re.search(r'<title>([^<]*)</title>', open(f).read()).group(1)))
            for f in files if os.path.basename(f)[:-5] not in used]
    if rest:
        sections['Andre guides'] = rest

    total = sum(len(v) for v in sections.values())
    body = ''
    for cat, items in sections.items():
        lis = '\n'.join(
            f'<li style="margin-bottom:10px"><a href="/da/blog/{slug}">{html.escape(t)}</a></li>'
            for slug, t in items)
        body += (f'<section class="problem"><div class="container"><h2>{cat} '
                 f'({len(items)})</h2><ul style="list-style:none;padding-left:0">{lis}</ul>'
                 f'</div></section>\n')

    return total, f'''<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Alle danske guides ({total}) — compliance, SEO & dev-værktøjer</title>
<meta name="description" content="Komplet arkiv over alle {total} danske guides: EAA og tilgængelighed, GDPR, NIS2, SEO-metadata og dev-værktøjer. Alt gratis, intet kræver tilmelding.">
<meta property="og:title" content="Alle danske guides ({total})">
<meta property="og:description" content="Komplet arkiv: {total} danske guides om compliance, SEO og dev-værktøjer. Gratis.">
<meta property="og:url" content="{BASE}/da/guides">
<link rel="canonical" href="{BASE}/da/guides">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">GUIDES &middot; ARKIV</div>
    <h1>Alle {total}<br>danske guides</h1>
    <p class="subtitle">Det komplette arkiv: hver eneste guide på dansk — tilgængelighed, GDPR,
    NIS2, SEO og udviklerværktøjer. Alt gratis, intet kræver tilmelding.</p>
    <div class="hero-cta">
      <a href="/da/#tools" class="btn-primary">Se de gratis værktøjer &rarr;</a>
    </div>
  </div>
</header>
{body}
<footer style="padding:32px 24px;">
  <p><a href="/da">Forside</a> &middot; <a href="/free-tools">Gratis værktøjer</a> &middot; <a href="/deskuptime">DeskUptime</a> &middot; <a href="/page-profile">Page Profile</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>'''


def verify_hub():
    files = {os.path.basename(f)[:-5] for f in glob.glob(f'{SITE}/da/blog/*.html')}
    hub = set(re.findall(r'href="/da/blog/([^"]+)"', open(f'{SITE}/da.html').read()))
    extra = hub - files
    print(f'verify_hub: disk={len(files)} hub={len(hub)} dead_links={sorted(extra)}')
    assert not extra, f'hubbet linker til ikke-eksisterende sider: {extra}'


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
            update_sitemap(('blog/' + p['en_slug']) if 'blog/en' not in out and '.html' in out and '/da/' not in out else 'da/blog/' + p['slug'])
            all_files.append(out)
        add_hub_card(p)
        add_blog_index(p)
        outs.append(da_out)

    total, archive_html = build_da_archive()
    with open(f'{SITE}/da/guides.html', 'w') as f:
        f.write(archive_html)
    print(f'da/guides.html written: {total} guides listed')
    update_sitemap('da/guides')
    all_files.append(f'{SITE}/da/guides.html')
    all_files += [f'{SITE}/da.html', f'{SITE}/blog/index.html']

    verify_hub()
    broken = check_links(all_files)
    if broken:
        print('BROKEN INTERNAL LINKS:')
        for path, link in broken:
            print(f'  {path} -> {link}')
        sys.exit(1)
    print('Internal link check: OK')


if __name__ == '__main__':
    main()
