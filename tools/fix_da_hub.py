#!/usr/bin/env python3
"""Hub-reparation: tilføj manglende hub-kort for alle /da/blog-sider på site/da.html.

Kort genereres automatisk fra hver sides <h1> og meta description.
Idempotent: kør igen uden at lave dubletter. Verificerer til sidst at
hub og disk matcher 1:1, samt at alle interne links i de berørte filer
peger på noget der findes.

Usage: python3 tools/fix_da_hub.py
"""
import html as htmllib
import os
import re
import sys

SITE = 'site'
HUB = f'{SITE}/da.html'

# slug -> (badge, titel-override, beskrivelse-override)
# Overrides bruges hvor h1/meta er for lange eller har HTML-artefakter.
OVERRIDES = {
    'canonisk-url-guide': ('SEO · CANONICAL', 'Guide til kanoniske URL\u2019er',
        'Sådan sætter, tjekker og retter du kanoniske URLs — med eksempler.'),
    'compliance-tjek-github-action': ('COMPLIANCE · CI', 'Automatisér compliance-tjek i CI',
        'Gratis GitHub Action der tjekker et website for 9 ting ved hvert push.'),
    'html-tabel-til-csv-konverter': ('TABELLER · KONVERTER', 'HTML-tabel til CSV',
        'Konvertér enhver HTML-tabel til ren CSV direkte i browseren, RFC 4180-korrekt.'),
    'html-til-markdown-api': ('HTML → MARKDOWN', 'HTML-til-Markdown REST-API',
        'Send HTML som JSON, få ren Markdown tilbage — til pipelines og integrationer.'),
    'http-headere-reference': ('HTTP · REFERENCE', 'HTTP-headere: den praktiske reference',
        'Caching, CSP og andre sikkerhedsheadere forklaret med eksempler.'),
    'installer-clean-copy-obsidian': ('CLEAN COPY', 'Installer Clean Copy til Obsidian',
        'Plugin der indsætter clipboard-HTML som korrekt Markdown i Obsidian.'),
    'overvaag-hjemmeside-fra-terminalen': ('OPPETID · CLI', 'Overvåg hjemmesider fra terminalen',
        'DeskUptime: én engangsbetaling i stedet for månedlige overvågningsabonnementer.'),
    'overvaag-hjemmeside-mac-menu-bar': ('OPPETID · MAC', 'Hjemmeside-overvågning fra menu bar\u2019en',
        'Hold øje med dine hjemmesider direkte fra macOS menu bar med notifikationer.'),
    'roegtest-efter-udgivelse-statiske-sites': ('CI · RØGTEST', 'Røgtest efter udgivelse af statiske sites',
        'Et to-trins GitHub Actions-job der tjekker at udgivelsen faktisk virker.'),
    'site-health-github-actions-stak': ('CI · SITE HEALTH', 'Site health fra GitHub Actions',
        'Daglig oppetids- og compliance-overvågning helt gratis med Actions cron.'),
    'tjek-hastighed-uden-lighthouse': ('YDELSE', 'Tjek hastigheden — uden Lighthouse',
        'Letvægts alternativ til fuld browser-render: hurtig ydelsestjek i CI.'),
}

BADGE_RULES = [
    ('tilgaengelighed|eaa|wcag|bitv|en-301', 'TILGÆNGELIGHED · EAA'),
    ('gdpr|nis2|dbbaftale|cookie|databehandler', 'COMPLIANCE · GDPR/NIS2'),
    ('overvaag|oppetid|ned|uptime|ssl-certifikat', 'OPPETID'),
    ('tabel|konverter|csv|markdown|kopier|indsaet|indsæt|ren-tekst|rentekst', 'VÆRKTØJER'),
    ('seo|hreflang|canonical|canonisk|metadata|redirect', 'SEO'),
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
    p = f'{SITE}/da/blog/{slug}.html'
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
    url = f'/da/blog/{slug}'
    if f'href="{url}"' in c:
        print(f'skip {slug} (allerede i hub)')
        return False
    title, desc = page_meta(slug)
    card = (
        f'\n      <div class="product-card">\n'
        f'        <div class="product-badge product-badge-secondary">{badge_for(slug)}</div>\n'
        f'        <div class="product-body">\n'
        f'          <h3><a href="{url}" style="color:inherit;text-decoration:none;">{htmllib.escape(title)}</a></h3>\n'
        f'          <p class="product-desc">{htmllib.escape(desc)}</p>\n'
        f'          <div class="product-details"><span class="product-meta">📖 Guide</span>'
        f'<span class="product-meta">🇩🇰 Dansk</span></div>\n'
        f'          <a href="{url}" class="btn-secondary" style="margin-top:12px;">L&aelig;s guide &rarr;</a>\n'
        f'        </div>\n      </div>\n'
    )
    pos = c.rfind('<a href="/da/blog/')
    end = c.find('\n      </div>\n', pos)
    assert pos != -1 and end != -1, 'kunne ikke finde indsættelsespunkt'
    ins = end + len('\n      </div>\n')
    c = c[:ins] + card + c[ins:]
    open(HUB, 'w').write(c)
    print(f'tilføjet kort: {slug}')
    return True


def main():
    files = {os.path.basename(f)[:-5] for f in __import__('glob').glob(f'{SITE}/da/blog/*.html')}
    added = [s for s in sorted(files) if add_card(s)]
    # Verificér: hub <-> disk 1:1
    c = open(HUB).read()
    hub = set(re.findall(r'href="/da/blog/([^"]+)"', c))
    dead = hub - files
    missing = files - hub
    assert not dead, f'hubbet linker til ikke-eksisterende sider: {dead}'
    assert not missing, f'mangler stadig i hub: {missing}'
    print(f'verify OK: disk={len(files)} hub={len(hub)} tilføjet={len(added)}')
    # Intern link-tjek for hubben
    broken = []
    for m in sorted(set(re.findall(r'href="(/[^"#?]*?)(?:\?.*)?"', c))):
        t = ('site' + m).rstrip('/')
        if not (os.path.exists(t) or os.path.exists(t + '.html') or m == '/'
                or os.path.exists(t + '/index.html') or m.startswith('/#')):
            broken.append(m)
    assert not broken, f'brudte links i da.html: {broken}'
    print('Intern link-tjek da.html: OK')


if __name__ == '__main__':
    main()
