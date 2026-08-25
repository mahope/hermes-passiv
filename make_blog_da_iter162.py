#!/usr/bin/env python3
"""Iteration 162: Danish pendants round 3.

1. NEW page  site/da/blog/skriv-tilgaengelighedserklaering.html
             (pendant of EN how-to-write-accessibility-statement)
2. Cross-links + hreflang only for two existing pairs:
   - accessibility-audit-cost   <-> da pris-tilgaengelighedsgennemgang
   - eaa-deadline-2026          <-> da eaa-frister-2026
JSON-LD validated, sitemap updated, internal link check.
"""
import json, re, os
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

# Existing pairs that only need hreflang + visible cross-links both ways
PAIRS = [
    ('accessibility-audit-cost', 'blog/pris-tilgaengelighedsgennemgang'),
    ('eaa-deadline-2026', 'blog/eaa-frister-2026'),
]

NEW_PAGE = {
    'slug': 'skriv-tilgaengelighedserklaering',
    'en_slug': 'how-to-write-accessibility-statement',
    'title': 'Sådan skriver du en tilgængelighedserklæring (EAA-skabelon 2026)',
    'h1': 'Sådan Skriver Du en<br>Tilgængelighedserklæring',
    'desc': ('Trin-for-trin guide til at skrive en EAA-compliant '
             'tilgængelighedserklæring for din hjemmeside: kravene i EU-regulation '
             '2023/2419, de seks obligatoriske afsnit, typiske fejl og en udfyld-skabelon.'),
    'og_desc': ('Hvad skal en tilgængelighedserklæring indeholde efter Europas '
                'tilgængelighedslov? De seks obligatoriske afsnit, typiske fejl og en '
                'gratis generator — på 10 minutter.'),
    'badge': 'EAA &middot; GUIDE &amp; SKABELON',
    'subtitle': ('Siden juni 2025 skal alle hjemmesider der tilbyder varer eller tjenester '
                 'til EU-forbrugere have en offentlig tilgængelighedserklæring. Her er '
                 'præcis hvad den skal indeholde — og hvordan du skriver den på under en time.'),
    'cta1': ('<a href="/accessibility-statement-generator" lang="en" class="btn-primary">'
             'Brug den gratis generator (engelsk) &rarr;</a>'),
    'cta2': '<a href="#krav" class="btn-secondary">Se de seks krav</a>',
    'tool_url': '/accessibility-statement-generator',
    'tool_label': 'Generér din erklæring nu',
    'faq': [
        ("Skal hver enkelt underside have sin egen erklæring?",
         "Nej. Én tilgængelighedserklæring pr. domæne/tjeneste er nok, så længe den "
         "dækker hele sitet. Kører du flere selvstændige tjenester på separate domæner, "
         "skal hver have sin egen — med korrekt conformance-status for netop den tjeneste."),
        ("Må jeg bruge samme erklæring til flere kundesider?",
         "Nej — kopier ikke blindt. Organisation, feedback-e-mail, kendte begrænsninger "
         "og testmetode skal afspejle det enkelte site. Brug strukturen fra denne guide som "
         "skabelon, men udfyld alt indhold pr. side. Bureauer bør lave en tjekliste pr. leverance."),
        ("Skal erklæringen være på dansk?",
         "Den skal være på et sprog dine brugere forstår. Er sitet på dansk, skal "
         "erklæringen også være det — myndigheder og brugere forventer det. Har du et "
         "flersproget site, kan du have versioner pr. sprog, men indholdet skal være ens."),
        ("Hvad sker der, hvis jeg ikke har en erklæring?",
         "Uden offentlig tilgængelighedserklæring er sitet reelt non-compliant med Europas "
         "tilgængelighedslov — uanset hvor tilgængelig koden i øvrigt er. Tilsynsmyndigheden "
         "(i Danmark er der udpegede markedsføringstilsyn under loven) kan pålægge rettelse "
         "og i sidste instans bøder. Erklæringen er samtidig det nemmeste krav at opfylde."),
    ],
    'body': '''
<section class="problem" id="hvorfor">
  <div class="container">
    <h2>Hvorfor sitet har brug for en erklæring</h2>
    <p>Europas tilgængelighedslov (EAA) trådte i kraft i juni 2025. Alle hjemmesider der
    tilbyder varer eller tjenester til EU-forbrugere skal offentliggøre en
    tilgængelighedserklæring. Det er ikke frivilligt — det er et lovkrav, og uden
    erklæringen er sitet automatisk non-compliant, uanset hvor tilgængelig koden er.</p>
    <div class="problem-cards">
      <div class="card"><h3>⚖️ Juridisk compliance</h3><p>Loven kræver eksplicit en offentlig erklæring om tilgængelighed. Mangler den, er sitet non-compliant — uanset hvor godt det i øvrigt lever op til WCAG.</p></div>
      <div class="card"><h3>🤝 Transparens over for brugere</h3><p>Besøgende med handicap kan straks se sitets niveau, kendte problemer og hvordan de melder fejl. Det bygger tillid og reducerer henvendelser.</p></div>
      <div class="card"><h3>📋 Krav i udbud og indkøb</h3><p>Virksomheder og offentlige kunder spørger i stigende grad efter tilgængelighedserklæringer i leverandøronboarding. Har du én, fjerner du en klassisk kontraktblokering.</p></div>
    </div>
  </div>
</section>

<section class="products" id="krav">
  <div class="container">
    <h2>De seks obligatoriske afsnit (EU-regulation 2023/2419)</h2>
    <ol>
      <li><strong>Forpligtelse til tilgængelighed</strong> — én til to sætninger om at sitet skal kunne bruges af alle. Hold det kort.</li>
      <li><strong>Conformance-status</strong> — hvilken standard I sigter mod (WCAG 2.1 AA for EAA), og om sitet er fuldt, delvist eller ikke conformant. De fleste sider er "delvist conformant" — det er acceptabelt, hvis begrænsningerne er dokumenteret.</li>
      <li><strong>Kendte begrænsninger</strong> — ærlig liste over kendte problemer og, hvor muligt, en alternativ måde at få indholdet på. Dokumenterede begrænsninger er compliant; at skjule dem er ikke.</li>
      <li><strong>Feedback-mekanisme</strong> — en e-mail eller formular hvor brugere kan melde problemer, samt svartid. Jo flere kanaler, jo bedre.</li>
      <li><strong>Testmetode</strong> — hvordan tilgængeligheden er vurderet: automatisk scanning, manuel test, brugertest eller ekstern revision. Vær ærlig — selvvurdering med automatiske værktøjer tæller med.</li>
      <li><strong>Kontakt til tilsynsmyndighed</strong> — den nationale myndighed brugere kan henvende sig til, hvis de er utilfredse med jeres svar. Link til jeres lands myndighed.</li>
    </ol>
    <p>Til det: vis datoen for seneste gennemgang. En erklæring uden dato virker forældet —
    og bliver det også.</p>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Sådan gør du — på under en time</h2>
    <ol>
      <li>Scan sitet med et gratis værktøj så du kender dine faktiske problemer
      (<a href="/scan-da" style="color:var(--color-accent);">Accessibility Scanner</a>).</li>
      <li>Udfyld de seks afsnit ovenfor — ærligt, især om begrænsninger.</li>
      <li>Læg erklæringen på en offentlig side (fx /tilgaengelighed) og link til den fra
      footeren på alle undersider.</li>
      <li>Kalenderpåmindelse: gennemgå erklæringen kvartalsvis, og opdatér kendte
      begrænsninger efter hver scanning.</li>
    </ol>
    <p>Vil du spare arbejdet? Den gratis
    <a href="/accessibility-statement-generator" lang="en" style="color:var(--color-accent);">Statement Generator</a>
    (på engelsk) genererer en komplet erklæring ud fra syv svar — klar til copy-paste.
    Eller se vores oversigt over
    <a href="/blog/gratis-eaa-saetninger" style="color:var(--color-accent);">gratis EAA-sætninger og generatorer</a>.</p>
    <div style="text-align:center;margin-top:20px;">
      <a href="/accessibility-statement-generator" lang="en" class="btn-primary">Generér din erklæring nu &rarr;</a>
      &nbsp;
      <a href="/da/blog/gratis-tilgaengelighedsvaerktoejer" class="btn-secondary">Gratis testværktøjer</a>
    </div>
  </div>
</section>

<section class="products">
  <div class="container">
    <h2>Typiske fejl du skal undgå</h2>
    <ul>
      <li><strong>At påstå fuld conformance uden bevis</strong> — overclaiming er en juridisk risiko. Skriv delvis conformance og dokumentér undtagelserne.</li>
      <li><strong>Ingen feedback-mulighed</strong> — erklæringen uden kontaktvej opfylder ikke kravet.</li>
      <li><strong>Forældet tilsynskontakt</strong> — tjek årligt at myndigheden og kontaktoplysningerne stadig passer.</li>
      <li><strong>Erklæringen gemt væk</strong> — den skal ligge på en offentlig side og linkes fra footeren.</li>
      <li><strong>Ingen dato for seneste gennemgang</strong> — uden dato fremstår dokumentet dødt.</li>
    </ul>
  </div>
</section>
''',
    'related': ('<a href="/blog/gratis-eaa-saetninger" lang="da">Gratis EAA-sætninger</a> &middot; '
                '<a href="/da/blog/gratis-tilgaengelighedsvaerktoejer" lang="da">Gratis tilgængelighedsværktøjer</a> &middot; '
                '<a href="/blog/eaa-frister-2026" lang="da">EAA-frister 2026</a>'),
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
      <a href="{p['tool_url']}" lang="en" class="btn-primary">{p['tool_label']} &rarr;</a>
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


def add_hreflang_pair(en_slug, da_path):
    """Add reciprocal hreflang + visible DA/EN cross-links between an EN post
    in /blog/ and a DA page anywhere on the site."""
    en_f = f'{SITE}/blog/{en_slug}.html'
    da_f = f'{SITE}/{da_path}.html'
    en = open(en_f).read()
    da = open(da_f).read()

    # hreflang on EN -> DA
    da_url = f'{BASE}/{da_path}'
    if f'hreflang="da" href="{da_url}"' not in en:
        assert '</head>' in en
        en = en.replace('</head>',
                        f'<link rel="alternate" hreflang="en" href="{BASE}/blog/{en_slug}">\n'
                        f'<link rel="alternate" hreflang="da" href="{da_url}">\n</head>')
        open(en_f, 'w').write(en)
        print(f'{en_slug}: hreflang pair added')
    else:
        print(f'{en_slug}: hreflang already present')

    # Visible cross-link from EN down to DA
    if 'Dansk version af denne guide' not in en:
        done = False
        for anchor in ('<footer style="padding:32px 24px;">', '<footer class="site-footer">'):
            if anchor in en:
                en = open(en_f).read().replace(anchor,
                    f'<p><a href="/{da_path}" lang="da">Dansk version af denne guide</a></p>\n{anchor}', 1)
                open(en_f, 'w').write(en)
                print(f'{en_slug}: DA cross-link added')
                done = True
                break
        if not done:
            print(f'{en_slug}: WARNING no footer anchor found')

    # hreflang on DA -> EN (only if the DA page has a head block we can patch)
    en_url = f'{BASE}/blog/{en_slug}'
    if f'hreflang="en" href="{en_url}"' not in da:
        assert '</head>' in da
        da = da.replace('</head>',
                        f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
                        f'<link rel="alternate" hreflang="da" href="{da_url}">\n</head>')
        open(da_f, 'w').write(da)
        print(f'{da_path}: hreflang pair added')
    else:
        print(f'{da_path}: hreflang already present')


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
    # 1. Build the new DA pendant
    out = f'{SITE}/da/blog/{NEW_PAGE["slug"]}.html'
    page = build_page(NEW_PAGE)
    with open(out, 'w') as f:
        f.write(page)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)
    for b in blocks:
        d = json.loads(b)
        assert d['@context'] == 'https://schema.org', d['@context']
    print(f'{out} written, JSON-LD OK ({len(blocks)} blocks)')
    update_sitemap(NEW_PAGE['slug'])
    add_hreflang_pair(NEW_PAGE['en_slug'], f'da/blog/{NEW_PAGE["slug"]}')

    # 2. Cross-link existing pairs only
    for en_slug, da_rel in PAIRS:
        add_hreflang_pair(en_slug, da_rel)

    files = [out] + [f'{SITE}/blog/{s}.html' for s, _ in PAIRS] \
          + [f'{SITE}/{p}.html' for _, p in PAIRS] \
          + [f'{SITE}/blog/{NEW_PAGE["en_slug"]}.html']
    broken = check_links(files)
    print('broken internal links:', broken if broken else 'none')
    sx = open(f'{SITE}/sitemap.xml').read()
    assert '</urlset>' in sx
    assert '.html</loc>' not in sx
    print('sitemap URLs:', sx.count('<loc>'))
    print('\nDone: 1 new DA guide + 3 reciprocal EN<->DA link pairs')


if __name__ == '__main__':
    main()
