#!/usr/bin/env python3
"""Iteration 240: krydslink DA↔EN mellem eksisterende spejl-posts.

Fire EN/DA-par der allerede findes, men ikke linker til hinanden:
- copy-table-from-pdf-to-excel        <-> /da/blog/kopier-tabel-fra-pdf
- copy-table-website-to-notion        <-> /da/blog/kopier-tabel-hjemmeside-til-notion
- accessibility-audit-cost (lang=da)  <-> pris-tilgaengelighedsgennemgang (lang=da)
Idempotent: tilføjer kun linjen hvis den mangler.
"""
import os

ROOT = '/Users/madsholstjensen/hermes-passiv'
SITE = os.path.join(ROOT, 'site')

# (en_path, da_path_without_lang_prefix, en_label, da_label)
PAIRS = [
    ('blog/copy-table-from-pdf-to-excel.html', 'da/blog/kopier-tabel-fra-pdf',
     'Dansk version af denne guide', 'English version of this guide'),
    ('blog/copy-table-website-to-notion.html', 'da/blog/kopier-tabel-hjemmeside-til-notion',
     'Dansk version af denne guide', 'English version of this guide'),
    ('blog/accessibility-audit-cost.html', 'blog/pris-tilgaengelighedsgennemgang',
     'Se også: Pris på tilgængelighedsgennemgang', 'Se også: How much does an accessibility audit cost'),
]

for en_rel, da_slug, en_label, _ in PAIRS:
    en_path = os.path.join(SITE, en_rel)
    da_url = '/' + da_slug
    c = open(en_path).read()
    if da_url in c:
        print('OK already linked:', en_rel)
        continue
    anchor = '<footer style="padding:32px 24px;">'
    assert anchor in c, 'no footer anchor in ' + en_rel
    line = ('<p style="text-align:center;"><a href="%s">%s</a></p>\n' % (da_url, en_label))
    c = c.replace(anchor, line + anchor, 1)
    open(en_path, 'w').write(c)
    print('linked:', en_rel, '->', da_url)

print('\nDone')
