#!/usr/bin/env python3
"""Iteration 483: EN-guide-arkiv (/guides) + indeks-reparationer.

1. /guides — arkiv over ALLE EN-blogposts, grupperet i kategorier
   (spejl af /da/guides fra iter482).
2. Ret forældede tællinger i blog/index.html ("84 English guides").
3. Ret de to iter482-EN-indekslinjer der fejlagtigt fik danske beskrivelser.
4. Regenerér /da/guides så nye poster er med.
5. Link /guides fra blog-indekset og /da/guides-kort på /da.html.
Ingen eksterne søgninger.
"""
import json, re, os, sys, glob, html
from datetime import date

SITE = 'site'
TODAY = date.today().isoformat()
BASE = 'https://hermes-passiv.pages.dev'

CATS = [
    ('Accessibility & EAA', ['tilgaeng', 'eaa', 'wcag', 'accessibility', 'contrast',
                             'color-blind', 'ada-', 'section-508']),
    ('GDPR & Cookies', ['gdpr', 'cookie', 'dpa', 'cmp-', 'privacy-policy', 'ropa']),
    ('NIS2 & Security', ['nis2', 'ssl', 'security-header', 'http-headers', 'csp']),
    ('SEO & Site Health', ['seo', 'meta-', 'open-graph', 'hreflang', 'canonical',
                           'redirect', 'speed', 'site-health', 'down-checker',
                           'monitor', 'uptime', 'compare-two-web-pages']),
    ('Copy-Paste & Text Tools', ['copy', 'clean-text', 'paste', 'markdown', 'table',
                                 'obsidian', 'notion', 'airtable', 'chatgpt', 'word',
                                 'text-tools', 'url-to-markdown', 'csv']),
    ('Dev Tools & CI', ['bug-report', 'ci-pipeline', 'github-action', 'release-integrity',
                        'zip-before-release', 'smoke-test', 'cli', 'desktop', 'vscode',
                        'developer', 'base64', 'case-converter', 'json']),
]


def title_of(path):
    m = re.search(r'<title>([^<]*)</title>', open(path).read())
    return html.unescape(m.group(1)) if m else os.path.basename(path)[:-5]


def clean_title(t):
    t = html.unescape(t)
    t = re.sub(r'\s*[\(\[][^)\]\[]*2026?[\)\]]\s*$', '', t).strip()
    # Trim dangling fragments like "Real Numbers for" / "Generator, Scanner &"
    t = re.sub(r'\s+(?:for|and|to|with|the|a|an|of|in|on|&|&amp;|\+|—|-|,|:)\s*$', '', t, flags=re.I).strip()
    if len(t) < 20 and '(' in t:
        t = re.sub(r'\s*\([^)]*\)\s*', ' ', t).strip()
    return t


def build_archive(lang):
    """lang='en' -> site/blog/*.html -> /guides ; lang='da' -> da/blog -> /da/guides."""
    if lang == 'en':
        files = sorted(glob.glob(f'{SITE}/blog/*.html'))
        prefix = '/blog/'
        out_path = f'{SITE}/guides.html'
        canon = f'{BASE}/guides'
        cta = '<a href="/free-tools" class="btn-primary">Browse the free tools &rarr;</a>'
        badge = 'GUIDES &middot; ARCHIVE'
        h1 = f'All {{n}}<br>English guides'
    else:
        files = sorted(glob.glob(f'{SITE}/da/blog/*.html'))
        prefix = '/da/blog/'
        out_path = f'{SITE}/da/guides.html'
        canon = f'{BASE}/da/guides'
        cta = '<a href="/da/#tools" class="btn-primary">Se de gratis værktøjer &rarr;</a>'
        badge = 'GUIDES &middot; ARKIV'
        h1 = f'Alle {{n}}<br>danske guides'

    sections = {}
    used = set()
    for cat, keys in CATS:
        items = []
        for f in files:
            base = os.path.basename(f)[:-5]
            if base == 'index' or base in used:
                continue
            if any(k in base.lower() for k in keys):
                items.append((base, clean_title(title_of(f))))
                used.add(base)
        if items:
            sections[cat] = items
    rest = []
    for f in files:
        base = os.path.basename(f)[:-5]
        if base != 'index' and base not in used:
            rest.append((base, clean_title(title_of(f))))
    if rest:
        sections['More guides' if lang == 'en' else 'Andre guides'] = rest

    total = sum(len(v) for v in sections.values())
    body = ''
    for cat, items in sections.items():
        lis = '\n'.join(
            f'<li style="margin-bottom:10px"><a href="{prefix}{slug}">{html.escape(t)}</a></li>'
            for slug, t in items)
        body += (f'<section class="problem"><div class="container"><h2>{cat} '
                 f'({len(items)})</h2><ul style="list-style:none;padding-left:0">{lis}</ul>'
                 f'</div></section>\n')

    if lang == 'en':
        title = f'All {total} English guides — compliance, SEO & dev tools'
        desc = (f'Complete archive of all {total} English guides: EAA accessibility, GDPR, '
                f'NIS2, SEO metadata and developer tools. All free, no signup.')
        subtitle = ('The complete archive: every English guide on this site — accessibility, '
                    'GDPR, NIS2, SEO and developer tools. All free, nothing requires signup.')
    else:
        title = f'Alle danske guides ({total}) — compliance, SEO & dev-værktøjer'
        desc = (f'Komplet arkiv over alle {total} danske guides: EAA og tilgængelighed, GDPR, '
                f'NIS2, SEO-metadata og dev-værktøjer. Alt gratis, intet kræver tilmelding.')
        subtitle = ('Det komplette arkiv: hver eneste guide på dansk — tilgængelighed, GDPR, '
                    'NIS2, SEO og udviklerværktøjer. Alt gratis, intet kræver tilmelding.')

    page = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<link rel="canonical" href="{canon}">
<link rel="alternate" hreflang="{'da' if lang == 'da' else 'en'}" href="{canon}">
<link rel="alternate" hreflang="{'en' if lang == 'da' else 'da'}" href="{'https://hermes-passiv.pages.dev/guides' if lang == 'da' else 'https://hermes-passiv.pages.dev/da/guides'}">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">
<script defer src="/track.js"></script>
</head>
<body>
<header class="hero">
  <div class="container">
    <div class="badge">{badge}</div>
    <h1>{h1.format(n=total)}</h1>
    <p class="subtitle">{subtitle}</p>
    <div class="hero-cta">
      {cta}
    </div>
  </div>
</header>
{body}
<footer style="padding:32px 24px;">
  <p><a href="{'/da' if lang == 'da' else '/'}">{'Forside' if lang == 'da' else 'Home'}</a> &middot;
     <a href="/free-tools">Free tools</a> &middot;
     <a href="/deskuptime">DeskUptime</a> &middot;
     <a href="/page-profile">Page Profile</a></p>
</footer>
<script>
(function(){{try{{if(navigator.doNotTrack==='1')return;var p=location.pathname.replace(/\\.html$/,'')||'/';fetch('/api/track',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{path:p}}),keepalive:true}}).catch(function(){{}});}}catch(e){{}}}})();
</script>
</body>
</html>'''
    with open(out_path, 'w') as f:
        f.write(page)
    print(f'{out_path} written: {total} guides listed')
    return total, out_path


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


def fix_en_index_descriptions():
    """iter482 bug: the two new EN index entries got Danish hub_desc texts."""
    path = f'{SITE}/blog/index.html'
    c = open(path).read()
    fixes = [
        ('Alt en side skal have af titel, description, canonical og Open Graph — tjekket med én CLI-kommando.',
         'Everything a page needs — title, description, canonical and Open Graph — checked with one CLI command.'),
        ('Se forskellene i metadata, struktureret data og teknisk SEO mellem to URLs — før/efter redesign eller dig mod konkurrenten.',
         'See the differences in metadata, structured data and technical SEO between two URLs — before/after redesign or you vs a competitor.'),
    ]
    changed = 0
    for old, new in fixes:
        if old in c:
            c = c.replace(old, new)
            changed += 1
    open(path, 'w').write(c)
    print(f'en-index: {changed} Danish descriptions fixed')


def fix_counts():
    """Update stale guide counts on hub pages."""
    n_da = len([f for f in glob.glob(f'{SITE}/da/blog/*.html')])
    n_en = len([f for f in glob.glob(f'{SITE}/blog/*.html') if 'index' not in f])
    fixes = {
        f'{SITE}/blog/index.html': [
            (re.compile(r'\d+ English guides on EU compliance'),
             f'{n_en} English guides on EU compliance'),
            (re.compile(r'plus \d+ Danish guides'), f'plus {n_da} Danish guides'),
        ],
    }
    for path, subs in fixes.items():
        c = open(path).read()
        for rx, rep in subs:
            c2 = rx.sub(rep, c)
            if c2 != c:
                print(f'counts: {path}: {rx.pattern} -> {rep}')
            c = c2
        open(path, 'w').write(c)


def link_archives_from_index():
    """Add an /guides archive link at the top of the EN blog index."""
    path = f'{SITE}/blog/index.html'
    c = open(path).read()
    if 'href="/guides"' not in c:
        marker = '<p class="subtitle">'
        pos = c.find(marker)
        assert pos != -1, 'subtitle marker missing'
        end = c.find('</p>', pos) + 4
        extra = ('\n<p style="margin-top:12px"><a href="/guides" '
                 'class="btn-secondary">Browse all guides by category →</a></p>')
        c = c[:end] + extra + c[end:]
        open(path, 'w').write(c)
        print('index: /guides link added')
    else:
        print('index: /guides link already present')


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


def main():
    total_en, en_out = build_archive('en')
    total_da, da_out = build_archive('da')
    update_sitemap('guides')
    fix_en_index_descriptions()
    fix_counts()
    link_archives_from_index()
    all_files = [en_out, da_out, f'{SITE}/blog/index.html']
    broken = check_links(all_files)
    if broken:
        print('BROKEN INTERNAL LINKS:')
        for path, link in broken:
            print(f'  {path} -> {link}')
        sys.exit(1)
    print('Internal link check: OK')
    print(f'DONE: EN={total_en} DA={total_da}')


if __name__ == '__main__':
    main()
