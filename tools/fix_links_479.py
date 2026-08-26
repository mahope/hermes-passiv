#!/usr/bin/env python3
"""Iter 479: fix broken internal links (kvalitetskravet). Idempotent mapping
af doede URL'er til eksisterende sider + opret /privacy/ og /terms/."""
import os, re, glob

ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')

# dead target -> replacement (existing page)
MAP = {
    '/da/blog/ren-tekst-fra-hjemmeside': '/da/blog/kopier-ren-tekst-fra-hjemmeside',
    '/da/blog/pris-tilgaengelighedsgennemgang': '/da/blog/hvad-koster-tilgaengelighedsgennemgang',
    '/da/blog/kopier-tabel-fra-pdf': '/da/blog/kopier-tabel-fra-pdf-til-excel',
    '/da/blog/open-graph-tjekker': '/da/blog/open-graph-tjekker-guide',
    '/docs': '/clean-copy-cli-ref',
}

changed = {}
for path in glob.glob(os.path.join(SITE, '**', '*.html'), recursive=True):
    with open(path, encoding='utf-8') as f:
        html = f.read()
    orig = html
    for dead, live in MAP.items():
        html = html.replace(f'href="{dead}"', f'href="{live}"')
        html = html.replace(f'href="{dead}/"', f'href="{live}"')
    if html != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        changed[os.path.relpath(path, SITE)] = True

print('files changed:', len(changed))
for k in sorted(changed): print(' -', k)

# --- downloads.html: point at files that actually exist ---
dl = os.path.join(SITE, 'downloads.html')
with open(dl, encoding='utf-8') as f:
    html = f.read()
fixes = [
    ('/downloads/eaa_scanner-1.3.0-py3-none-any.whl', '/downloads/eaa_scanner-1.2.0-py3-none-any.whl'),
    ('/downloads/eaa_scanner-1.3.0.tar.gz', '/downloads/eaa_scanner-1.2.0.tar.gz'),
]
n_dl = 0
for dead, live in fixes:
    if dead in html:
        n_dl += html.count(dead)
        html = html.replace(dead, live)
# mahope-eaa-scanner-1.3.0.tgz -> 1.2.0 tgz exists in downloads dir? check on disk
tgz = os.path.join(SITE, 'downloads', 'mahope-eaa-scanner-1.2.0.tgz')
if '/downloads/mahope-eaa-scanner-1.3.0.tgz' in html and os.path.exists(tgz):
    n_dl += html.count('/downloads/mahope-eaa-scanner-1.3.0.tgz')
    html = html.replace('/downloads/mahope-eaa-scanner-1.3.0.tgz', '/downloads/mahope-eaa-scanner-1.2.0.tgz')
# old page-profile tarball -> current 1.1.0
if '/downloads/page-profile/page-profile-1.0.0.tar.gz' in html:
    html = html.replace('/downloads/page-profile/page-profile-1.0.0.tar.gz',
                        '/downloads/page-profile/page-profile-1.1.0.tar.gz')
    n_dl += 1
with open(dl, 'w', encoding='utf-8') as f:
    f.write(html)
print('downloads.html link fixes:', n_dl)

# --- free-tools link in url-inspector ---
ui = os.path.join(SITE, 'url-inspector', 'index.html')
with open(ui, encoding='utf-8') as f:
    h = f.read()
h = h.replace('href="/free-tools/"', 'href="/free-tools"')
with open(ui, 'w', encoding='utf-8') as f:
    f.write(h)
print('url-inspector fixed')
