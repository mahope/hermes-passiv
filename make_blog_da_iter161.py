#!/usr/bin/env python3
"""Iteration 161: Two more Danish blog pendants.

- site/da/blog/meta-tjekker.html            (pendant of EN meta-tag-checker)
- site/da/blog/gratis-tilgaengelighedsvaerktoejer.html (pendant of EN free-accessibility-testing-tools)
- Cross-links both ways + hreflang on EN posts, JSON-LD validated,
  sitemap updated, internal link check.
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

PAGES = [
    {
        'slug': 'meta-tjekker',
        'en_slug': 'meta-tag-checker',
        'title': 'Meta-tjekker — se hvilke meta-tags crawlers ser (gratis)',
        'h1': 'Meta-Tjekker<br>Se Hvad Crawlers Ser',
        'desc': ('Indsæt en URL og få et komplet billede af sidens title, description, '
                 'Open Graph, Twitter Cards, robots-direktiver og kanoniske URL — '
                 'gratis og uden tilmelding.'),
        'og_desc': ('Tjek enhver sides meta-tags gratis: title, description, Open Graph, '
                    'robots og canonical — ét indtryk, fuld rapport.'),
        'badge': 'SEO &middot; GRATIS VÆRKTØJ',
        'subtitle': ('Title, description og sociale kort bestemmer hvordan din side ser ud '
                     'i søgeresultater og på sociale medier. Se præcis hvad crawlers og '
                     'delinger ser — på fem sekunder.'),
        'cta1': '<a href="/page-profile" class="btn-primary">Tjek meta-tags nu &rarr;</a>',
        'cta2': '<a href="#hvad" class="btn-secondary">Hvad du kan tjekke</a>',
        'faq': [
            ("Hvilke meta-tags betyder mest for SEO?",
             "Title-tag og meta description er de vigtigste: de vises i søgeresultaterne "
             "og påvirker både placering og klikrate. Derefter kommer robots (må siden "
             "indekseres?), canonical URL (hvilken version tæller?) og Open Graph-tags "
             "(hvordan linket ser ud når det deles)."),
            ("Hvor lang skal en meta description være?",
             "Ca. 140–160 tegn. Længere beskrivelser klippes af med tre prikker i Google. "
             "Skriv det vigtigste først, og gør beskrivelsen til en grund til at klikke — "
             "ikke en liste med nøgleord."),
            ("Hvad er forskellen på Open Graph og Twitter Cards?",
             "Begge styrer hvordan dit link ser ud når det deles. Open Graph (og:title, "
             "og:description, og:image) bruges af Facebook, LinkedIn og de fleste platforme; "
             "Twitter/X læser også Open Graph men kan overstyres af twitter:card-tags. Har "
             "du kun ét sæt, så vælg Open Graph."),
            ("Er værktøjet gratis?",
             "Ja. page-profile giver dig fuld meta-rapport for enhver URL uden konto eller "
             "grænser. Skal hele sitet gennemgås — inklusive overskrifter, alt-tekster og "
             "kontrast — brug den gratis Accessibility Scanner på /scan-da."),
        ],
        'body': '''
<section class="problem" id="hvorfor">
  <div class="container">
    <h2>Problemet: din side ses gennem meta-tags</h2>
    <p>Google viser din <strong>title</strong> og <strong>meta description</strong>.
    Facebook, LinkedIn og X viser <strong>Open Graph</strong>-tags når nogen deler dit
    link. Browserfanen viser title. Hvis tagsne mangler, er for lange eller duplikerede,
    taber du klik — ofte uden at vide det.</p>
    <div class="problem-cards">
      <div class="card"><h3>🔍 Se som crawler</h3><p>Du får præcis hvad maskinerne ser — ikke hvad CMS-et påstår at have udsendt. Duplikerede titler, manglende descriptions og forkerte canonicals bliver synlige med det samme.</p></div>
      <div class="card"><h3>📱 Sociale kort</h3><p>og:title, og:description og og:image afgør om delt linket ser professionelt eller som en nøgen URL. Test før du deler.</p></div>
      <div class="card"><h3>🤖 Robots &amp; canonical</h3><p>Er siden ved et uheld blokeret for indeksering? Peger canonical på den forkerte URL? Det er typiske årsager til at sider forsvinder fra Google.</p></div>
    </div>
  </div>
</section>

<section class="products" id="hvad">
  <div class="container">
    <h2>Sådan gør du</h2>
    <ol>
      <li>Åbn den gratis <a href="/page-profile" style="color:var(--color-accent);">page-profile meta-tjekker</a>.</li>
      <li>Indsæt sidens URL — fx din forside eller et vigtigt landing page.</li>
      <li>Læs rapporten: title-længde, description, Open Graph, Twitter Card, robots-direktiv og canonical URL.</li>
      <li>Ret det der mangler i dit CMS, og kør tjekket igen.</li>
    </ol>
    <p>Tjekliste: én unik title pr. side (ca. 50–60 tegn) &middot; én description på
    140–160 tegn &middot; gyldig canonical der peger på siden selv &middot; ingen
    <code>noindex</code> på sider der skal findes &middot; Open Graph-billede mindst
    1200&times;630 px.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Fra enkelt side til helt site</h2>
    <p>Meta-tjekkeren går én side i dybden. Skal et helt site screenes for tekniske
    fejl — meta-tags, overskriftshierarki, billeder uden alt-tekst, kontrast og
    tastaturnavigation — brug den gratis <a href="/scan-da" style="color:var(--color-accent);">Accessibility Scanner</a>
    eller læs guiden til <a href="/blog/teknisk-seo-tjek-hjemmeside" lang="en" style="color:var(--color-accent);">teknisk SEO-tjek af hjemmesider</a>.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/page-profile" class="btn-primary">Tjek dine meta-tags gratis &rarr;</a>
    </div>
  </div>
</section>
''',
        'related': ('<a href="/da/blog/open-graph-tjekker" lang="da">Open Graph-tjekker-guide</a> &middot; '
                    '<a href="/blog/teknisk-seo-tjek-hjemmeside" lang="en">Teknisk SEO-tjek (engelsk)</a> &middot; '
                    '<a href="/da/blog/ren-tekst-fra-hjemmeside" lang="da">Ren tekst fra hjemmeside</a>'),
        # extra CTA target used in FAQ footer button differs from template default;
        # handled via cta_tool below
        'tool_url': '/page-profile',
        'tool_label': 'Prøv meta-tjekkeren gratis',
    },
    {
        'slug': 'gratis-tilgaengelighedsvaerktoejer',
        'en_slug': 'free-accessibility-testing-tools',
        'title': 'Gratis tilgængelighedsværktøjer 2026 — hvad fanger hver af dem?',
        'h1': 'Gratis Tilgængeligheds<br>Værktøjer — Oversigt 2026',
        'desc': ('Sammenligning af de bedste gratis tilgængelighedsværktøjer: WAVE, axe '
                 'DevTools, Lighthouse, Accessibility Insights, skærmlæsere og automatiske '
                 'scannere — hvad hver enkelt fanger, og hvad ingen af dem fanger.'),
        'og_desc': ('WAVE, axe DevTools, Lighthouse og flere: hvad fanger hvert gratis '
                    'tilgængelighedsværktøj reelt — og hvorfor automatisering kun dækker '
                    'en tredjedel?'),
        'badge': 'TILGÆNGELIGHED &middot; VÆRKTØJSOVERSIGT',
        'subtitle': ('Automatiske værktøjer fanger omkring en tredjedel af WCAG-problemerne '
                     '— men de rigtige tre fanger det meste af det der tæller. Her er hvad '
                     'hver af dem faktisk kan, og hvad du stadig selv skal teste.'),
        'cta1': '<a href="/scan" class="btn-primary">Scan din side nu &rarr;</a>',
        'cta2': '<a href="#oversigt" class="btn-secondary">Se oversigten</a>',
        'faq': [
            ("Hvad er det bedste gratis tilgængelighedsværktøj?",
             "Det afhænger af opgaven. WAVE er det hurtigste visuelle overblik over en "
             "enkelt side, axe DevTools er standarden i dev-værktøjer og CI-pipelines, og "
             "Lighthouse giver en samlet score direkte i Chrome. Brug to af dem — de fanger "
             "delvis overlappende fejl."),
            ("Kan automatiske tests erstatte manuel test?",
             "Nej. Automatiske scannere fanger typisk 25–35 % af WCAG-problemerne. Alt med "
             "kontekst kræver et menneske: om alt-teksten er fornuftig, om rækkefølgen giver "
             "mening med tastatur, om formular-fejlbeskeder er forståelige, og om sidens "
             "struktur fungerer med skærmlæser."),
            ("Hvordan tester jeg med en skærmlæser uden at købe noget?",
             "Windows: NVDA er gratis og open source (VoiceOver følger med macOS og iOS). "
             "Lær tre grundkommandoer: pil ned for at læse videre, Tab for at hoppe mellem "
             "interaktive elementer, og headings-navigation (H-tasten i NVDA). Navigerer du "
             "selv rundt i din side på under to minutter, passer strukturen nok."),
            ("Hvad med EAA — er et automatisk tjek nok til loven?",
             "Nej. Europas tilgængelighedslov stiller WCAG 2.1 AA-krav, og opfyldelse "
             "dokumenteres ikke alene med et scanner-resultat. Brug scannere til at finde de "
             "tekniske fejl hurtigt, og supér med manuel tastatur- og skærmlæsertest. Se også "
             "guiden om EAA-frister."),
        ],
        'body': '''
<section class="products" id="oversigt">
  <div class="container">
    <h2>Oversigten: seks gratis værktøjer</h2>
    <div class="problem-cards">
      <div class="card"><h3>1️⃣ WAVE (browserudvidelse)</h3><p>Viser fejl <em>på selve siden</em> med ikoner: manglende alt-tekst, lav kontrast, brudte ARIA-attributter, tomme knapper. Bedst til at se problemet i sin kontekst. Gratis fra WebAIM.</p></div>
      <div class="card"><h3>2️⃣ axe DevTools</h3><p>Udviklernes standard. Kører i browserens devtools, giver regelmæssige, falsk-positive-fattige resultater og har en gratis kerne. Kan bygges direkte ind i automatiserede tests (axe-core).</p></div>
      <div class="card"><h3>3️⃣ Lighthouse</h3><p>Bygget ind i Chrome. Én tilgængeligheds-score plus konkrete fund: kontrast, ARIA, labels, navne på knapper. Godt første tjek — men kun ét snapshot af én side.</p></div>
      <div class="card"><h3>4️⃣ Accessibility Insights for Web</h3><p>Microsofts gratis værktøj. FastPass gennemgår de mest kritiske automatiske tjek, og Assessment guer dig trin for trin igennem manuelle WCAG-kriterier.</p></div>
      <div class="card"><h3>5️⃣ Skærmlæsere (NVDA/VoiceOver)</h3><p>Den eneste måde at opleve sitet som blinde brugere gør. NVDA er gratis på Windows; VoiceOver følger med macOS/iOS. Ikke et tjek — en øvelse der afslører strukturelle problemer scannere aldrig ser.</p></div>
      <div class="card"><h3>6️⃣ Automatiske helhedsscannere</h3><p>Værktøjer som den gratis <a href="/scan" style="color:var(--color-accent);">Accessibility Scanner</a> tager en hel URL og lister alle kontrast-, overskrifts-, alt-tekst- og formulartjek i én rapport — praktisk til status før en leverance.</p></div>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Hvad ingen af dem fanger</h2>
    <ul>
      <li><strong>Kvalitet i alt-tekster</strong> — scanneren ser at alt-teksten findes, ikke om den giver mening.</li>
      <li><strong>Tastatur-logik</strong> — om tab-rækkefølgen og fokus-indikatorerne følger sidens visuelle flow.</li>
      <li><strong>Forståelige fejlbeskeder</strong> — om formularen fortæller brugeren hvad der skal rettes, og hvor.</li>
      <li><strong>Mening</strong> — om overskrifterne afspejler indholdets hierarki, og om teksten er skrevet klart.</li>
    </ul>
    <p>Derfor: lad scannere finde de tekniske fejl (det klarer de bedre og hurtigere end
    mennesker), og brug 15 minutter med tastatur og skærmlæser på de vigtigste sider.
    Sammen dækker det det meste af WCAG AA.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/scan" class="btn-primary">Start med et scan &rarr;</a>
      &nbsp;
      <a href="/blog/eaa-accessibility-checklist" class="btn-secondary">Eller tag EAA-checklisten</a>
    </div>
  </div>
</section>
''',
        'related': ('<a href="/blog/accessibility-scanner-cli" lang="en">Scanner som CLI (engelsk)</a> &middot; '
                    '<a href="/da/blog/wcag-kontrast-checker" lang="da">WCAG Kontrast-Checker</a> &middot; '
                    '<a href="/da/blog/tekst-paa-billede-kontrasttjek" lang="da">Tekst-på-billede-tjek</a>'),
        'tool_url': '/scan',
        'tool_label': 'Scan din side gratis',
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
    <p class="hero-note">Opdateret august 2026 &middot; 4 minutters læsning</p>
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


def patch_file(path, old, new):
    c = open(path).read()
    if new in c:
        print(f'{path}: already patched')
        return
    assert old in c, f'anchor not found in {path}: {old[:70]!r}'
    open(path, 'w').write(c.replace(old, new))
    print(f'{path}: patched')


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
    outs = []
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
        # Cross-link from the EN post down to this DA guide + hreflang both ways
        patch_file(f'{SITE}/blog/{p["en_slug"]}.html',
                   '</head>',
                   f'<link rel="alternate" hreflang="en" href="{BASE}/blog/{p["en_slug"]}">\n'
                   f'<link rel="alternate" hreflang="da" href="{BASE}/da/blog/{p["slug"]}">\n</head>')
        en = open(f'{SITE}/blog/{p["en_slug"]}.html').read()
        if 'Dansk version af denne guide' not in en:
            for anchor in ('<footer style="padding:32px 24px;">', '<footer class="site-footer">'):
                if anchor in en:
                    en = en.replace(anchor,
                        f'<p><a href="/da/blog/{p["slug"]}" lang="da">Dansk version af denne guide</a></p>\n{anchor}', 1)
                    open(f'{SITE}/blog/{p["en_slug"]}.html', 'w').write(en)
                    print(f'{p["en_slug"]}: DA cross-link added')
                    break
            else:
                print(f'{p["en_slug"]}: WARNING no footer anchor found')
        else:
            print(f'{p["en_slug"]}: DA cross-link already present')
        outs.append(out)

    files = outs + [f'{SITE}/blog/{p["en_slug"]}.html' for p in PAGES]
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')
    sx = open(f'{SITE}/sitemap.xml').read()
    assert '</urlset>' in sx
    assert '.html</loc>' not in sx
    print('sitemap URLs:', sx.count('<loc>'))
    print('\nDone: 2 DA guides created + sitemap + cross-links')


if __name__ == '__main__':
    main()
