#!/usr/bin/env python3
"""Generate site/blog/index.html — the real blog overview page.
Run from repo root: python3 tools/make_blog_index.py [--out <fil>] [--da-out <fil>]

Deterministic: reads every post's <title> + <meta description>, groups by topic.

**The page must be byte-identical to this generator's output**, for both
languages: `tools/check_blog_index.py` dømmer det. Det er ikke pedanteri — det
er den fejl der lå her. Siden blev genereret en gang og derefter redigeret i
hånden, og da nye artikler kom, fulgte de ikke med: 7 engelske og 13 danske
guides lå i `site/` uden et eneste link fra den side, hvis
`<meta name="description">` siger «Every guide on this site». Derfor ejer
generatoren nu *hele* filen, inklusive bogs-CTA'en i footeren og det afsluttende
track-script, så en regenerering ikke kan slette dem.

`--out` skriver til en anden fil end `site/blog/index.html`; porten bruger det til
at sammenligne den committede side med den genererede, uden at røre repoet.

Målt 3/10: der var **ingen dansk indeksside**. `site/da/blog/` rummede 85 artikler,
men ingen `index.html`, så alle 97 danske sider sendte læseren til den engelske
`/blog/` — 282 links. Den side lister de danske guider under en «På dansk»-skiller
efter 93 engelske, med **engelske** emne-overskrifter («Accessibility & EAA
(dansk)») og engelsk chrome. Så en dansk læser der trykkede «Guides» fik en
engelsk side, hvor hans eget sprog lå nederst. Derfor skriver en kørsel uden
argumenter nu **to** sider: `site/blog/index.html` og `site/da/blog/index.html`,
den danske på dansk med danske emne-overskrifter og kun de danske artikler.
`--out` skriver kun den engelske, fordi porten bruger den til sammenligningen.
"""
import glob, html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
BASE = 'https://hermes-passiv.pages.dev'

# Nøgleordene dømmer **begge** sprog: de danske slugs (`kopier-`,
# `tjek-om-hjemmeside-er-nede-gratis`) er ikke oversættelser af de engelske, så
# en liste med kun EN-nøgleord sendte dem alle i den første kategori de ramte —
# eller i sidste kategorien, fordi ingen passede. Listen er derfor ét sæt per
# emne med begge sprog i.
CATS = [
    ('Accessibility & EAA',
     ['accessib', 'eaa', 'wcag', 'bitv', 'joomla', 'drupal', 'typo3', 'ghost-',
      'magento', 'prestashop', 'shopify', 'squarespace', 'webflow', 'wix',
      'wordpress-vs', 'contrast-checker', 'text-on-image',
      # dansk
      'tilgaengelighed', 'kontrast', 'tekst-paa-billede', 'skriv-til-']),
    ('GDPR, NIS2 & Cookie Compliance',
     ['gdpr', 'nis2', 'cookie', 'cmp-', 'compliance', 'dpa-web',
      # dansk
      'dbbaftale', 'databehandleraftage']),
    ('Copy, Tables & Markdown Tools',
     ['copy-', 'copy_', 'table', 'html-to-markdown', 'html-tabel', 'markdown',
      'paste-', 'url-to-markdown', 'building-html',
      # dansk
      'kopier', 'klistre', 'tabel', 'html-til-markdown', 'url-til-markdown',
      'indsæt-', 'indsat-', 'byg-en-']),
    ('SEO & Website Health',
     ['redirect', 'ssl', 'http-headers', 'meta-tag', 'open-graph',
      'technical-seo', 'seo', 'zip-before-release', 'release-integrity',
      'broken-link', 'find-all-pages', 'website-page-size', 'down-checker',
      'macos-menu-bar', 'site-health', 'get-notified', 'lighthouse',
      'metadata-checker',
      # dansk
      'omdirigering', 'hovedere', 'meta-tjekker', 'seo-', 'nedbrud', 'nedet',
      'nede', 'overvaag', 'hastighed', 'delaegge', 'hvor-stor',
      'sammenlign-to-sider', 'seo-metadata']),
    ('Dev Tools & Guides',
     ['bug-report', 'desktop-website-monitor', 'developer-text-tools',
      'cli', 'vscode', 'obsidian', 'chrome', 'github-action',
      # dansk
      'terminalen', 'bugrapport', 'udgivelse']),
]

# De samme fem emner på dansk. De ligger her og ikke i `CATS`, fordi de kun er
# et **sprogvalg for en overskrift** — kategoriseringen (`categorize`) bruger
# slugs og er sprogneutral. Uden dem måtte den danske side have engelske
# emne-overskrifter, hvilket var præcis fundet da siden ikke fandtes.
DA_CATS = [
    'Tilgængelighed & EAA',
    'GDPR, NIS2 & cookie-compliance',
    'Kopiér, tabeller & Markdown',
    'SEO & sidens sundhed',
    'Udviklerværktøjer & guides',
]

def categorize(slug):
    slug = slug.lower()
    for name, keys in CATS:
        if any(k in slug for k in keys):
            return name
    return 'Dev Tools & Guides'

def extract(path):
    s = open(path, encoding='utf-8', errors='ignore').read()
    t = re.search(r'<title>(.*?)</title>', s, re.S)
    og = re.search(r'<meta property="og:title" content="(.*?)"\s*/?>', s)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S | re.I)
    d = re.search(r'<meta name="description" content="(.*?)"\s*/?>', s)
    # prefer og:title: full titles, no <br> truncation issues; fall back to h1
    src = og or h1 or t
    title = html.unescape(re.sub(r'<[^>]+>|<br\s*/?>', ' ', src.group(1))).strip() if src else ''
    title = re.sub(r'\s+', ' ', title)
    # strip trailing " | ..." suffixes some titles carry
    title = re.split(r'\s*[|—]\s*(?:Mahope|Hermes|Clean Copy)', title)[0].strip()
    desc = html.unescape(d.group(1).strip()) if d else ''
    return title, desc

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args_out = None
    args_da = None
    i = 0
    while i < len(argv):
        if argv[i] == '--out' and i + 1 < len(argv):
            args_out = argv[i + 1]
            i += 2
        elif argv[i] == '--da-out' and i + 1 < len(argv):
            args_da = argv[i + 1]
            i += 2
        else:
            print(f'unkendt argument: {argv[i]}', file=sys.stderr)
            i += 1
    posts = []
    for f in sorted(glob.glob(os.path.join(SITE, 'blog', '*.html'))):
        slug = os.path.basename(f)[:-5]
        if slug == 'index':
            continue
        title, desc = extract(f)
        if not title:
            print(f'WARN no title: {slug}', file=sys.stderr)
            continue
        posts.append((slug, title, desc, categorize(slug)))

    da_posts = []
    for f in sorted(glob.glob(os.path.join(SITE, 'da', 'blog', '*.html'))):
        slug = os.path.basename(f)[:-5]
        # `index` er den danske indeksside, ikke en guide. Den engelske loop har
        # samme spring — uden det tæller siden sig selv med og får 97 i stedet
        # for 96, og begge sider lister `/da/blog/index` som en artikel.
        if slug == 'index':
            continue
        title, desc = extract(f)
        if title:
            da_posts.append((slug, title, desc, categorize(slug)))

    grouped = {}
    for p in posts:
        grouped.setdefault(p[3], []).append(p)

    da_grouped = {}
    for p in da_posts:
        da_grouped.setdefault(p[3], []).append(p)

    out = ["""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blog — All Guides &amp; Free Tool Tutorials</title>
<meta name="description" content="Every guide on this site: EU compliance (EAA, GDPR, NIS2), accessibility audits, copy-paste tools, SEO checks and developer tooling. All free, no signup.">
<meta property="og:type" content="website">
<meta property="og:title" content="Blog — All Guides &amp; Free Tool Tutorials">
<meta property="og:description" content="EU compliance, accessibility, copy-paste tools, SEO checks and developer tooling — every guide in one place. All free.">
<meta property="og:url" content="{base}/blog">
<meta property="og:image" content="{base}/cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{base}/blog">
<link rel="alternate" type="text/plain" href="/llms.txt" title="Machine-readable tool catalog">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">BLOG</div>
    <h1>All Guides &amp;<br>Tutorials</h1>
    <p class="subtitle">{n} English guides on EU compliance, accessibility, copy-paste workflows, SEO checks and free developer tools — plus {nda} Danish guides.</p>
  </div>
</header>
<main class="container" style="max-width:900px;padding-top:32px">
""".format(base=BASE, n=len(posts), nda=len(da_posts))]

    def sektion(name, praefiks, items, dansk=False):
        """Én emne-sektion. Samme markering for begge sprog, så en dansk læser
        får samme opdeling som en engelsk — før stod de 96 danske guides som én
        flad liste på 83 linjer uden beskrivelser.

        `dansk=True` giver overskriften og ankeret deres egen form, fordi de fem
        emner ellers ville stå to gange på samme side med samme `id`."""
        anchor = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        overskrift = f'{name} (dansk)' if dansk else name
        if dansk:
            anchor += '-da'
        out.append(f'<section id="{anchor}">\n<h2>{overskrift}</h2>\n<ul style="list-style:none">\n')
        for slug, title, desc, _c in items:
            href = f'/{praefiks}{slug}'
            out.append(
                f'<li style="margin-bottom:20px">'
                f'<a href="{href}" style="color:var(--color-accent);font-weight:600;text-decoration:none;font-size:1.02rem">{html.escape(title)}</a>'
                + (f'<br><span style="color:var(--color-text-muted);font-size:0.88rem">{html.escape(desc[:180])}</span>' if desc else '')
                + '</li>\n')
        out.append('</ul>\n</section>\n')

    for name, _keys in CATS:
        if grouped.get(name):
            sektion(name, 'blog/', grouped[name])

    if da_posts:
        out.append('<p style="font-size:0.8rem;color:var(--color-text-muted);margin:40px 0 0">'
                   'P&aring; dansk</p>\n')
        for name, _keys in CATS:
            if da_grouped.get(name):
                sektion(name, 'da/blog/', da_grouped[name], dansk=True)

    out.append("""<p style="margin:48px 0;text-align:center"><a href="/" class="btn-secondary">&larr; Home</a> &nbsp; <a href="/free-tools" class="btn-primary">Browse all free tools &rarr;</a></p>
</main>
<footer style="padding:32px 24px;text-align:center;color:var(--color-text-muted)">
  <p>&copy; 2026 Mahope &middot; <a href="/">Hermes Passiv</a></p>
<div class="book-cta" style="border:1px solid #ddd;border-radius:8px;padding:16px 20px;margin:32px 0;">
  <h3>Free e-books: EU compliance guides</h3>
  <p>Six practical guides (NIS2, GDPR, EAA, cookies) &mdash; every complete book is a free EPUB download.</p>
  <a href="/books" class="btn-primary">Browse the free e-books &rarr;</a>
  <p style="margin:12px 0 0;font-size:13px;color:#555;">Want all six guides? <a href="/books/compliance-bundle"><strong>Complete EU Compliance Bundle</strong></a> &mdash; all six listed together, each a free EPUB.</p>
</div>
</footer>
<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});}catch(e){}})();
</script>
</body>
</html>
""")

    dest = args_out or os.path.join(SITE, 'blog', 'index.html')
    open(dest, 'w', encoding='utf-8').write(''.join(out))
    total = sum(len(v) for v in grouped.values())
    print(f'Wrote {dest}: {total} EN posts in {len([k for k,_ in CATS if grouped.get(k)])} sections + {len(da_posts)} DA posts')
    # coverage check
    missing = [name for name, _k in CATS if not grouped.get(name)]
    if missing:
        print('Empty categories:', missing)

    # Den danske indeksside. `args_out` alene må ikke røre repoet: porten
    # sammenligner den engelske side med `--out`, og en sådan kørsel skal ikke
    # skrive den danske side ved siden af sammenligningen. `--da-out` skriver
    # kun den danske til den sti, porten bruger til sin egen sammenligning.
    if args_da or args_out is None:
        da_dest = args_da or os.path.join(SITE, 'da', 'blog', 'index.html')
        os.makedirs(os.path.dirname(da_dest), exist_ok=True)
        open(da_dest, 'w', encoding='utf-8').write(''.join(dansk_index(da_posts, da_grouped, len(posts))))
        print(f'Wrote {da_dest}: {len(da_posts)} DA posts in '
              f'{len([k for k,_ in CATS if da_grouped.get(k)])} sections')


# Den danske side. Samme markering som den engelske (`<section>`, `<h2>`, `<ul>`,
# `var(--color-…)`), fordi design-reglerne er de samme — kun teksten er dansk.
#
# `n_en` er antallet engelske guider, talt af generatoren og ikke skrevet i
# hånden: det er det samme tal `/blog/` fortæller, og hvis det rådner på den ene
# side og ikke på den anden, er læseren holdt op at kunne regne (punkt 11).
def dansk_index(da_posts, da_grouped, n_en):
    n = len(da_posts)
    out = ["""<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guider &mdash; alle artikler om EU-compliance, tilgængelighed og gratis værkt&oslash;j</title>
<meta name="description" content="Vores {n} danske guides: EU-compliance (EAA, GDPR, NIS2), tilg&aelig;ngelighed, kopi&eacute;r-v&aelig;rkt&oslash;j, SEO-tjek og udviklerv&aelig;rkt&oslash;j. Alle gratis, ingen tilmelding.">
<meta property="og:type" content="website">
<meta property="og:title" content="Guider &mdash; alle artikler om EU-compliance og gratis v&aelig;rkt&oslash;j">
<meta property="og:description" content="Vores {n} danske guides om EU-compliance, tilg&aelig;ngelighed, kopi&eacute;r-v&aelig;rkt&oslash;j, SEO-tjek og udviklerv&aelig;rkt&oslash;j &mdash; alle sammen p&aring; &eacute;n side.">
<meta property="og:url" content="{base}/da/blog">
<meta property="og:image" content="{base}/cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{base}/da/blog">
<link rel="alternate" type="text/plain" href="/llms.txt" title="Machine-readable tool catalog">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">GUIDER</div>
    <h1>Alle danske guider</h1>
    <p class="subtitle">{n} guider p&aring; dansk om EU-compliance, tilg&aelig;ngelighed, arbejdsgange med tekst og tabeller, SEO-tjek og udviklerv&aelig;rkt&oslash;j. De {n_en} engelske guider ligger p&aring; <a href="/blog/">den engelske indeksside</a>.</p>
  </div>
</header>
<main class="container" style="max-width:900px;padding-top:32px">
""".format(base=BASE, n=n, n_en=n_en)]

    def sektion_tal(items, tittel):
        anchor = re.sub(r'[^a-z0-9]+', '-', tittel.lower()).strip('-')
        out.append(f'<section id="{anchor}">\n<h2>{html.escape(tittel)}</h2>\n<ul style="list-style:none">\n')
        for slug, title, desc, _c in items:
            out.append(
                f'<li style="margin-bottom:20px">'
                f'<a href="/da/blog/{slug}" style="color:var(--color-accent);font-weight:600;text-decoration:none;font-size:1.02rem">{html.escape(title)}</a>'
                + (f'<br><span style="color:var(--color-text-muted);font-size:0.88rem">{html.escape(desc[:180])}</span>' if desc else '')
                + '</li>\n')
        out.append('</ul>\n</section>\n')

    for (navn, _keys), da_navn in zip(CATS, DA_CATS):
        if da_grouped.get(navn):
            sektion_tal(da_grouped[navn], da_navn)

    out.append("""<p style="margin:48px 0;text-align:center"><a href="/da/" class="btn-secondary">&larr; Forside</a> &nbsp; <a href="/da/free-tools" class="btn-primary">Se alle v&aelig;rkt&oslash;j &rarr;</a></p>
</main>
<footer style="padding:32px 24px;text-align:center;color:var(--color-text-muted)">
  <p>&copy; 2026 Mahope &middot; <a href="/da/">Hermes Passiv</a></p>
<div class="book-cta" style="border:1px solid #ddd;border-radius:8px;padding:16px 20px;margin:32px 0;">
  <h3>Gratis e-b&oslash;ger om EU-compliance</h3>
  <p>Seks praktiske guider (NIS2, GDPR, EAA, cookies) &mdash; alle seks er en gratis EPUB-download. B&oslash;gerne er skrevet p&aring; engelsk.</p>
  <a href="/books" class="btn-primary">Se de gratis e-b&oslash;ger &rarr;</a>
  <p style="margin:12px 0 0;font-size:13px;color:#555;">Vil du alle seks? <a href="/books/compliance-bundle"><strong>Komplet EU-compliance-pakke</strong></a> &mdash; alle seks samlet, hver som en gratis EPUB.</p>
</div>
</footer>
<script>
(function(){try{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\.html$/,'')||'/';fetch('/api/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:p}),keepalive:true}).catch(function(){});}catch(e){}})();
</script>
</body>
</html>
""")
    return out

if __name__ == '__main__':
    main(sys.argv[1:])
