#!/usr/bin/env python3
"""iter498: insert a bundle/e-book CTA before </footer> on all blog posts (EN+DA)
that don't already link to /books. Idempotent, tracks via existing page tracking.
"""
import os, re, json

ROOT = '/Users/madsholstjensen/hermes-passiv/site'

# Map post keywords -> most relevant book slug; default = compliance bundle mention only
BOOK_HINTS = [
    ('eaa', 'eaa-checklist', 'EAA Compliance Checklist for WordPress Sites',
     'Free e-book: EAA Compliance Checklist', 'The complete accessibility checklist is available as a free EPUB — no signup required.'),
    ('accessibility', 'eaa-checklist', None, None, None),
    ('gdpr', 'gdpr-for-agencies', 'GDPR Compliance for Small Web Agencies',
     'Free e-book: GDPR Compliance for Small Web Agencies',
     'The complete guide is available as a free EPUB — no signup required.'),
    ('cookie', 'cookie-consent-guide', 'Cookie Consent & GDPR Compliance for Web Agencies',
     "Free e-book: Cookie Consent & GDPR", 'The complete guide is available as a free EPUB — no signup required.'),
    ('nis2', 'nis2-for-agencies', 'NIS2 Compliance for Small Web Agencies',
     'Free e-book: NIS2 Compliance for Small Web Agencies',
     'The complete guide is available as a free EPUB — no signup required.'),
]

DA_BOOK_HINTS = [
    ('tilgaengelighed', 'eaa-checklist'),
    ('eaa', 'eaa-checklist'),
    ('bitv', 'eaa-checklist'),
    ('gdpr', 'gdpr-for-agencies'),
    ('cookie', 'cookie-consent-guide'),
    ('nis2', 'nis2-for-agencies'),
]

EN_BUNDLE_LINE = ('  <p style="margin:12px 0 0;font-size:13px;color:#555;">Want all six guides? '
                  '<a href="/books/compliance-bundle"><strong>Complete EU Compliance Bundle</strong></a>'
                  ' — combined PDF + all EPUBs, $29.</p>\n')
DA_BUNDLE_LINE = ('  <p style="margin:12px 0 0;font-size:13px;color:#555;">Alle seks guides i én pakke: '
                  '<a href="/books/compliance-bundle"><strong>Complete EU Compliance Bundle</strong></a>'
                  ' — samlet PDF + alle EPUB&#39;er, $29. De enkelte bøger er gratis som EPUB.</p>\n')

def book_cta_en(slug, title, heading, blurb):
    return (f'<div class="book-cta" style="border:1px solid #ddd;border-radius:8px;padding:16px 20px;margin:32px 0;">\n'
            f'  <h3>{heading}</h3>\n  <p>{blurb}</p>\n'
            f'  <a href="/books/{slug}" class="btn-primary">Get the free e-book →</a>\n'
            f'{EN_BUNDLE_LINE}</div>\n')

def da_block(slug):
    return ('<div style="border:1px solid #ddd;border-radius:8px;padding:16px 20px;margin:32px 0;">\n'
            f'  <h3>Gratis e-bog</h3>\n'
            f'  <p><a href="/books/{slug}"><strong>Hent den komplette guide som gratis EPUB</strong></a> — ingen tilmelding.</p>\n'
            f'{DA_BUNDLE_LINE}</div>\n')

def pick_book(name, hints, da=False):
    low = name.lower()
    for entry in hints:
        kw = entry[0]
        if kw in low:
            return entry[1]
    return None

def process(dirpath, da=False):
    changed = []
    for fn in sorted(os.listdir(dirpath)):
        if not fn.endswith('.html'):
            continue
        path = os.path.join(dirpath, fn)
        t = open(path, encoding='utf-8').read()
        if '/books' in t or '</footer>' not in t:
            continue
        if da:
            slug = pick_book(fn, DA_BOOK_HINTS, da=True) or 'nis2-for-agencies'
            block = da_block(slug)
        else:
            hit = None
            for kw, slug, title, heading, blurb in BOOK_HINTS:
                if kw in fn.lower():
                    hit = (slug, title, heading, blurb); break
            if hit:
                block = book_cta_en(*hit)
            else:
                # generic: bundle-only card
                block = ('<div class="book-cta" style="border:1px solid #ddd;border-radius:8px;'
                         'padding:16px 20px;margin:32px 0;">\n'
                         '  <h3>Free e-books: EU compliance guides</h3>\n'
                         '  <p>Six practical guides (NIS2, GDPR, EAA, cookies) — every complete book is a free EPUB download.</p>\n'
                         '  <a href="/books" class="btn-primary">Browse the free e-books →</a>\n'
                         + EN_BUNDLE_LINE + '</div>\n')
        newt = t.replace('</footer>', block + '</footer>', 1)
        open(path, 'w', encoding='utf-8').write(newt)
        changed.append(fn)
    return changed

en_changed = process(os.path.join(ROOT, 'blog'))
da_changed = process(os.path.join(ROOT, 'da', 'blog'), da=True)
print(json.dumps({'en': len(en_changed), 'da': len(da_changed)}))
print('EN:', en_changed)
print('DA:', da_changed)
