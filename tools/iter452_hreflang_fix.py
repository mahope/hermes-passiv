#!/usr/bin/env python3
"""Iteration 452: fix remaining hreflang problems found by hreflang_audit.py.

1. canonical-url-guide pair: missing self-language link on both sides.
2. copy-table-website-iphone-ipad pair: EN had 0 links; add full set.
3. EN-only pages with partial/pointless sets (lone x-default or
   x-default+en, no DA mirror): drop the set entirely.
4. da/blog/kopier-tabel-hjemmeside-til-excel: DA-only page whose x-default
   pointed at itself; drop it.
5. da/blog/nis2-beredskabstjek-2026: DA translation OF nis2-readiness-guide
   (same article), while nis2-guide-da is a SEPARATE Danish article that
   wrongly claimed nis2-readiness-guide as its mirror. Fix:
   - beredskabstjek-2026: full set -> mirror of readiness-guide (also fixes
     a stray '>' typo after the x-default tag).
   - nis2-guide-da: drop hreflang (standalone DA article).
   - readiness-guide EN: point at beredskabstjek-2026; fix in-body link.
Idempotent. Verify afterwards with tools/hreflang_audit.py.
"""
import glob, os, re

BASE='https://hermes-passiv.pages.dev'
SITE='/Users/madsholstjensen/hermes-passiv/site'

def read(p): return open(p).read()
def write(p,c): open(p,'w').write(c)

def remove_links(c, langs=None):
    def repl(m):
        if langs is None or m.group(1) in langs:
            return ''
        return m.group(0)
    c=re.sub(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">>?\n?',repl,c)
    return c.replace('\n\n\n','\n\n')

def insert_after_canonical(c, tags):
    m=re.search(r'<link rel="canonical"[^>]*>',c)
    assert m, 'no canonical found in page'
    return c[:m.end()]+'\n'+'\n'.join(tags)+c[m.end():]

changed=[]

# --- 1+2: simple mirror-pair repairs ---
PAIRS=[
    ('canonical-url-guide','canonisk-url-guide'),
    ('copy-table-website-iphone-ipad','kopier-tabel-iphone-ipad'),
]
for en_slug, da_slug in PAIRS:
    en_url=BASE+'/blog/'+en_slug; da_url=BASE+'/da/blog/'+da_slug
    want={'x-default':en_url,'da':da_url,'en':en_url}
    for path in (SITE+'/blog/'+en_slug+'.html', SITE+'/da/blog/'+da_slug+'.html'):
        c=read(path); orig=c
        existing=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',c))
        for lang,href in list(existing.items()):
            if lang not in want or want[lang]!=href:
                c=remove_links(c,{lang}); del existing[lang]
        missing=[l for l in ('da','en','x-default') if l not in existing]
        if missing:
            tags=['<link rel="alternate" hreflang="%s" href="%s">' % (l, want[l]) for l in missing]
            c=insert_after_canonical(c,tags)
        if c!=orig:
            write(path,c); changed.append(path)

# --- 3: EN-only pages with partial/pointless sets ---
paired_en={p[0] for p in PAIRS} | {'nis2-readiness-guide'}
for f in sorted(glob.glob(SITE+'/blog/*.html')):
    slug=os.path.basename(f)[:-5]
    if slug in paired_en: continue
    existing=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',read(f)))
    if not existing or 'da' in existing: continue
    c=read(f); orig=c
    c=remove_links(c)
    if c!=orig:
        write(f,c); changed.append(f+' (dropped %s)'%sorted(existing))

# --- 4: DA-only page with self-pointing x-default ---
f=SITE+'/da/blog/kopier-tabel-hjemmeside-til-excel.html'
existing=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',read(f)))
if set(existing)=={'x-default'} and existing['x-default'].endswith('kopier-tabel-hjemmeside-til-excel'):
    c=read(f); orig=c
    c=remove_links(c)
    if c!=orig:
        write(f,c); changed.append(f+' (dropped self-x-default)')

# --- 5: NIS2 trio ---
en_url=BASE+'/blog/nis2-readiness-guide'
ber_url=BASE+'/da/blog/nis2-beredskabstjek-2026'

f=SITE+'/da/blog/nis2-beredskabstjek-2026.html'   # true DA translation
c=read(f); orig=c
existing=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">?',c))
want={'x-default':en_url,'da':ber_url,'en':en_url}
if existing!=want:
    c=remove_links(c)
    c=insert_after_canonical(c,['<link rel="alternate" hreflang="%s" href="%s">'%(l,want[l]) for l in ('x-default','en','da')])
if c!=orig:
    write(f,c); changed.append(f+' (full set -> readiness-guide mirror)')

f=SITE+'/da/blog/nis2-guide-da.html'              # standalone DA article
c=read(f); orig=c
c=remove_links(c)
if c!=orig:
    write(f,c); changed.append(f+' (dropped wrong mirror set)')

f=SITE+'/blog/nis2-readiness-guide.html'          # EN original
c=read(f); orig=c
existing=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',c))
want={'x-default':en_url,'da':ber_url,'en':en_url}
if existing!=want:
    c=remove_links(c)
    c=insert_after_canonical(c,['<link rel="alternate" hreflang="%s" href="%s">'%(l,want[l]) for l in ('x-default','da','en')])
c=c.replace('<a href="/da/blog/nis2-guide-da" lang="da">Dansk version af denne guide</a>',
            '<a href="/da/blog/nis2-beredskabstjek-2026" lang="da">Dansk version af denne guide</a>')
if c!=orig:
    write(f,c); changed.append(f+' (mirror -> beredskabstjek-2026)')

print('changed files:')
for ch in changed: print(' ',ch)

# --- 6: wcag-22-krav-liste (standalone DA article): drop lone x-default ---
f=SITE+'/da/blog/wcag-22-krav-liste.html'
existing=dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">?',read(f)))
if set(existing)=={'x-default'}:
    c=read(f); orig=c
    c=remove_links(c)
    if c!=orig:
        write(f,c); changed.append(f+' (dropped lone x-default)')
        print('changed files (phase 6):')
        for ch in changed[-1:]: print(' ',ch)
