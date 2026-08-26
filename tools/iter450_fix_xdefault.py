#!/usr/bin/env python3
"""Iteration 450 fixup v2: correct x-default on DA blog pages using BOTH
directions of hreflang pairs as ground truth (EN->da and DA->en), plus
manual mapping for the 4 stragglers. Verifies every x-default target
exists on disk afterwards."""
import glob, os, re

BASE = 'https://hermes-passiv.pages.dev'
SITE = '/Users/madsholstjensen/hermes-passiv/site'

da2en = {}
# from EN pages' da links
for p in glob.glob(os.path.join(SITE, 'blog', '*.html')):
    c = open(p).read()
    m = re.search(r'<link rel="alternate" hreflang="da" href="([^"]+)"', c)
    if not m:
        continue
    en = re.search(r'<link rel="canonical" href="([^"]+)"', c).group(1)
    da2en[m.group(1)] = en
# from DA pages' en links (overrides/extends)
for p in glob.glob(os.path.join(SITE, 'da', 'blog', '*.html')):
    c = open(p).read()
    m = re.search(r'<link rel="alternate" hreflang="en" href="([^"]+)"', c)
    if not m:
        continue
    own = re.search(r'<link rel="canonical" href="([^"]+)"', c).group(1)
    da2en[own] = m.group(1)
print(len(da2en), 'DA->EN pairs')

MANUAL = {
    'wcag-22-krav-liste': 'wcag-22-what-changes',
    'eaa-frist-hvad-nu': 'eaa-deadline-passed',
}
for da_slug, en_slug in MANUAL.items():
    da2en[f'{BASE}/da/blog/{da_slug}'] = f'{BASE}/blog/{en_slug}'

fixed = 0
for p in sorted(glob.glob(os.path.join(SITE, 'da', 'blog', '*.html'))):
    c = open(p).read()
    own = re.search(r'<link rel="canonical" href="([^"]+)"', c).group(1)
    want = da2en.get(own)
    m = re.search(r'<link rel="alternate" hreflang="x-default" href="([^"]+)"', c)
    if want is None:
        # no EN mirror exists: x-default should be self (single-language page)
        want = own
        print('no EN mirror -> self:', os.path.basename(p))
    cur = m.group(1) if m else None
    if cur != want:
        xd_tag = f'<link rel="alternate" hreflang="x-default" href="{want}">\n'
        if m:
            c = c.replace(m.group(0), f'<link rel="alternate" hreflang="x-default" href="{want}">', 1)
        else:
            first = re.search(r'<link rel="alternate" hreflang="[^"]+"[^>]*>', c)
            if first:
                c = c.replace(first.group(0), xd_tag + first.group(0), 1)
            else:
                # no alternates at all: insert before canonical
                can = re.search(r'<link rel="canonical"[^>]*>', c).group(0)
                c = c.replace(can, xd_tag + can, 1)
        open(p, 'w').write(c)
        fixed += 1
        print('fixed', os.path.basename(p), '->', want.split('/blog/')[-1])
print('fixed:', fixed)

# verify: every DA page has x-default; every x-default/en/da hreflang target file exists
bad = []
for p in sorted(glob.glob(os.path.join(SITE, '**', '*.html'), recursive=True)):
    c = open(p).read()
    alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', c)
    if len(alts) >= 2 and 'x-default' not in [a[0] for a in alts]:
        bad.append((p, 'missing x-default'))
    for lang, href in alts:
        path = href.replace(BASE + '/', SITE + '/') + '.html'
        if not os.path.exists(path) and not os.path.exists(href.replace(BASE + '/', SITE + '/')):
            bad.append((p, f'dangling {lang} target: {href}'))
assert not bad, bad
print('verified: all pages have x-default and no dangling hreflang targets')
