#!/usr/bin/env python3
"""Iteration 451: Add complete hreflang sets to the eaa-deadline-passed /
eaa-frist-hvad-nu mirror pair. Both pages have incomplete sets:
- EN page (eaa-deadline-passed): 0 hreflang links
- DA page (eaa-frist-hvad-nu): only x-default

Adds: x-default, da, en on both sides. Idempotent.
"""
import glob, os, re

BASE = 'https://hermes-passiv.pages.dev'
SITE = '/Users/madsholstjensen/hermes-passiv/site'

PAIRS = [
    # (en_slug, da_slug)
    ('eaa-deadline-passed', 'eaa-frist-hvad-nu'),
]

EN_URLS = {s: f'{BASE}/blog/{s}' for s in [p[0] for p in PAIRS]}
DA_URLS = {s: f'{BASE}/da/blog/{s}' for s in [p[1] for p in PAIRS]}

HREFLANG_TEMPLATES = {
    'en': '<link rel="alternate" hreflang="en" href="{}">',
    'da': '<link rel="alternate" hreflang="da" href="{}">',
    'x-default': '<link rel="alternate" hreflang="x-default" href="{}">',
}

fixed_en = 0
fixed_da = 0

for en_slug, da_slug in PAIRS:
    en_url = EN_URLS[en_slug]
    da_url = DA_URLS[da_slug]

    # --- EN page: add complete hreflang set ---
    en_path = os.path.join(SITE, 'blog', en_slug + '.html')
    c = open(en_path).read()
    existing = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', c)
    existing_langs = {lang for lang, _ in existing}

    want_en = {
        'x-default': en_url,
        'da': da_url,
        'en': en_url,
    }

    # Remove incomplete/bad alternates
    for lang, href in existing:
        if want_en.get(lang) != href or (lang not in want_en):
            c = c.replace(f'<link rel="alternate" hreflang="{lang}" href="{href}">', '')
            existing_langs.discard(lang)

    # Add missing links
    for lang in ('x-default', 'da', 'en'):
        if lang not in existing_langs:
            href = want_en[lang]
            tag = HREFLANG_TEMPLATES[lang].format(href)
            # Insert after canonical
            can = re.search(r'<link rel="canonical"[^>]*>', c)
            if can:
                c = c[:can.end()] + '\n' + tag + c[can.end():]
            fixed_en += 1
            # re-check existing after insertion
            existing_langs.add(lang)

    open(en_path, 'w').write(c)

    # --- DA page: add/complete hreflang set ---
    da_path = os.path.join(SITE, 'da', 'blog', da_slug + '.html')
    c = open(da_path).read()
    existing = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', c)
    existing_langs = {lang for lang, _ in existing}

    want_da = {
        'x-default': en_url,
        'da': da_url,
        'en': en_url,
    }

    for lang, href in existing:
        if want_da.get(lang) != href or (lang not in want_da):
            c = c.replace(f'<link rel="alternate" hreflang="{lang}" href="{href}">', '')
            existing_langs.discard(lang)

    for lang in ('x-default', 'da', 'en'):
        if lang not in existing_langs:
            href = want_da[lang]
            tag = HREFLANG_TEMPLATES[lang].format(href)
            can = re.search(r'<link rel="canonical"[^>]*>', c)
            if can:
                c = c[:can.end()] + '\n' + tag + c[can.end():]
            fixed_da += 1
            existing_langs.add(lang)

    open(da_path, 'w').write(c)

print(f'fixed EN links: {fixed_en} | fixed DA links: {fixed_da}')

# Verify: all alternates present
for en_slug, da_slug in PAIRS:
    en_url = EN_URLS[en_slug]
    da_url = DA_URLS[da_slug]

    en_path = os.path.join(SITE, 'blog', en_slug + '.html')
    c = open(en_path).read()
    alts = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', c))
    assert alts['x-default'] == en_url, f'{en_slug}: x-default wrong: {alts.get("x-default")} != {en_url}'
    assert alts['da'] == da_url, f'{en_slug}: da wrong: {alts.get("da")} != {da_url}'
    assert alts['en'] == en_url, f'{en_slug}: en wrong: {alts.get("en")} != {en_url}'
    print(f'  {en_slug}/blog: x-default, da, en OK')

    da_path = os.path.join(SITE, 'da', 'blog', da_slug + '.html')
    c = open(da_path).read()
    alts = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', c))
    assert alts['x-default'] == en_url, f'{da_slug}: x-default wrong: {alts.get("x-default")} != {en_url}'
    assert alts['da'] == da_url, f'{da_slug}: da wrong: {alts.get("da")} != {da_url}'
    assert alts['en'] == en_url, f'{da_slug}: en wrong: {alts.get("en")} != {en_url}'
    print(f'  {da_slug}/da/blog: x-default, da, en OK')

print('All verified.')