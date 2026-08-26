#!/usr/bin/env python3
"""Hub-reparation: tilføj manglende blog-kort for alle /blog-sider på site/index.html.

Kort genereres automatisk fra hver sides <h1> og meta description.
Idempotent: kør igen uden at lave dubletter. Verificerer til sidst at
hub og disk matcher 1:1, samt at alle interne links i sektionen peger
på noget der findes.

Usage: python3 tools/fix_en_hub.py
"""
import glob
import html as htmllib
import os
import re

SITE = 'site'
HUB = f'{SITE}/index.html'
SECTION_MARKER = '<section class="products" id="blog">'

# slug -> (badge, title-override, description-override)
OVERRIDES = {
    'html-tabel-til-csv': ('VÆRKTØJ · DA', 'HTML-tabel til CSV (dansk)',
        'Konvertér enhver HTML-tabel til ren CSV direkte i browseren — guide på dansk.'),
    'bugrapporter-i-ci-pipeline': ('DEV TOOLS · DA', 'Bugrapporter i CI-pipelinen',
        'Få brugerrapporterede fejl direkte ind i GitHub Actions — guide på dansk.'),
}

BADGE_RULES = [
    ('accessib|eaa|wcag|overlay|audit-cost|statement', 'ACCESSIBILITY · EAA'),
    ('gdpr|nis2|cookie|cmp|dpa|consent', 'COMPLIANCE'),
    ('monitor|down|uptime|ssl|smoke|release-integrity|zip', 'MONITORING · CI'),
    ('table|csv|markdown|copy|clean|text|base64|case|hash|json', 'DEV TOOLS'),
    ('seo|hreflang|canonical|meta|redirect|speed|lighthouse|pages|open-graph', 'SEO'),
    ('desktop|cli|vscode|obsidian|iphone|ipad|brew|github-action', 'PLATFORMS'),
]


def badge_for(slug):
    if slug in OVERRIDES:
        return OVERRIDES[slug][0]
    for pat, b in BADGE_RULES:
        if re.search(pat, slug):
            return b
    return 'GUIDE'


def clean(s):
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def page_meta(slug):
    p = f'{SITE}/blog/{slug}.html'
    h = open(p).read()
    t = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.DOTALL)
    d = re.search(r'name="description" content="(.*?)"', h)
    title = clean(t.group(1)) if t else slug
    desc = clean(htmllib.unescape(d.group(1))) if d else ''
    if len(title) > 70:
        title = title[:67].rstrip() + '…'
    if len(desc) > 140:
        desc = desc[:137].rstrip() + '…'
    if slug in OVERRIDES:
        _, to, do = OVERRIDES[slug]
        title, desc = to, do
    return title, desc


def add_card(slug):
    c = open(HUB).read()
    url = f'/blog/{slug}'
    if f'href="{url}"' in c:
        print(f'skip {slug} (already linked)')
        return False
    title, desc = page_meta(slug)
    card = (
        f'\n      <div class="product-card">\n'
        f'        <div class="product-badge product-badge-secondary">{htmllib.escape(badge_for(slug))}</div>\n'
        f'        <div class="product-body">\n'
        f'          <h3><a href="{url}" style="color:inherit;text-decoration:none;">{htmllib.escape(title)}</a></h3>\n'
        f'          <p class="product-desc">{htmllib.escape(desc)}</p>\n'
        f'          <div class="product-details"><span class="product-meta">📖 Guide</span>'
        f'<span class="product-meta">✅ Free</span></div>\n'
        f'          <a href="{url}" class="btn-secondary" style="margin-top:12px;">Read Guide &rarr;</a>\n'
        f'        </div>\n      </div>\n'
    )
    sec_start = c.find(SECTION_MARKER)
    assert sec_start != -1, 'blog-sektion ikke fundet'
    pos = c.rfind('<a href="/blog/', sec_start)
    end = c.find('</section>', pos)
    assert pos != -1 and end != -1, 'kunne ikke finde indsættelsespunkt'
    c = c[:end] + card + '\n' + c[end:]
    open(HUB, 'w').write(c)
    print(f'added card: {slug}')
    return True


def main():
    files = {os.path.basename(f)[:-5]
             for f in glob.glob(f'{SITE}/blog/*.html')
             if os.path.basename(f) != 'index.html'}
    added = [s for s in sorted(files) if add_card(s)]
    # Verificér: hub <-> disk 1:1
    c = open(HUB).read()
    hub = set(re.findall(r'href="/blog/([^"#?]+)"', c))
    dead = hub - files
    missing = files - hub
    assert not dead, f'hub links to non-existent pages: {dead}'
    assert not missing, f'still missing from hub: {missing}'
    print(f'verify OK: disk={len(files)} hub={len(hub)} added={len(added)}')
    # Intern link-tjek for hele forsiden
    broken = []
    for m in sorted(set(re.findall(r'href="(/[^"#?]*?)(?:\?.*)?"', c))):
        t = ('site' + m).rstrip('/')
        if not (os.path.exists(t) or os.path.exists(t + '.html') or m == '/'
                or os.path.exists(t + '/index.html')):
            broken.append(m)
    assert not broken, f'broken links in index.html: {broken}'
    print('Internal link check index.html: OK')


if __name__ == '__main__':
    main()
