#!/usr/bin/env python3
"""Ret sitemap-URL'er der 301-redirecter (gammelt slug, canonical peger på det nye).
Fjerner dublet-posten for den gamle slug og opdaterer hreflang-alternates der
peger på den. Kør: python3 tools/fix_sitemap_redirects.py"""
import re, subprocess
import concurrent.futures as cf

SM = 'site/sitemap.xml'
BASE = 'https://hermes-passiv.pages.dev/'

def status(u):
    p = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', u],
                       capture_output=True)
    return p.stdout.decode()

html = open(SM).read()
urls = re.findall(r'<loc>(.*?)</loc>', html)
print(len(urls), 'urls i sitemap')

redirects = []
with cf.ThreadPoolExecutor(12) as ex:
    for u, code in zip(urls, ex.map(status, urls)):
        if code in ('301', '302'):
            # find redirect-målet
            p = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w',
                                '%{http_code} %{redirect_url}', '-I' if False else '-s',
                                '-o', '/dev/null', '-w', '%{http_code} %{redirect_url}', u],
                               capture_output=True)
            redirects.append((u, p.stdout.decode().split(' ', 1)[1]))
            print('REDIRECT:', u)

if not redirects:
    print('Ingen redirects — intet at rette.')
    raise SystemExit(0)

# Fjern hele <url>-blokke hvis loc er en redirectende URL (canonical findes allerede)
for old, new in redirects:
    # match blokken: <url> ... <loc>old</loc> ... </url>
    pat = re.compile(r'<url>(?:(?!</url>).)*?<loc>' + re.escape(old) +
                     r'</loc>(?:(?!</url>).)*?</url>\s*', re.S)
    html2, n = pat.subn('', html)
    if n == 0:
        print('KUNNE IKKE fjerne blok for', old)
    html = html2
    # opdatér hreflang-referencer til den gamle URL andre steder
    html = html.replace(f'href="{old}"', f'href="{new}"')

open(SM, 'w').write(html)
import re as _re
print('Nu', len(_re.findall(r'<loc>', html)), 'urls')
